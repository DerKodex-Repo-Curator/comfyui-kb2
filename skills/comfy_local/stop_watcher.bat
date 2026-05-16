@echo off
REM Stop the ComfyUI watcher daemon.

setlocal
set "SKILL_DIR=%~dp0"
set "PIDFILE=%SKILL_DIR%state\watcher.pid"

if not exist "%PIDFILE%" (
    echo No watcher.pid found at %PIDFILE%
    echo Watcher not running, or it was already stopped.
    pause
    exit /b 0
)

set /p PID=<"%PIDFILE%"
echo Stopping watcher PID=%PID%
taskkill /PID %PID% /F 2>NUL

if errorlevel 1 (
    echo (process not found, removing stale PID file)
)
del "%PIDFILE%" 2>NUL

echo Done.
pause
endlocal
