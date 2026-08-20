@echo off
echo ============================================
echo   Among Us Mobile Auto Suite — Launcher
echo ============================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install from python.org
    pause
    exit /b 1
)

REM Install deps silently
echo Installing dependencies...
pip install -r requirements.txt -q

REM Launch
echo Launching...
python among_us_auto.py

pause
