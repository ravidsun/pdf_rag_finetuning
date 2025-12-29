#!/bin/bash
# ============================================================================
# QA Generator - Linux/Mac Bash Runner
# ============================================================================

echo "========================================"
echo "QA Generator - Batch Processing"
echo "========================================"
echo

# Change to script directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found"
    echo "Please create config.yaml from config.yaml.example"
    exit 1
fi

# Run the QA generator
echo "Starting QA generation..."
echo
python3 scripts/qa_generator.py --config config.yaml

# Check exit code
if [ $? -ne 0 ]; then
    echo
    echo "ERROR: QA generation failed"
    exit 1
else
    echo
    echo "QA generation completed successfully!"
fi
