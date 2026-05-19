@echo off
echo ============================================================
echo Loading 1137.json into (local)\SQL2022
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
python load_1137.py

echo.
pause
