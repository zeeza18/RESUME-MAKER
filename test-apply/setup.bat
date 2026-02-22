@echo off
REM Quick setup script for Windows

echo ============================================================
echo Job Application Automation - Setup
echo ============================================================
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

echo Installing Playwright browsers...
playwright install chromium
echo.

REM Create config files if they don't exist
if not exist "config.yaml" (
    echo Creating config.yaml from example...
    copy config.example.yaml config.yaml
    echo.
)

if not exist ".env" (
    echo Creating .env from example...
    copy .env.example .env
    echo.
)

echo ============================================================
echo Setup complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Run: python quick_setup.py
echo      (This will configure your profile interactively)
echo.
echo   2. Edit .env and set your password:
echo      JOB_APP_PASSWORD=your_password
echo.
echo   3. Verify: python verify_setup.py
echo.
echo   4. Run: run.bat "YOUR_JOB_URL"
echo.
echo ============================================================

pause
