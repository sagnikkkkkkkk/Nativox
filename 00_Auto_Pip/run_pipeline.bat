@echo off
setlocal

if "%~1"=="" (
    echo Usage: run_pipeline.bat "path\to\video.mp4" [output-folder]
    exit /b 1
)

set "PYTHON=%~dp0venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo Shared virtual environment not found. Run setup.bat first.
    exit /b 1
)

if "%~2"=="" (
    "%PYTHON%" "%~dp0orchestrator.py" "%~1"
) else (
    "%PYTHON%" "%~dp0orchestrator.py" "%~1" --work-dir "%~2"
)
