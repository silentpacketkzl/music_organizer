"""
Tests for Deduplication Engine & Quality Evaluator.
"""
from music_cleaner.deduper import calculate_quality_score, deduplicate_library, compare_two_fingerprints


def test_quality_score_prefers_lossless():
    flac_track = {
        "file_path": "song.flac",
        "is_lossless": 1,
        "bitrate": 850,
        "sample_rate": 44100,
        "raw_title": "Song",
        "raw_artist": "Artist",
    }
    mp3_320 = {
        "file_path": "song.mp3",
        "is_lossless": 0,
        "bitrate": 320,
        "sample_rate": 44100,
        "raw_title": "Song",
        "raw_artist": "Artist",
    }
    assert calculate_quality_score(flac_track) > calculate_quality_score(mp3_320)


def test_quality_score_prefers_higher_bitrate():
    mp3_320 = {
        "file_path": "song_320.mp3",
        "is_lossless": 0,
        "bitrate": 320,
        "sample_rate": 44100,
    }
    mp3_128 = {
        "file_path": "song_128.mp3",
        "is_lossless": 0,
        "bitrate": 128,
        "sample_rate": 44100,
    }
    assert calculate_quality_score(mp3_320) > calculate_quality_score(mp3_128)


def test_exact_md5_deduplication():
    files = [
        {
            "file_path": "/dir1/song.mp3",
            "md5_hash": "hash111",
            "duration": 180.0,
            "bitrate": 320,
            "sample_rate": 44100,
            "is_lossless": 0,
            "fingerprint": "fp1",
            "raw_title": "Track 1",
            "raw_artist": "Artist A",
        },
        {
            "file_path": "/dir2/song_copy.mp3",
            "md5_hash": "hash111",  # Same exact MD5
            "duration": 180.0,
            "bitrate": 320,
            "sample_rate": 44100,
            "is_lossless": 0,
            "fingerprint": "fp1",
            "raw_title": "Track 1",
            "raw_artist": "Artist A",
        },
        {
            "file_path": "/dir1/unique_song.mp3",
            "md5_hash": "hash222",
            "duration": 200.0,
            "bitrate": 320,
            "sample_rate": 44100,
            "is_lossless": 0,
            "fingerprint": "fp2",
            "raw_title": "Unique Track",
            "raw_artist": "Artist B",
        }
    ]

    res = deduplicate_library(files)
    assert len(res["keepers"]) == 2
    assert len(res["duplicates"]) == 1
    assert res["duplicates"][0]["file"]["file_path"] in ["/dir1/song.mp3", "/dir2/song_copy.mp3"]
    assert "Exact MD5" in res["duplicates"][0]["reason"]


def test_acoustic_waveform_deduplication():
    # Two files with DIFFERENT MD5s (e.g. FLAC vs MP3 re-encode of the exact same audio waveform)
    files = [
        {
            "file_path": "/lossless/track.flac",
            "md5_hash": "flac_hash_aaa",
            "duration": 195.0,
            "bitrate": 900,
            "sample_rate": 44100,
            "is_lossless": 1,
            "fingerprint": "MATCHING_CHROMAPRINT_WAVEFORM",
            "raw_title": "A Chit",
            "raw_artist": "Sai Htee Saing",
        },
        {
            "file_path": "/lossy/track.mp3",
            "md5_hash": "mp3_hash_bbb",
            "duration": 195.0,
            "bitrate": 192,
            "sample_rate": 44100,
            "is_lossless": 0,
            "fingerprint": "MATCHING_CHROMAPRINT_WAVEFORM",
            "raw_title": "A Chit",
            "raw_artist": "Sai Htee Saing",
        }
    ]

    res = deduplicate_library(files)
    assert len(res["keepers"]) == 1
    assert res["keepers"][0]["file_path"] == "/lossless/track.flac"
    assert len(res["duplicates"]) == 1
    assert res["duplicates"][0]["file"]["file_path"] == "/lossy/track.mp3"
    assert "Acoustic duplicate" in res["duplicates"][0]["reason"]
