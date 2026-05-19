@echo off
echo ============================================================
echo SQL Saturday - Load events 1128, 1135, 1139, 1140, 1145, 1147
echo ============================================================

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found on PATH.
    pause
    exit /b 1
)

echo Installing/verifying dependencies...
pip install pyodbc python-dotenv -q

echo.
python load_events.py

echo.
pause
