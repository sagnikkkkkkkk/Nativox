@echo off
setlocal

echo ===============================================
echo   Nativox - Keyword Translation stage
echo ===============================================

cd backend

if not exist venv (
    echo Creating virtual environment with Python 3.11...
    py -3.11 -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting server on http://127.0.0.1:8011 ...
echo (Press CTRL+C to stop)
echo.

uvicorn main:app --reload --port 8011

endlocal
