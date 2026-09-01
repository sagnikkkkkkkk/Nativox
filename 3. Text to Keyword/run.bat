@echo off
cd /d "%~dp0backend"

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo.
echo Starting Text to Keyword at http://127.0.0.1:8010
echo Press Ctrl+C to stop.
echo.
uvicorn main:app --reload --port 8010
