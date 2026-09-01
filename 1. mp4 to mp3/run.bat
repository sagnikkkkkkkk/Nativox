@echo off
cd /d "%~dp0backend"

if not exist venv (
    echo Creating virtual environment...
    py -3.11 -m venv venv
)

call venv\Scripts\activate
pip install -q -r requirements.txt

echo.
echo Starting server at http://127.0.0.1:8000
echo.
uvicorn main:app --reload
