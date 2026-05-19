@echo off
echo ============================================================
echo SQL Saturday Job Loader - sqlsat1137_jobs.json
echo ============================================================

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found on PATH. Please install Python and try again.
    pause
    exit /b 1
)

echo Installing/verifying dependencies...
pip install pyodbc -q

echo.
python load_jobs.py

echo.
pause
