#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "Starting server at http://127.0.0.1:8000"
echo ""
uvicorn main:app --reload
