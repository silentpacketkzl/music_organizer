#!/usr/bin/env python3
"""
Burmese Music Library Deduplicator & Myanglish Tag Cleaner CLI.

Features:
- Exact duplicate detection via MD5 hashing
- Acoustic waveform duplicate detection via Chromaprint (fpcalc / pyacoustid)
- Intelligent quality arbiter (Lossless > Lossy, bitrate, sample rate)
- AI-powered Myanmar script (Unicode/Zawgyi) to Myanglish transliteration (gpt-4o-mini)
- Non-destructive routing to _Duplicates_Trash with --dry-run safety
- Undo / Rollback support
"""

import os
import sys
import argparse
import time
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

from music_cleaner.db import Database
from music_cleaner.scanner import scan_directory
from music_cleaner.deduper import deduplicate_library
from music_cleaner.transliterate import TransliterationEngine, contains_burmese
from music_cleaner.organizer import LibraryOrganizer

# ANSI Colors for clean CLI presentation
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_MAGENTA = "\033[95m"
C_DIM = "\033[2m"


def print_banner():
    print(f"\n{C_CYAN}{C_BOLD}======================================================================{C_RESET}")
    print(f"{C_CYAN}{C_BOLD}  🎵  BURMESE AUDIO LIBRARY DEDUPER & MYANGLISH TAG CLEANER  🎵{C_RESET}")
    print(f"{C_CYAN}  MD5 & Chromaprint Waveform Deduplication | Burmese -> Myanglish AI{C_RESET}")
    print(f"{C_CYAN}{C_BOLD}======================================================================{C_RESET}\n")


def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def display_preview(plan: Dict[str, Any], library_root: str):
    trash_actions = plan.get("trash_actions", [])
    keeper_actions = plan.get("keeper_actions", [])

    print(f"\n{C_BOLD}📋 DEDUPLICATION SUMMARY:{C_RESET}")
    print(f"  • Total tracks analyzed : {C_BOLD}{len(keeper_actions) + len(trash_actions)}{C_RESET}")
    print(f"  • Keepers (Best Quality): {C_GREEN}{C_BOLD}{len(keeper_actions)}{C_RESET}")
    print(f"  • Flagged Duplicates    : {C_YELLOW}{C_BOLD}{len(trash_actions)}{C_RESET}")
    print(f"  • Duplicates Trash Dir  : {C_DIM}{plan['summary']['trash_dir']}{C_RESET}\n")

    if trash_actions:
        print(f"{C_YELLOW}{C_BOLD}🗑️  DUPLICATES ROUTED TO TRASH ({len(trash_actions)} files):{C_RESET}")
        for idx, item in enumerate(trash_actions, 1):
            finfo = item["file_info"]
            fmt = finfo.get("format", "AUDIO")
            br = finfo.get("bitrate", 0)
            dur = format_duration(finfo.get("duration", 0))
            lossless_tag = f"{C_MAGENTA}[LOSSLESS]{C_RESET}" if finfo.get("is_lossless") else f"{C_DIM}[LOSSY]{C_RESET}"
            rel_src = os.path.relpath(item["source"], library_root)

            print(f"  {C_BOLD}[{idx:02d}]{C_RESET} {rel_src}")
            print(f"       {lossless_tag} {fmt} {br}kbps | Duration: {dur}")
            print(f"       {C_RED}Reason: {item['reason']}{C_RESET}")
        print()

    print(f"{C_GREEN}{C_BOLD}✨ KEEPERS & REORGANIZATION PLAN ({len(keeper_actions)} tracks):{C_RESET}")
    for idx, item in enumerate(keeper_actions, 1):
        finfo = item["file_info"]
        old_t = item["old_tags"]
        new_t = item["new_tags"]
        rel_src = os.path.relpath(item["source"], library_root)
        rel_dest = os.path.relpath(item["destination"], library_root)

        # Highlight tag transformations
        tag_diff = []
        if old_t["title"] != new_t["title"]:
            tag_diff.append(f"Title: '{old_t['title']}' -> '{C_GREEN}{new_t['title']}{C_RESET}'")
        if old_t["artist"] != new_t["artist"]:
            tag_diff.append(f"Artist: '{old_t['artist']}' -> '{C_GREEN}{new_t['artist']}{C_RESET}'")
        if old_t["album"] != new_t["album"]:
            tag_diff.append(f"Album: '{old_t['album']}' -> '{C_GREEN}{new_t['album']}{C_RESET}'")

        lossless_tag = f"{C_MAGENTA}[LOSSLESS]{C_RESET}" if finfo.get("is_lossless") else f"{C_DIM}[LOSSY]{C_RESET}"
        print(f"  {C_BOLD}[{idx:02d}]{C_RESET} {rel_src} {lossless_tag} ({finfo['format']} {finfo.get('bitrate', 0)}kbps)")
        print(f"       -> {C_CYAN}{rel_dest}{C_RESET}")
        if tag_diff:
            print(f"       🏷️  Tag Updates: {' | '.join(tag_diff)}")
    print()


