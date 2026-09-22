# Implementation Plan Artifact: Burmese Audio Library Deduplication & Myanglish Transliteration Engine

## 1. System Verification Status
- **Python Runtime:** Python 3.10.12 / 3.11.2 (Active and verified)
- **Audio Processing Binaries:**
  - `fpcalc` (Chromaprint v1.5.1): Verified at `/usr/bin/fpcalc`
  - `ffmpeg` (v4.4.2): Verified at `/usr/bin/ffmpeg`
- **Python Libraries:**
  - `mutagen` (v1.48.1): Audio metadata tagging and inspection
  - `pyacoustid` (v1.3.1): Chromaprint acoustic waveform fingerprinting
  - `pytest` (v9.1.1): Test suite runner
  - `openai` (v3.17.0): Transliteration engine (`gpt-4o-mini`)
  - `sqlite3`: Native relational caching database

---

## 2. Module Breakdown & Responsibilities

```
music_cleaner/
├── __init__.py
├── main.py              # CLI entry point (argparse: --scan, --dry-run, --apply, --trash-dir, etc.)
├── scanner.py           # Recursive filesystem walker, audio metadata reader (mutagen), file hashing
├── deduper.py           # Exact (MD5) & Acoustic (Chromaprint/fpcalc) grouping and quality evaluator
├── transliterate.py     # Batch GPT transliteration engine (Unicode/Zawgyi -> Myanglish) with SQLite caching
├── organizer.py         # Tag writer & safe file reorganizer (dry-run mode, trash routing, undo manifest)
├── db.py                # SQLite cache manager for hashes, fingerprints, and transliteration strings
└── tests/
    ├── __init__.py
    ├── test_scanner.py
    ├── test_deduper.py
    ├── test_transliterate.py
    └── test_organizer.py
```

### Detailed Component Roles
1. **`db.py` (Persistence & Cost Minimization):**
   - Maintains `cache.db` to prevent redundant audio re-fingerprinting and redundant LLM API calls.
   - Fast lookup tables indexed by file path, mtime, audio hash, and Burmese text token.
2. **`scanner.py` (Audio Ingestion & Quality Extraction):**
   - Recursively traverses input directory for `.mp3`, `.flac`, `.m4a`, `.wav`, `.ogg`.
   - Computes fast MD5 content hash.
   - Extracts metadata (Title, Artist, Album, Year, Track Number) via `mutagen`.
   - Extracts audio quality specs: format (lossless vs lossy), bitrate (kbps), sample rate (Hz), channels, and exact duration (seconds).
3. **`deduper.py` (Two-Tier Duplicate Detection & Quality Arbiter):**
   - **Tier 1 (Exact):** Groups files with identical MD5 hashes.
   - **Tier 2 (Acoustic):** Fingerprints tracks using `fpcalc` / `pyacoustid`. Groups tracks with matching fingerprints and matching duration (within ±3s tolerance).
   - **Quality Scoring Formula:**
     $$\text{Score} = (\text{is\_lossless} \times 10000) + \text{bitrate\_kbps} + (\text{sample\_rate} / 1000)$$
   - The highest-scoring track is crowned **Keeper**; all others in the duplicate group are flagged as **Trash Candidates**.
4. **`transliterate.py` (AI Burmese -> Myanglish Transliteration Engine):**
   - Collects all unique Burmese strings from Artist, Album, and Title tags.
   - Checks `cache.db` first. Any cache misses are batched in groups of 25-30 items.
   - Prompts `gpt-4o-mini` (with fallback to Gemini API if configured) with JSON-schema output format:
     - Handles both standard Myanmar Unicode and legacy Zawgyi encoding.
     - Maps colloquial Burmese titles and names to standard, clean Latin Myanglish (e.g. `မင်းသိမ်း` -> `Min Thein`, `အချစ်ဆုတောင်း` -> `A Chit Su Taung`).
   - Caches results immediately into `cache.db`.
5. **`organizer.py` (Safe Relocation & Tag Updating):**
   - Target pattern:
     `Music/{Artist_Myanglish}/[{Year}] {Album_Myanglish}/{Track} - {Title_Myanglish}.{ext}`
   - If `--dry-run`: prints clear formatted table and diff of planned actions without modifying disk.
   - If `--apply`:
     - Updates audio tags with normalized Myanglish tags via `mutagen`.
     - Relocates duplicate files to `_Duplicates_Trash/` (maintaining original filename and provenance metadata).
     - Relocates and renames keeper files into tidy structured folders.
     - Writes `manifest_rollback.json` for safety and instant reversal capability.
