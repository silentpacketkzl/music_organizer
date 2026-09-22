"""
Tests for Library Organizer and Audio Tagging.
"""
import os
import tempfile
import shutil
import pytest
from music_cleaner.db import Database
from music_cleaner.organizer import (
    sanitize_filename,
    format_track_number,
    format_year,
    get_target_reorganized_path,
    LibraryOrganizer
)


@pytest.fixture
def temp_env():
    work_dir = tempfile.mkdtemp()
    db_path = os.path.join(work_dir, "test_cache.db")
    db = Database(db_path)
    yield {"work_dir": work_dir, "db": db}
    shutil.rmtree(work_dir, ignore_errors=True)


def test_filename_sanitization():
    assert sanitize_filename("Artist / Name: Test?") == "Artist - Name- Test-"
    assert sanitize_filename("Track 01*") == "Track 01-"
    assert format_track_number("3") == "03"
    assert format_track_number("05/12") == "05"
    assert format_year("2018-04-12") == "2018"
    assert format_year("") == "Unknown Year"


def test_target_reorganized_path():
    file_rec = {"file_path": "/some/path/song.mp3"}
    tags = {
        "artist": "Sai Htee Saing",
        "album": "Best Hits",
        "year": "2000",
        "track": "2",
        "title": "A Chit",
    }
    target = get_target_reorganized_path("/music", file_rec, tags)
    expected = os.path.join("/music", "Sai Htee Saing", "[2000] Best Hits", "02 - A Chit.mp3")
    assert target == expected


def test_organizer_dry_run_vs_apply(temp_env):
    work_dir = temp_env["work_dir"]
    db = temp_env["db"]

    # Create real dummy files
    file_a = os.path.join(work_dir, "file_a.mp3")
    file_b = os.path.join(work_dir, "file_b.mp3")
    with open(file_a, "wb") as f:
        f.write(b"AUDIO_DATA_AAA")
    with open(file_b, "wb") as f:
        f.write(b"AUDIO_DATA_BBB")

    keepers = [{
        "file_path": file_a,
        "raw_title": "Song A",
        "raw_artist": "Artist A",
        "raw_album": "Album 1",
        "raw_year": "2020",
        "raw_track": "1",
    }]
    duplicates = [{
        "file": {
            "file_path": file_b,
            "raw_title": "Song B Copy",
        },
        "reason": "Exact MD5 duplicate",
    }]

    transliteration_map = {
        "Song A": "Song A",
        "Artist A": "Artist A",
        "Album 1": "Album 1",
    }

    # 1. Dry run
    organizer_dry = LibraryOrganizer(db=db, dry_run=True)
    plan = organizer_dry.plan_organization(keepers, duplicates, transliteration_map, work_dir)
    res_dry = organizer_dry.execute_plan(plan)
    assert res_dry["status"] == "dry_run_complete"
    # Files must NOT be moved during dry run
    assert os.path.exists(file_a)
    assert os.path.exists(file_b)

    # 2. Apply run
    organizer_apply = LibraryOrganizer(db=db, dry_run=False)
    res_apply = organizer_apply.execute_plan(plan)
    assert len(res_apply["moved_to_trash"]) == 1
    # file_b moved to _Duplicates_Trash
    assert not os.path.exists(file_b)
    trash_file = res_apply["moved_to_trash"][0]["destination"]
    assert os.path.exists(trash_file)

    # 3. Test Undo / Rollback
    undo_res = organizer_apply.rollback_session()
    assert undo_res["status"] == "rollback_completed"
    assert os.path.exists(file_b)