def run_pipeline(args):
    start_time = time.time()
    db = Database(args.db_path)

    # Handle Undo / Rollback
    if args.undo:
        if not args.json:
            print(f"{C_YELLOW}Initiating rollback from database operations log...{C_RESET}")
        organizer = LibraryOrganizer(db=db, dry_run=False)
        result = organizer.rollback_session()
        if args.json:
            print(json.dumps({"status": "rollback_completed", "restored": result.get("restored", [])}))
        else:
            print(f"{C_GREEN}Rollback complete! Restored {len(result.get('restored', []))} files.{C_RESET}")
        return

    if not args.scan:
        if args.json:
            print(json.dumps({"error": "--scan <path> is required"}))
        else:
            print(f"{C_RED}Error: --scan <path> is required. Use --help for usage.{C_RESET}")
        sys.exit(1)

    scan_dir = os.path.abspath(args.scan)
    if not os.path.exists(scan_dir):
        if args.json:
            print(json.dumps({"error": f"Path does not exist: {scan_dir}"}))
        else:
            print(f"{C_RED}Error: Path does not exist: {scan_dir}{C_RESET}")
        sys.exit(1)

    is_dry_run = not args.apply

    if not args.json:
        print(f"🔍 Scanning directory: {C_BOLD}{scan_dir}{C_RESET}")
    files = scan_directory(scan_dir, db=db)
    if not args.json:
        print(f"✓ Discovered {C_BOLD}{len(files)}{C_RESET} supported audio files.")

    if not files:
        if args.json:
            print(json.dumps({"error": "No audio files found", "files": []}))
        else:
            print("No audio files found. Exiting.")
        return

    # 1. Deduplication
    if not args.json:
        print(f"\n🧬 Analyzing exact MD5 hashes and Chromaprint acoustic waveforms...")
    dedup_results = deduplicate_library(files)
    keepers = dedup_results["keepers"]
    duplicates = dedup_results["duplicates"]

    if not args.json:
        print(f"✓ Identified {C_GREEN}{len(keepers)} keepers{C_RESET} and {C_YELLOW}{len(duplicates)} duplicates{C_RESET}.")

    # 2. Transliteration of Burmese tags
    if not args.json:
        print(f"\n🈴 Extracting Burmese tags and resolving Myanglish transliterations...")
    all_texts_to_transliterate = []
    for k in keepers:
        if k.get("raw_title"): all_texts_to_transliterate.append(k["raw_title"])
        if k.get("raw_artist"): all_texts_to_transliterate.append(k["raw_artist"])
        if k.get("raw_album"): all_texts_to_transliterate.append(k["raw_album"])

    engine = TransliterationEngine(db=db, openai_key=args.openai_key)
    transliteration_map = engine.transliterate_texts(all_texts_to_transliterate)

    burmese_count = sum(1 for t in set(all_texts_to_transliterate) if contains_burmese(t))
    if not args.json:
        print(f"✓ Processed {C_BOLD}{len(all_texts_to_transliterate)}{C_RESET} metadata fields ({burmese_count} Burmese fields transliterated).")

    # 3. Organization & Tagging
    organizer = LibraryOrganizer(db=db, dry_run=is_dry_run, trash_dir=args.trash_dir)
    plan = organizer.plan_organization(
        keepers=keepers,
        duplicates=duplicates,
        transliteration_map=transliteration_map,
        library_root=scan_dir
    )

    if args.json:
        result_payload = {
            "mode": "dry_run" if is_dry_run else "applied",
            "summary": plan["summary"],
            "keepers": plan["keeper_actions"],
            "duplicates": plan["trash_actions"],
            "transliteration_count": burmese_count,
            "elapsed_seconds": round(time.time() - start_time, 2)
        }
        if not is_dry_run:
            exec_result = organizer.execute_plan(plan)
            result_payload["execution"] = exec_result
        print(json.dumps(result_payload, indent=2))
        return

    display_preview(plan, scan_dir)

    if is_dry_run:
        print(f"{C_YELLOW}{C_BOLD}⚠️  DRY RUN MODE ACTIVE (No files were altered or moved).{C_RESET}")
        print(f"To execute these changes safely, re-run with: {C_GREEN}{C_BOLD}python main.py --scan \"{args.scan}\" --apply{C_RESET}\n")
    else:
        print(f"{C_GREEN}{C_BOLD}🚀 APPLYING CHANGES TO DISK...{C_RESET}")
        exec_result = organizer.execute_plan(plan)
        print(f"✓ Session ID        : {C_BOLD}{exec_result.get('session_id')}{C_RESET}")
        print(f"✓ Moved to Trash    : {C_YELLOW}{len(exec_result.get('moved_to_trash', []))} duplicates{C_RESET}")
        print(f"✓ Tagged & Organized: {C_GREEN}{len(exec_result.get('reorganized', []))} keepers{C_RESET}")
        if exec_result.get("errors"):
            print(f"{C_RED}⚠️ Encounted {len(exec_result['errors'])} errors during execution.{C_RESET}")
        print(f"{C_CYAN}Undo anytime with: python main.py --undo{C_RESET}\n")

    elapsed = time.time() - start_time
    print(f"⏱️ Finished in {elapsed:.2f}s.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Burmese Audio Deduplicator & Myanglish Metadata Tag Cleaner",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--scan",
        type=str,
        help="Path to the music directory to scan and organize."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate the reorganization and print diff preview without modifying files (Default: True)."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute tag updates, duplicate isolation, and library restructuring."
    )
    parser.add_argument(
        "--trash-dir",
        type=str,
        default=None,
        help="Custom directory path for isolated duplicates (defaults to <library_root>/_Duplicates_Trash)."
    )
    parser.add_argument(
        "--openai-key",
        type=str,
        default=None,
        help="OpenAI API key override for gpt-4o-mini (otherwise loaded from OPENAI_API_KEY env)."
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="cache.db",
        help="Path to the SQLite cache database (defaults to cache.db)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format."
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Revert the last organization session from SQLite audit logs."
    )

    args = parser.parse_args()
    if not args.json:
        print_banner()
    run_pipeline(args)


if __name__ == "__main__":
    main()