6. **`main.py` (CLI Interface):**
   - Clean colorized terminal logging with rich summary tables.
   - Supports:
     `python main.py --scan <path> [--dry-run | --apply] [--trash-dir <path>] [--openai-key <key>]`

---

## 3. SQLite Cache Schema (`cache.db`)

```sql
-- Track file metadata and hashes
CREATE TABLE IF NOT EXISTS file_cache (
    file_path TEXT PRIMARY KEY,
    mtime REAL NOT NULL,
    file_size INTEGER NOT NULL,
    md5_hash TEXT NOT NULL,
    duration REAL NOT NULL,
    bitrate INTEGER NOT NULL,
    sample_rate INTEGER NOT NULL,
    is_lossless INTEGER NOT NULL,
    fingerprint TEXT,
    raw_title TEXT,
    raw_artist TEXT,
    raw_album TEXT,
    raw_year TEXT,
    raw_track TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fingerprint index for quick acoustic matching
CREATE INDEX IF NOT EXISTS idx_md5_hash ON file_cache(md5_hash);
CREATE INDEX IF NOT EXISTS idx_fingerprint ON file_cache(fingerprint);

-- Transliteration cache to minimize LLM token usage
CREATE TABLE IF NOT EXISTS transliteration_cache (
    original_text TEXT PRIMARY KEY,
    myanglish_text TEXT NOT NULL,
    detected_script TEXT, -- 'unicode' or 'zawgyi'
    model_used TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollback audit trail
CREATE TABLE IF NOT EXISTS operations_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'MOVE_TO_TRASH', 'REORGANIZE', 'TAG_UPDATE'
    source_path TEXT NOT NULL,
    destination_path TEXT,
    original_tags_json TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Flowchart / Data Pipeline

```
              +-----------------------------------+
              |  Local Music Directory (Input)    |
              +-----------------+-----------------+
                                |
                                v
               [scanner.py: Read tags & metadata]
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
  [MD5 Checksum Hash]                 [fpcalc: Acoustic Fingerprint]
             |                                     |
             +------------------+------------------+
                                |
                                v
                  [deduper.py: Quality Arbiter]
                - Lossless > Lossy (FLAC > MP3)
                - Higher Bitrate / Sample Rate
                - Winner: KEEPER
                - Losers: DUPLICATES (to _Duplicates_Trash)
                                |
                                v
             [transliterate.py: Burmese Detection]
                - Filter Burmese Unicode / Zawgyi
                - Check SQLite Cache
                - Batch remaining to gpt-4o-mini
                - Obtain Latin Myanglish equivalents
                                |
                                v
                [organizer.py: Plan & Execution]
                                |
        +-----------------------+-----------------------+
        |                                               |
  (--dry-run)                                       (--apply)
        |                                               |
        v                                               v
  Print Preview Table                       - Write Mutagen tags
  No files moved                            - Move dupes to _Duplicates_Trash
                                            - Organize into clean folder hierarchy
                                            - Write rollback manifest
```

---

## 5. Value-Add Proposals & Enhancements (For User Review)

1. **Dual AI Provider Support (OpenAI + Built-in Gemini Fallback):**
   - While OpenAI `gpt-4o-mini` will be the default, we can also support Google Gemini (`gemini-2.5-flash`) as an immediate fallback or option. This allows the tool to run without requiring the user to supply an OpenAI key if they want zero-setup execution.
2. **Zawgyi & Unicode Detection:**
   - Burmese music files frequently mix Zawgyi and Unicode tags. We will instruct the transliterator prompt and add an automated regex detector to handle both flawlessly.
3. **Interactive Web UI & Visual Runner:**
   - In addition to the CLI, we can hook up a clean web dashboard on port 3000 in this container. Users can drag-and-drop or inspect local folders, preview duplicate waveforms/metadata, view before/after Myanglish tags, and test the CLI with one click.
4. **Reversible Rollback (`--undo`):**
   - Provide a `python main.py --undo` option reading the SQLite operations log to restore files if the user changes their mind.
