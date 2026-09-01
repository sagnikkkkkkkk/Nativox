#!/usr/bin/env bash
# One-command launcher: creates a venv (first run only), installs
# dependencies, and starts the server on http://127.0.0.1:8010
set -e
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo ""
echo "Starting Text to Keyword at http://127.0.0.1:8010"
echo "Press Ctrl+C to stop."
echo ""
uvicorn main:app --reload --port 8010
