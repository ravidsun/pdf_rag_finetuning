@echo off
REM ============================================================================
REM QA Generator - Status Check Runner
REM ============================================================================

echo ========================================
echo QA Generator - Status Check
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run status check
python scripts\qa_generator.py --config config.yaml --status

pause
