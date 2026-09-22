#!/bin/bash
# 🎵 Launch Burmese Audio Deduper & Myanglish Cleaner Web GUI

echo "=========================================================="
echo " Starting Burmese Audio Deduper & Myanglish Cleaner GUI"
echo "=========================================================="

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not found. Please install Node.js from https://nodejs.org"
    exit 1
fi

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not found. Please install Python from https://www.python.org"
    exit 1
fi

# Install dependencies if node_modules is missing
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo "🚀 Launching Web GUI on http://localhost:3000..."
npm run dev
