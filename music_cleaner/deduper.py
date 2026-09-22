"""
Deduplication Engine & Audio Quality Evaluator.
Performs exact MD5 checksum matching and Chromaprint acoustic waveform analysis.
Selects highest-quality tracks (Lossless > Lossy, bitrate, sample rate, tag completeness)
and routes duplicates to trash.
"""
from typing import List, Dict, Any, Tuple, Optional
import acoustid


def calculate_quality_score(file_rec: Dict[str, Any]) -> float:
    """
    Calculate quality score:
    Score = (is_lossless * 10000) + bitrate_kbps + (sample_rate / 1000) + metadata completeness
    """
    is_lossless = 1 if file_rec.get("is_lossless") else 0
    bitrate = float(file_rec.get("bitrate") or 0.0)
    sample_rate = float(file_rec.get("sample_rate") or 44100.0)

    score = (is_lossless * 10000.0) + bitrate + (sample_rate / 1000.0)

    # Metadata bonus (0 - 10 points) as deterministic tie-breaker
    meta_bonus = 0.0
    if file_rec.get("raw_title"):
        meta_bonus += 2.0
    if file_rec.get("raw_artist"):
        meta_bonus += 2.0
    if file_rec.get("raw_album"):
        meta_bonus += 2.0
    if file_rec.get("raw_year"):
        meta_bonus += 2.0
    if file_rec.get("raw_track"):
        meta_bonus += 2.0

    return score + meta_bonus


def compare_two_fingerprints(dur_a: float, fp_a: Optional[str],
                             dur_b: float, fp_b: Optional[str]) -> float:
    """
    Compare two acoustic fingerprints. Returns similarity float in [0.0, 1.0].
    """
    if not fp_a or not fp_b:
        return 0.0

    # Quick exact string match
    if fp_a.strip() == fp_b.strip():
        return 1.0

    try:
        # acoustid.compare_fingerprints expects bytes or string depending on pyacoustid version
        pair_a = (dur_a, fp_a.encode("utf-8") if isinstance(fp_a, str) else fp_a)
        pair_b = (dur_b, fp_b.encode("utf-8") if isinstance(fp_b, str) else fp_b)
        sim = acoustid.compare_fingerprints(pair_a, pair_b)
        return float(sim)
    except Exception:
        return 0.0


def deduplicate_library(files: List[Dict[str, Any]],
                         acoustic_threshold: float = 0.85,
                         duration_tolerance_sec: float = 4.0
                         ) -> Dict[str, Any]:
    """
    Analyze scanned files for exact and acoustic duplicates.

    Returns:
        {
            "groups": [
                {
                    "type": "EXACT_MD5" | "ACOUSTIC_SIMILARITY",
                    "keeper": file_rec,
                    "duplicates": [
                        {"file": file_rec, "reason": str}
                    ]
                }
            ],
            "keepers": [file_rec, ...],
            "duplicates": [{"file": file_rec, "reason": str, "keeper": file_rec}, ...],
            "singletons": [file_rec, ...]
        }
    """
    if not files:
        return {"groups": [], "keepers": [], "duplicates": [], "singletons": []}

    # Step 1: Group by Exact MD5 hash
    md5_buckets: Dict[str, List[Dict[str, Any]]] = {}
    for f in files:
        h = f.get("md5_hash", "")
        if h:
            md5_buckets.setdefault(h, []).append(f)
        else:
            md5_buckets.setdefault(f["file_path"], []).append(f)

    exact_keepers: List[Dict[str, Any]] = []
    flagged_duplicates: List[Dict[str, Any]] = []
    groups: List[Dict[str, Any]] = []

    for h, group_files in md5_buckets.items():
        if len(group_files) > 1:
            # Sort by quality score (highest first)
            sorted_group = sorted(group_files, key=calculate_quality_score, reverse=True)
            keeper = sorted_group[0]
            exact_keepers.append(keeper)
            dupe_items = []
            for dupe in sorted_group[1:]:
                fmt_keeper = keeper.get("format", "AUDIO")
                br_keeper = keeper.get("bitrate", 0)
                reason = f"Exact MD5 match with keeper ({fmt_keeper} {br_keeper}kbps)"
                dupe_items.append({"file": dupe, "reason": reason})
                flagged_duplicates.append({"file": dupe, "reason": reason, "keeper": keeper})
            groups.append({
                "type": "EXACT_MD5",
                "keeper": keeper,
                "duplicates": dupe_items,
            })
        else:
            exact_keepers.append(group_files[0])

    # Step 2: Acoustic duplicate detection among the remaining keepers
    acoustic_visited = set()
    final_keepers: List[Dict[str, Any]] = []
    singletons: List[Dict[str, Any]] = []

    for i, file_a in enumerate(exact_keepers):
        path_a = file_a["file_path"]
        if path_a in acoustic_visited:
            continue

        cluster = [file_a]
        fp_a = file_a.get("fingerprint")
        dur_a = float(file_a.get("duration") or 0.0)

        if fp_a and dur_a > 1.0:
            for j in range(i + 1, len(exact_keepers)):
                file_b = exact_keepers[j]
                path_b = file_b["file_path"]
                if path_b in acoustic_visited:
                    continue

                fp_b = file_b.get("fingerprint")
                dur_b = float(file_b.get("duration") or 0.0)

                # Duration check within tolerance
                if abs(dur_a - dur_b) <= duration_tolerance_sec:
                    sim = compare_two_fingerprints(dur_a, fp_a, dur_b, fp_b)
                    if sim >= acoustic_threshold:
                        cluster.append((file_b, sim))
                        acoustic_visited.add(path_b)

        if len(cluster) > 1:
            # First item is file_a, subsequent items are (file_b, sim)
            candidates = [cluster[0]] + [item[0] for item in cluster[1:]]
            sim_lookup = {item[0]["file_path"]: item[1] for item in cluster[1:]}

            # Rank by quality score
            ranked = sorted(candidates, key=calculate_quality_score, reverse=True)
            keeper = ranked[0]
            final_keepers.append(keeper)
            acoustic_visited.add(keeper["file_path"])

            dupe_items = []
            for dupe in ranked[1:]:
                dupe_path = dupe["file_path"]
                acoustic_visited.add(dupe_path)
                sim_val = sim_lookup.get(dupe_path, 1.0)
                fmt_k = keeper.get("format", "AUDIO")
                br_k = keeper.get("bitrate", 0)
                fmt_d = dupe.get("format", "AUDIO")
                br_d = dupe.get("bitrate", 0)
                reason = (
                    f"Acoustic duplicate (similarity {sim_val:.1%}, "
                    f"kept higher quality {fmt_k} {br_k}kbps "
                    f"over {fmt_d} {br_d}kbps)"
                )
                dupe_items.append({"file": dupe, "reason": reason})
                flagged_duplicates.append({"file": dupe, "reason": reason, "keeper": keeper})

            groups.append({
                "type": "ACOUSTIC_SIMILARITY",
                "keeper": keeper,
                "duplicates": dupe_items,
            })
        else:
            acoustic_visited.add(path_a)
            final_keepers.append(file_a)
            singletons.append(file_a)

    return {
        "groups": groups,
        "keepers": final_keepers,
        "duplicates": flagged_duplicates,
        "singletons": singletons,
    }
