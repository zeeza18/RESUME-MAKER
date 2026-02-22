@echo off
REM Job Application Automation - Easy Run Script for Windows
REM Usage: run.bat "YOUR_JOB_URL"

echo ============================================================
echo Job Application Automation
echo ============================================================

REM Check if URL is provided
if "%~1"=="" (
    echo ERROR: No URL provided!
    echo.
    echo Usage: run.bat "YOUR_JOB_URL"
    echo.
    echo Example:
    echo   run.bat "https://jobs.lenovo.com/en_US/careers/JobDetail?jobId=73488"
    echo.
    echo IMPORTANT: Wrap the URL in quotes!
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo WARNING: Virtual environment not found!
    echo Please run: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if config exists
if not exist "config.yaml" (
    echo WARNING: config.yaml not found!
    echo Please run: python quick_setup.py
    echo.
    pause
    exit /b 1
)

REM Run the tool with the provided URL (already quoted)
echo Running automation...
echo URL: %~1
echo.

python -m apply %1

echo.
echo ============================================================
echo Run complete! Check the runs\ folder for results.
echo ============================================================

pause
