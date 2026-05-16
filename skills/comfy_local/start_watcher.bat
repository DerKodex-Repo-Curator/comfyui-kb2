@echo off
REM Start the ComfyUI watcher daemon as a background process.
REM Logs to state\watcher.log; PID written to state\watcher.pid.

setlocal
set "SKILL_DIR=%~dp0"
set "PY=%SKILL_DIR%..\..\..\python_embeded\python.exe"

if not exist "%PY%" (
    echo ERROR: python_embeded not found at:
    echo   %PY%
    pause
    exit /b 1
)

REM Make sure websocket-client is installed in the embedded Python
"%PY%" -c "import websocket" 2>NUL
if errorlevel 1 (
    echo Installing websocket-client into python_embeded...
    "%PY%" -m pip install websocket-client
)

REM Launch watcher.py in a hidden background process via PowerShell.
REM PowerShell captures the PID and writes it to state\watcher.pid.
powershell -NoProfile -Command ^
    "$p = Start-Process -FilePath '%PY%' -ArgumentList '%SKILL_DIR%watcher.py' -WindowStyle Hidden -PassThru;" ^
    "Set-Content -Path '%SKILL_DIR%state\watcher.pid' -Value $p.Id;" ^
    "Write-Host ('watcher started, PID = ' + $p.Id)"

echo.
echo Watcher running in background.
echo   Output folder: %SKILL_DIR%..\..\..\outputs_watched\
echo   Log:           %SKILL_DIR%state\watcher.log
echo.
echo Stop with: stop_watcher.bat
echo.
pause
endlocal
