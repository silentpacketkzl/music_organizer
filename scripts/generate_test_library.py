"""
Generator script to create realistic synthetic audio test library in /tmp/music_test.
Encodes FLAC and MP3 files with real audio signals and tags with Burmese Unicode/Zawgyi.
"""
import os
import shutil
import subprocess
import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK

TEST_DIR = "/tmp/music_test"


def create_synthetic_audio(dest_path: str, song_id: int, duration: float, fmt: str, bitrate: str = "320k"):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    # Generate distinct polyphonic frequency-modulated signal for each song
    if song_id == 1:
        expr = "sin(440*2*PI*t)*cos(220*2*PI*t)+sin(880*2*PI*t*t)"
    elif song_id == 2:
        expr = "sin(1200*2*PI*t)*sin(600*2*PI*t)+cos(350*2*PI*t*t)"
    else:
        expr = "sin(2400*2*PI*t)+sin(1750*2*PI*t*t)+cos(800*2*PI*t)"

    if fmt == "flac":
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"aevalsrc={expr}:duration={duration}",
            "-c:a", "flac", "-sample_fmt", "s16", "-ar", "44100",
            dest_path
        ]
    elif fmt == "mp3":
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"aevalsrc={expr}:duration={duration}",
            "-c:a", "libmp3lame", "-b:a", bitrate, "-ar", "44100",
            dest_path
        ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def tag_flac(path: str, title: str, artist: str, album: str, year: str, track: str):
    audio = FLAC(path)
    audio["title"] = [title]
    audio["artist"] = [artist]
    audio["album"] = [album]
    audio["date"] = [year]
    audio["tracknumber"] = [track]
    audio.save()


def tag_mp3(path: str, title: str, artist: str, album: str, year: str, track: str):
    try:
        id3 = ID3(path)
    except Exception:
        id3 = ID3()
    id3["TIT2"] = TIT2(encoding=3, text=title)
    id3["TPE1"] = TPE1(encoding=3, text=artist)
    id3["TALB"] = TALB(encoding=3, text=album)
    id3["TDRC"] = TDRC(encoding=3, text=year)
    id3["TRCK"] = TRCK(encoding=3, text=track)
    id3.save(path)


def generate():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)

    print(f"Generating synthetic audio test files in {TEST_DIR}...")

    # Track 1: Lossless Master (FLAC)
    t1_flac = os.path.join(TEST_DIR, "Master_Recordings", "SaiHteeSaing_MinThein.flac")
    create_synthetic_audio(t1_flac, song_id=1, duration=5.0, fmt="flac")
    tag_flac(t1_flac, title="မင်းသိမ်း", artist="စိုင်းထီးဆိုင်", album="အချစ်ဆုတောင်း", year="1998", track="01")

    # Track 1: Exact byte-for-byte duplicate (MD5 match) in Downloads/
    t1_exact = os.path.join(TEST_DIR, "Downloads", "SaiHteeSaing_MinThein_Copy.flac")
    os.makedirs(os.path.dirname(t1_exact), exist_ok=True)
    shutil.copy2(t1_flac, t1_exact)

    # Track 1: Acoustic duplicate re-encoded to 128kbps MP3 with Zawgyi tag
    t1_acoustic_dupe = os.path.join(TEST_DIR, "Old_Rips", "Track01_Lossy.mp3")
    create_synthetic_audio(t1_acoustic_dupe, song_id=1, duration=5.0, fmt="mp3", bitrate="128k")
    tag_mp3(t1_acoustic_dupe, title="မင္းသိမ္း", artist="စိုင္းထီးဆိုင္", album="အခ်စ္ဆုေတာင္း", year="1998", track="01")

    # Track 2: Lossy High Quality 320k MP3
    t2_mp3_320 = os.path.join(TEST_DIR, "Rock", "LayPhyu_ALwan_320k.mp3")
    create_synthetic_audio(t2_mp3_320, song_id=2, duration=5.0, fmt="mp3", bitrate="320k")
    tag_mp3(t2_mp3_320, title="အလွမ်း", artist="လေးဖြူ", album="သီချင်းများ", year="2002", track="02")

    # Track 2: Acoustic duplicate lower quality 128k MP3
    t2_mp3_128 = os.path.join(TEST_DIR, "Unsorted", "ALwan_low_quality.mp3")
    create_synthetic_audio(t2_mp3_128, song_id=2, duration=5.0, fmt="mp3", bitrate="128k")
    tag_mp3(t2_mp3_128, title="အလွမ်း", artist="လေးဖြူ", album="သီချင်းများ", year="2002", track="02")

    # Track 3: Unique Track
    t3_unique = os.path.join(TEST_DIR, "Pop", "NayMin_Summer.mp3")
    create_synthetic_audio(t3_unique, song_id=3, duration=5.0, fmt="mp3", bitrate="256k")
    tag_mp3(t3_unique, title="နေမင်း", artist="နီနီခင်ဇော်", album="နွေ", year="2016", track="03")

    print(f"✓ Generated 6 synthetic audio tracks in {TEST_DIR}.")
    for root, _, files in os.walk(TEST_DIR):
        for f in files:
            p = os.path.join(root, f)
            print(f"   • {os.path.relpath(p, TEST_DIR)} ({os.path.getsize(p)} bytes)")


if __name__ == "__main__":
    generate()
