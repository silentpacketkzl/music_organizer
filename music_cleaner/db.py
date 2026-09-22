"""
SQLite Cache and Audit Log Manager for Music Cleaner.
Stores file hashes, acoustic fingerprints, transliterations, and operation logs.
"""
import os
import sqlite3
import json
from typing import Optional, Dict, Any, List


class Database:
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # File analysis cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_cache (
                    file_path TEXT PRIMARY KEY,
                    mtime REAL NOT NULL,
                    file_size INTEGER NOT NULL,
                    md5_hash TEXT NOT NULL,
                    duration REAL NOT NULL,
                    bitrate INTEGER NOT NULL,
                    sample_rate INTEGER NOT NULL,
                    is_lossless INTEGER NOT NULL,
                    channels INTEGER DEFAULT 2,
                    format TEXT NOT NULL,
                    fingerprint TEXT,
                    raw_title TEXT,
                    raw_artist TEXT,
                    raw_album TEXT,
                    raw_year TEXT,
                    raw_track TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_md5_hash ON file_cache(md5_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fingerprint ON file_cache(fingerprint)")

            # Transliteration cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transliteration_cache (
                    original_text TEXT PRIMARY KEY,
                    myanglish_text TEXT NOT NULL,
                    detected_script TEXT,
                    model_used TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Operations log for audit and undo/rollback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    destination_path TEXT,
                    original_tags_json TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get_cached_file(self, file_path: str, mtime: float) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM file_cache WHERE file_path = ? AND ABS(mtime - ?) < 0.001",
                (file_path, mtime)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def save_cached_file(self, file_data: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO file_cache (
                    file_path, mtime, file_size, md5_hash, duration, bitrate,
                    sample_rate, is_lossless, channels, format, fingerprint,
                    raw_title, raw_artist, raw_album, raw_year, raw_track
                ) VALUES (
                    :file_path, :mtime, :file_size, :md5_hash, :duration, :bitrate,
                    :sample_rate, :is_lossless, :channels, :format, :fingerprint,
                    :raw_title, :raw_artist, :raw_album, :raw_year, :raw_track
                )
            """, file_data)
            conn.commit()

    def get_cached_transliteration(self, text: str) -> Optional[str]:
        if not text:
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT myanglish_text FROM transliteration_cache WHERE original_text = ?",
                (text.strip(),)
            )
            row = cursor.fetchone()
            if row:
                return row["myanglish_text"]
        return None

    def get_cached_transliterations_bulk(self, texts: List[str]) -> Dict[str, str]:
        results = {}
        if not texts:
            return results
        cleaned = [t.strip() for t in texts if t and t.strip()]
        if not cleaned:
            return results
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in cleaned)
            cursor.execute(
                f"SELECT original_text, myanglish_text FROM transliteration_cache WHERE original_text IN ({placeholders})",
                cleaned
            )
            for row in cursor.fetchall():
                results[row["original_text"]] = row["myanglish_text"]
        return results

    def save_transliteration(self, original_text: str, myanglish_text: str, detected_script: str = "burmese", model_used: str = "gpt-4o-mini"):
        if not original_text or not original_text.strip():
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO transliteration_cache (
                    original_text, myanglish_text, detected_script, model_used
                ) VALUES (?, ?, ?, ?)
            """, (original_text.strip(), myanglish_text.strip(), detected_script, model_used))
            conn.commit()

    def save_transliterations_bulk(self, mappings: Dict[str, str], detected_script: str = "burmese", model_used: str = "gpt-4o-mini"):
        if not mappings:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            data = [
                (orig.strip(), translit.strip(), detected_script, model_used)
                for orig, translit in mappings.items() if orig and orig.strip()
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO transliteration_cache (
                    original_text, myanglish_text, detected_script, model_used
                ) VALUES (?, ?, ?, ?)
            """, data)
            conn.commit()

    def log_operation(self, session_id: str, action_type: str, source_path: str,
                      destination_path: Optional[str] = None, original_tags: Optional[Dict[str, Any]] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            tags_json = json.dumps(original_tags) if original_tags else None
            cursor.execute("""
                INSERT INTO operations_log (
                    session_id, action_type, source_path, destination_path, original_tags_json
                ) VALUES (?, ?, ?, ?, ?)
            """, (session_id, action_type, source_path, destination_path, tags_json))
            conn.commit()

    def get_operations(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute(
                    "SELECT * FROM operations_log WHERE session_id = ? ORDER BY id DESC",
                    (session_id,)
                )
            else:
                cursor.execute("SELECT * FROM operations_log ORDER BY id DESC")
            return [dict(r) for r in cursor.fetchall()]

    def clear_operations(self, session_id: Optional[str] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("DELETE FROM operations_log WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM operations_log")
            conn.commit()
