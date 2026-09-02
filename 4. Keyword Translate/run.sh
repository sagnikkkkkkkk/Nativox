#!/bin/bash
set -e

echo "==============================================="
echo "  Nativox - Keyword Translation stage"
echo "==============================================="

cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting server on http://127.0.0.1:8011 ..."
echo "(Press CTRL+C to stop)"
echo ""

uvicorn main:app --reload --port 8011
