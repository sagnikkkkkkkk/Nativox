@echo off
setlocal

for %%P in (8001 8002 8003) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr /r /c:":%%P .*LISTENING"') do (
        powershell -NoProfile -Command "Stop-Process -Id %%I -Force -ErrorAction SilentlyContinue"
    )
)

echo Stopped Nativox services on ports 8001, 8002, and 8003.
