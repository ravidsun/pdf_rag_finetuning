@echo off
REM ============================================================================
REM QA Generator - Fresh Start Runner (Ignore Checkpoints)
REM ============================================================================

echo ========================================
echo QA Generator - Fresh Start
echo ========================================
echo.
echo WARNING: This will ignore all existing checkpoints
echo and start processing from the beginning.
echo.
set /p confirm="Are you sure? (Y/N): "

if /i not "%confirm%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

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

REM Run with --no-resume flag
echo Starting fresh QA generation...
echo.
python scripts\qa_generator.py --config config.yaml --no-resume

if errorlevel 1 (
    echo.
    echo ERROR: QA generation failed
    pause
    exit /b 1
) else (
    echo.
    echo QA generation completed successfully!
    pause
)
