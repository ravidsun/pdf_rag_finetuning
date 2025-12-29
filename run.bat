@echo off
REM ============================================================================
REM QA Generator - Windows Batch Runner
REM ============================================================================

echo ========================================
echo QA Generator - Batch Processing
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if config.yaml exists
if not exist "config.yaml" (
    echo ERROR: config.yaml not found
    echo Please create config.yaml from config.yaml.example
    pause
    exit /b 1
)

REM Run the QA generator
echo Starting QA generation...
echo.
python scripts\qa_generator.py --config config.yaml

REM Check exit code
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
