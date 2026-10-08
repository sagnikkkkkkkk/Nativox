@echo off
setlocal

set "ROOT=%~dp0.."
set "PYTHON=%~dp0venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Shared virtual environment not found.
    echo Run setup.bat first.
    exit /b 1
)

start "01 MP4 to MP3" /D "%ROOT%\01_MP4_to_MP3\backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8001"
start "02 MP3 to Text" /D "%ROOT%\02_MP3_to_Text\backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8002"
start "03 Text to Keyword" /D "%ROOT%\03_Text_to_Keyword\backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8003"
start "04 Keyword to Sentence" /D "%ROOT%\04_Keyword_to_Sentence_Construction" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8004"
start "05b Sentence Reformation" /D "%ROOT%\05b_Sentence_Reformation__Atanu\backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8012"
start "06 Text to MP3" /D "%ROOT%\06_Converted_Text_to_MP3\backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8013"
start "07 Merge MP3 with MP4" /D "%ROOT%\07_Merge_MP3_with_MP4\backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8014"

echo Started all seven stages.
echo Close the server windows or run stop_all.bat to stop them.