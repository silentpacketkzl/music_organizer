"""
Tests for SQLite Database Cache and Operations Log.
"""
import os
import tempfile
import pytest
from music_cleaner.db import Database


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    yield db
    if os.path.exists(path):
        os.remove(path)


def test_file_cache_operations(temp_db):
    sample_file = {
        "file_path": "/test/song.mp3",
        "mtime": 1700000000.0,
        "file_size": 5000000,
        "md5_hash": "abcdef1234567890abcdef1234567890",
        "duration": 210.5,
        "bitrate": 320,
        "sample_rate": 44100,
        "is_lossless": 0,
        "channels": 2,
        "format": "MP3",
        "fingerprint": "AQAAZEkUSUlCRUEk",
        "raw_title": "အချစ်",
        "raw_artist": "စိုင်းထီးဆိုင်",
        "raw_album": "သီချင်းများ",
        "raw_year": "2000",
        "raw_track": "1",
    }
    temp_db.save_cached_file(sample_file)

    cached = temp_db.get_cached_file("/test/song.mp3", 1700000000.0)
    assert cached is not None
    assert cached["md5_hash"] == "abcdef1234567890abcdef1234567890"
    assert cached["bitrate"] == 320
    assert cached["raw_artist"] == "စိုင်းထီးဆိုင်"

    # Mtime mismatch returns None
    assert temp_db.get_cached_file("/test/song.mp3", 1700000050.0) is None


def test_transliteration_cache(temp_db):
    temp_db.save_transliteration("လေးဖြူ", "Lay Phyu", detected_script="burmese", model_used="test")
    assert temp_db.get_cached_transliteration("လေးဖြူ") == "Lay Phyu"
    assert temp_db.get_cached_transliteration("အချစ်") is None

    # Bulk cache
    temp_db.save_transliterations_bulk({
        "အချစ်": "A Chit",
        "စိုင်းထီးဆိုင်": "Sai Htee Saing"
    })
    bulk = temp_db.get_cached_transliterations_bulk(["အချစ်", "စိုင်းထီးဆိုင်", "unknown"])
    assert bulk["အချစ်"] == "A Chit"
    assert bulk["စိုင်းထီးဆိုင်"] == "Sai Htee Saing"
    assert "unknown" not in bulk


def test_operations_log_and_clear(temp_db):
    temp_db.log_operation("sess1", "MOVE_TO_TRASH", "/path/a.mp3", "/trash/a.mp3", {"title": "Song A"})
    temp_db.log_operation("sess1", "REORGANIZE", "/path/b.mp3", "/music/b.mp3", {"title": "Song B"})

    ops = temp_db.get_operations(session_id="sess1")
    assert len(ops) == 2
    assert ops[0]["action_type"] == "REORGANIZE"  # ordered DESC

    temp_db.clear_operations(session_id="sess1")
    assert len(temp_db.get_operations(session_id="sess1")) == 0
