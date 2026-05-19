@echo off
echo ============================================================
echo SQL Saturday Loader - sqlsat1147 (plain-text format)
echo ============================================================

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found on PATH.
    pause
    exit /b 1
)

pip install pyodbc python-dotenv -q

echo.
python load_1147.py

echo.
pause
