"""
Tests for Burmese to Myanglish Transliteration Engine.
"""
import os
import tempfile
import pytest
from music_cleaner.db import Database
from music_cleaner.transliterate import (
    contains_burmese,
    offline_transliterate,
    TransliterationEngine
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    yield db
    if os.path.exists(path):
        os.remove(path)


def test_contains_burmese():
    assert contains_burmese("စိုင်းထီးဆိုင်") is True
    assert contains_burmese("Lay Phyu") is False
    assert contains_burmese("Track 01 - အချစ်ဆုတောင်း") is True
    assert contains_burmese("Album 1998 (Remastered)") is False


def test_offline_transliteration():
    assert offline_transliterate("စိုင်းထီးဆိုင်") == "Sai Htee Saing"
    assert offline_transliterate("လေးဖြူ") == "Lay Phyu"
    assert offline_transliterate("အချစ်") == "A Chit"
    # English stays clean
    assert offline_transliterate("Hotel California") == "Hotel California"


def test_transliteration_engine_with_caching(temp_db):
    engine = TransliterationEngine(db=temp_db)
    items = ["စိုင်းထီးဆိုင်", "လေးဖြူ", "Already English"]

    results = engine.transliterate_texts(items)
    assert results["စိုင်းထီးဆိုင်"] == "Sai Htee Saing"
    assert results["လေးဖြူ"] == "Lay Phyu"
    assert results["Already English"] == "Already English"

    # Verify cached in database
    cached_val = temp_db.get_cached_transliteration("စိုင်းထီးဆိုင်")
    assert cached_val == "Sai Htee Saing"
