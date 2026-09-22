"""
File Reorganization and Audio Tagging Module.
Updates tags via mutagen, routes duplicates to _Duplicates_Trash, organizes
keepers into: Music / {Artist_Myanglish} / [{Year}] {Album_Myanglish} / {Track} - {Title_Myanglish}.{ext}
Supports dry-run preview and undo rollback via operations_log.
"""
import os
import shutil
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK
from mutagen.easyid3 import EasyID3

from .db import Database


def sanitize_filename(name: str) -> str:
    """Sanitize string for safe filesystem usage across Linux, macOS, and Windows."""
    if not name:
        return "Unknown"
    # Replace path separators and reserved filesystem characters
    cleaned = re.sub(r'[\\/*?:"<>|]', "-", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(". ")
    return cleaned if cleaned else "Unknown"


def format_track_number(track_str: str) -> str:
    """Format track number into two digits (e.g. '3' -> '01', '03/12' -> '03')."""
    if not track_str:
        return "01"
    # Extract leading digits
    match = re.match(r"(\d+)", str(track_str).strip())
    if match:
        num = int(match.group(1))
        return f"{num:02d}"
    return "01"


def format_year(year_str: str) -> str:
    """Extract 4-digit year or return Unknown Year."""
    if not year_str:
        return "Unknown Year"
    match = re.search(r"(\d{4})", str(year_str))
    if match:
        return match.group(1)
    return sanitize_filename(str(year_str))


def update_audio_tags(file_path: str, tags: Dict[str, str]) -> bool:
    """
    Update audio metadata tags using Mutagen.
    tags dict: {"title": ..., "artist": ..., "album": ..., "year": ..., "track": ...}
    """
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return False

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".mp3":
            # Use ID3 for MP3
            try:
                id3 = ID3(file_path)
            except Exception:
                id3 = ID3()

            if "title" in tags:
                id3["TIT2"] = TIT2(encoding=3, text=tags["title"])
            if "artist" in tags:
                id3["TPE1"] = TPE1(encoding=3, text=tags["artist"])
            if "album" in tags:
                id3["TALB"] = TALB(encoding=3, text=tags["album"])
            if "year" in tags:
                id3["TDRC"] = TDRC(encoding=3, text=tags["year"])
            if "track" in tags:
                id3["TRCK"] = TRCK(encoding=3, text=tags["track"])
            id3.save(file_path)
            return True

        elif ext == ".flac" or isinstance(audio, FLAC):
            if "title" in tags:
                audio["title"] = [tags["title"]]
            if "artist" in tags:
                audio["artist"] = [tags["artist"]]
            if "album" in tags:
                audio["album"] = [tags["album"]]
            if "year" in tags:
                audio["date"] = [tags["year"]]
            if "track" in tags:
                audio["tracknumber"] = [tags["track"]]
            audio.save()
            return True

        else:
            # Generic mutagen dictionary update for m4a, ogg, etc.
            if hasattr(audio, "tags") and audio.tags is not None:
                if ext == ".m4a":
                    if "title" in tags:
                        audio.tags["\xa9nam"] = [tags["title"]]
                    if "artist" in tags:
                        audio.tags["\xa9ART"] = [tags["artist"]]
                    if "album" in tags:
                        audio.tags["\xa9alb"] = [tags["album"]]
                    if "year" in tags:
                        audio.tags["\xa9day"] = [tags["year"]]
                else:
                    for k, v in tags.items():
                        audio.tags[k] = [v]
                audio.save()
                return True
            return False
    except Exception as err:
        print(f"[organizer] Failed to update tags on {file_path}: {err}")
        return False


def get_target_reorganized_path(base_dir: str, file_rec: Dict[str, Any], transliterated_tags: Dict[str, str]) -> str:
    """
    Compute target path matching:
    Music / {Artist_Myanglish} / [{Year}] {Album_Myanglish} / {Track} - {Title_Myanglish}.{ext}
    """
    artist = sanitize_filename(transliterated_tags.get("artist") or "Unknown Artist")
    album = sanitize_filename(transliterated_tags.get("album") or "Single")
    year = format_year(transliterated_tags.get("year", ""))
    track = format_track_number(transliterated_tags.get("track", "01"))
    title = sanitize_filename(transliterated_tags.get("title") or "Unknown Title")
    ext = os.path.splitext(file_rec["file_path"])[1].lower()

    album_folder = f"[{year}] {album}"
    filename = f"{track} - {title}{ext}"

    return os.path.join(base_dir, artist, album_folder, filename)


class LibraryOrganizer:
    def __init__(self, db: Database, dry_run: bool = True, trash_dir: Optional[str] = None):
        self.db = db
        self.dry_run = dry_run
        self.trash_dir = trash_dir

    def plan_organization(
        self,
        keepers: List[Dict[str, Any]],
        duplicates: List[Dict[str, Any]],
        transliteration_map: Dict[str, str],
        library_root: str
    ) -> Dict[str, Any]:
        """
        Build an action plan with exact diffs before writing to disk.
        """
        resolved_trash_dir = self.trash_dir or os.path.join(library_root, "_Duplicates_Trash")

        actions = {
            "trash_actions": [],
            "keeper_actions": [],
            "summary": {
                "total_files": len(keepers) + len(duplicates),
                "keepers_count": len(keepers),
                "duplicates_count": len(duplicates),
                "trash_dir": resolved_trash_dir,
                "dry_run": self.dry_run,
            }
        }

        # Plan duplicates -> trash
        for item in duplicates:
            dupe_file = item["file"]
            src_path = dupe_file["file_path"]
            fname = os.path.basename(src_path)
            dest_path = os.path.join(resolved_trash_dir, fname)

            actions["trash_actions"].append({
                "source": src_path,
                "destination": dest_path,
                "reason": item["reason"],
                "file_info": dupe_file,
            })

        # Plan keepers -> updated tags & reorganized path
        for keeper in keepers:
            src_path = keeper["file_path"]
            raw_title = keeper.get("raw_title", "")
            raw_artist = keeper.get("raw_artist", "")
            raw_album = keeper.get("raw_album", "")
            raw_year = keeper.get("raw_year", "")
            raw_track = keeper.get("raw_track", "")

            # Transliterate tags
            new_title = transliteration_map.get(raw_title, raw_title) or os.path.splitext(os.path.basename(src_path))[0]
            new_artist = transliteration_map.get(raw_artist, raw_artist) or "Unknown Artist"
            new_album = transliteration_map.get(raw_album, raw_album) or "Single"
            new_year = format_year(raw_year)
            new_track = format_track_number(raw_track)

            new_tags = {
                "title": new_title,
                "artist": new_artist,
                "album": new_album,
                "year": new_year,
                "track": new_track,
            }

            dest_path = get_target_reorganized_path(library_root, keeper, new_tags)

            actions["keeper_actions"].append({
                "source": src_path,
                "destination": dest_path,
                "old_tags": {
                    "title": raw_title,
                    "artist": raw_artist,
                    "album": raw_album,
                    "year": raw_year,
                    "track": raw_track,
                },
                "new_tags": new_tags,
                "file_info": keeper,
            })

        return actions

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the organization plan:
        - If dry_run is True: does not modify disk, returns preview.
        - If dry_run is False: moves duplicates to trash, updates tags, moves keepers.
        Logs every step to SQLite for audit and rollback.
        """
        if self.dry_run:
            return {"status": "dry_run_complete", "plan": plan}

        session_id = str(uuid.uuid4())[:8]
        results = {"session_id": session_id, "moved_to_trash": [], "reorganized": [], "errors": []}

        # 1. Process duplicates to trash
        for item in plan["trash_actions"]:
            src = item["source"]
            dest = item["destination"]
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                # Avoid collision if destination exists in trash
                base, ext = os.path.splitext(dest)
                counter = 1
                while os.path.exists(dest):
                    dest = f"{base}_{counter}{ext}"
                    counter += 1

                shutil.move(src, dest)
                self.db.log_operation(
                    session_id=session_id,
                    action_type="MOVE_TO_TRASH",
                    source_path=src,
                    destination_path=dest,
                    original_tags=item.get("file_info")
                )
                results["moved_to_trash"].append({"source": src, "destination": dest})
            except Exception as e:
                results["errors"].append({"action": "MOVE_TO_TRASH", "source": src, "error": str(e)})

        # 2. Process keepers
        for item in plan["keeper_actions"]:
            src = item["source"]
            dest = item["destination"]
            new_tags = item["new_tags"]
            old_tags = item["old_tags"]

            try:
                # Update tags first
                update_audio_tags(src, new_tags)

                # Move if source and dest are different
                if os.path.abspath(src) != os.path.abspath(dest):
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    # Resolve collision if dest exists
                    if os.path.exists(dest) and os.path.abspath(src) != os.path.abspath(dest):
                        base, ext = os.path.splitext(dest)
                        dest = f"{base}_kept{ext}"

                    shutil.move(src, dest)

                self.db.log_operation(
                    session_id=session_id,
                    action_type="REORGANIZE",
                    source_path=src,
                    destination_path=dest,
                    original_tags=old_tags
                )
                results["reorganized"].append({"source": src, "destination": dest, "tags": new_tags})
            except Exception as e:
                results["errors"].append({"action": "REORGANIZE", "source": src, "error": str(e)})

        return results

    def rollback_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Roll back file movements and restore original tags from operations_log.
        """
        ops = self.db.get_operations(session_id=session_id)
        if not ops:
            return {"status": "no_operations_found", "restored": []}

        restored = []
        errors = []

        for op in ops:
            dest = op.get("destination_path")
            src = op.get("source_path")
            tags = op.get("original_tags_json")

            if dest and src and os.path.exists(dest):
                try:
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    shutil.move(dest, src)
                    if tags and op.get("action_type") == "REORGANIZE":
                        import json
                        tags_dict = json.loads(tags)
                        update_audio_tags(src, tags_dict)
                    restored.append({"from": dest, "to": src})
                except Exception as e:
                    errors.append({"dest": dest, "src": src, "error": str(e)})

        # Remove rolled back operations
        self.db.clear_operations(session_id=session_id)
        return {"status": "rollback_completed", "restored": restored, "errors": errors}
