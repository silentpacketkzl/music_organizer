"""
Audio File Scanner and Metadata Ingestion Module.
Extracts MD5 hash, acoustic fingerprints (via fpcalc/pyacoustid), audio quality specs, and tags.
"""
import os
import hashlib
import json
import subprocess
from typing import Dict, Any, List, Optional
import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
import acoustid

from .db import Database

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".wav", ".aiff", ".wma"}
LOSSLESS_EXTENSIONS = {".flac", ".wav", ".aiff", ".alac"}


def compute_md5(file_path: str, block_size: int = 65536) -> str:
    """Compute MD5 hash of file content."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_acoustic_fingerprint(file_path: str) -> Optional[str]:
    """
    Generate acoustic waveform fingerprint using pyacoustid / fpcalc.
    Falls back to running fpcalc directly if pyacoustid fails.
    """
    try:
        duration, fingerprint = acoustid.fingerprint_file(file_path)
        if fingerprint:
            return fingerprint.decode("utf-8") if isinstance(fingerprint, bytes) else str(fingerprint)
    except Exception:
        pass

    # Direct fpcalc fallback
    try:
        cmd = ["fpcalc", "-json", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        return data.get("fingerprint")
    except Exception:
        return None


def extract_tag_value(audio: Any, tag_names: List[str]) -> str:
    """Extract string value from audio tags across mutagen formats."""
    if not audio or not hasattr(audio, "tags") or audio.tags is None:
        return ""
    tags = audio.tags
    for tag in tag_names:
        if tag in tags:
            val = tags[tag]
            if isinstance(val, (list, tuple)):
                return str(val[0]).strip() if val else ""
            if hasattr(val, "text") and val.text:
                return str(val.text[0]).strip()
            return str(val).strip()
    return ""


def scan_file(file_path: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
    """Scan a single audio file and return metadata and quality info."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return None

    try:
        stat = os.stat(file_path)
    except OSError:
        return None

    mtime = stat.st_mtime
    file_size = stat.st_size

    # Check database cache first
    if db:
        cached = db.get_cached_file(file_path, mtime)
        if cached:
            return cached

    # Compute fast MD5 hash
    try:
        md5_hash = compute_md5(file_path)
    except Exception:
        return None

    # Inspect with mutagen
    try:
        audio = mutagen.File(file_path)
    except Exception:
        audio = None

    duration = 0.0
    bitrate = 0
    sample_rate = 44100
    channels = 2

    if audio and hasattr(audio, "info") and audio.info is not None:
        duration = float(getattr(audio.info, "length", 0.0) or 0.0)
        bitrate = int(getattr(audio.info, "bitrate", 0) or 0)
        sample_rate = int(getattr(audio.info, "sample_rate", 44100) or 44100)
        channels = int(getattr(audio.info, "channels", 2) or 2)

    # Estimate bitrate if zero and duration is positive
    if bitrate <= 0 and duration > 0:
        bitrate = int((file_size * 8) / duration)

    # Convert bps to kbps if excessively large
    if bitrate > 10000:
        bitrate = bitrate // 1000

    is_lossless = 1 if ext in LOSSLESS_EXTENSIONS or isinstance(audio, (FLAC, WAVE)) else 0

    # Extract tags
    raw_title = extract_tag_value(audio, ["TIT2", "title", "TITLE", "\xa9nam"])
    raw_artist = extract_tag_value(audio, ["TPE1", "artist", "ARTIST", "\xa9ART"])
    raw_album = extract_tag_value(audio, ["TALB", "album", "ALBUM", "\xa9alb"])
    raw_year = extract_tag_value(audio, ["TDRC", "TYER", "date", "DATE", "\xa9day"])
    raw_track = extract_tag_value(audio, ["TRCK", "tracknumber", "TRACKNUMBER", "trkn"])

    # Fallback to filename if title is blank
    if not raw_title:
        base = os.path.splitext(os.path.basename(file_path))[0]
        raw_title = base

    # Acoustic fingerprint
    fingerprint = get_acoustic_fingerprint(file_path)

    file_record = {
        "file_path": os.path.abspath(file_path),
        "mtime": mtime,
        "file_size": file_size,
        "md5_hash": md5_hash,
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "is_lossless": is_lossless,
        "channels": channels,
        "format": ext.lstrip(".").upper(),
        "fingerprint": fingerprint,
        "raw_title": raw_title,
        "raw_artist": raw_artist,
        "raw_album": raw_album,
        "raw_year": raw_year,
        "raw_track": raw_track,
    }

    if db:
        db.save_cached_file(file_record)

    return file_record


def scan_directory(directory_path: str, db: Optional[Database] = None) -> List[Dict[str, Any]]:
    """Recursively scan an entire directory for audio tracks."""
    results = []
    if not os.path.exists(directory_path):
        return results

    for root, _, files in os.walk(directory_path):
        # Skip trash directory
        if "_Duplicates_Trash" in root:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, f)
                rec = scan_file(full_path, db=db)
                if rec:
                    results.append(rec)
    return results
