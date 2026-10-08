@echo off
setlocal

set "ROOT=%~dp0.."
set "VENV=%~dp0venv"
set "PYTHON=%VENV%\Scripts\python.exe"

where py >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python 3.11 or newer and try again.
    exit /b 1
)

if not exist "%PYTHON%" (
    echo Creating shared virtual environment...
    py -3 -m venv "%VENV%"
    if errorlevel 1 exit /b 1
)

echo Updating pip...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo Installing stage dependencies...
for %%F in (
    "%ROOT%\01_MP4_to_MP3\backend\requirements.txt"
    "%ROOT%\02_MP3_to_Text\backend\requirements.txt"
    "%ROOT%\03_Text_to_Keyword\backend\requirements.txt"
) do (
    if not exist "%%~F" (
        echo Missing requirements file: %%~F
        exit /b 1
    )
    "%PYTHON%" -m pip install -r "%%~F"
    if errorlevel 1 exit /b 1
)

echo.
echo Setup complete. Run start_all.bat to start the services.
