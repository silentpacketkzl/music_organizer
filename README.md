# 🎵 Burmese Audio Deduper & Myanglish Tag Cleaner (Web GUI & CLI)

A tool designed to clean up messy local audio libraries:
- **Acoustic & MD5 Deduplication**: Identifies exact files and re-encoded songs (e.g. FLAC vs MP3 320k vs MP3 128k) using Chromaprint (`fpcalc`) waveform matching and MD5.
- **Burmese to Myanglish (Burglish)**: Automatically detects Myanmar Unicode / Zawgyi script in tags and translates them to clean English phonetics (e.g., `စိုင်းထီးဆိုင်` -> `Sai Htee Saing`, `လေးဖြူ` -> `Lay Phyu`).
- **Safe & Non-Destructive**: Zero permanent deletions. Duplicates are moved to `_Duplicates_Trash`. Everything is logged in SQLite and can be rolled back anytime.
- **Modern Web GUI & CLI**: Use either the interactive web browser dashboard or the command-line interface.

---

## 🚀 Quick Start: Web GUI Installation

To run the Web GUI locally on your computer:

### Step 1: Install System Prerequisites

#### **On macOS (using Homebrew)**
```bash
# 1. Install Node.js & Python (if not already installed)
brew install node python

# 2. Install ffmpeg and Chromaprint (fpcalc) audio analyzer
brew install ffmpeg chromaprint
```

#### **On Windows**
1. Install [Node.js (LTS)](https://nodejs.org/) and [Python 3.10+](https://www.python.org/). Make sure to check **"Add Python to PATH"** during installation.
2. Install `ffmpeg`:
   - Open PowerShell as Administrator and run:
     ```powershell
     winget install Gyan.FFmpeg
     ```
3. Download `fpcalc` (Chromaprint):
   - Download the Windows binary from [AcoustID Chromaprint Releases](https://acoustid.org/chromaprint).
   - Extract `fpcalc.exe` and place it in your system PATH (e.g., `C:\Windows\System32` or in your project folder).

#### **On Ubuntu / Debian Linux**
```bash
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm ffmpeg libchromaprint-tools
```

---

### Step 2: Install Project Dependencies

Open your terminal in this project folder:

```bash
# 1. Install Python packages
pip install -r requirements.txt

# 2. Install Node.js frontend/backend dependencies
npm install
```

---

### Step 3: Launch the Web GUI

Run this single command:

```bash
npm run dev
```

Now open your web browser to:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 💻 How to Use the Web GUI

1. **Test with Sample Audio**:
   - Click **"Generate Test Audio"** on the dashboard.
   - It will create 6 sample tracks in `/tmp/music_test` with real acoustic duplicate pairings and Burmese tags.
2. **Preview Safely (Dry-Run Mode)**:
   - Enter the path to your music folder (e.g. `/Users/yourname/Music` or `D:\Music`).
   - Leave **"Dry-Run (Preview)"** selected.
   - Click **"Simulate Deduplication"**.
   - You can review the exact list of keepers, duplicates, and Myanglish tag conversions without changing any files on your disk.
3. **Apply Changes**:
   - Switch the toggle to **"Apply (Move & Tag)"**.
   - Click **"Execute Reorganization"**.
   - The tool will organize your music folder and isolate duplicates in `_Duplicates_Trash`.
4. **Undo / Rollback**:
   - Click **"Undo Last Session"** at any time to instantly restore all files back to their original locations.

---

## ⚙️ Optional: OpenAI API Key for Advanced AI Transliteration

The app includes an **offline phonetic dictionary** for standard Burmese music terms and artists. If you want to use OpenAI (`gpt-4o-mini`) for rare phrases or complex lyrics:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Add your key:
   ```env
   OPENAI_API_KEY="sk-..."
   ```

---

## 📟 CLI Usage (Without Web Browser)

You can also run everything directly from the command line:

```bash
# Safe preview
python3 main.py --scan "/path/to/music" --dry-run

# Execute changes
python3 main.py --scan "/path/to/music" --apply

# Rollback last session
python3 main.py --undo
```
