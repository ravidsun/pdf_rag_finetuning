# Run Scripts Guide

Quick reference for all run scripts and batch files.

---

## Available Run Scripts

### Windows (.bat files)

| Script | Purpose | Usage |
|--------|---------|-------|
| `run.bat` | Start/resume processing | Double-click or `run.bat` |
| `run_status.bat` | Check progress | Double-click or `run_status.bat` |
| `run_fresh.bat` | Start fresh (ignore checkpoints) | Double-click or `run_fresh.bat` |

### Linux/Mac (.sh files)

| Script | Purpose | Usage |
|--------|---------|-------|
| `run.sh` | Start/resume processing | `./run.sh` or `bash run.sh` |

---

## Quick Start

### Windows

**1. Double-click `run.bat`**

That's it! The script will:
- Check if Python is installed
- Check if `config.yaml` exists
- Start QA generation
- Show progress in the terminal

**2. Check Progress**

Double-click `run_status.bat` while processing is running.

**3. Stop Processing**

Press `Ctrl+C` in the terminal window.

**4. Resume Processing**

Double-click `run.bat` again - it auto-resumes!

---

### Linux/Mac

**1. Make script executable (first time only)**:
```bash
chmod +x run.sh
```

**2. Run the script**:
```bash
./run.sh
```

Or:
```bash
bash run.sh
```

---

## Detailed Usage

### run.bat / run.sh

**Purpose:** Start QA generation with settings from `config.yaml`

**What it does:**
1. Changes to script directory
2. Checks Python installation
3. Checks for `config.yaml`
4. Runs QA generator
5. Shows success/error message

**Windows Example:**
```cmd
C:\LLM\pdf_rag_finetuning> run.bat

========================================
QA Generator - Batch Processing
========================================

Starting QA generation...

[Output from QA generator...]

QA generation completed successfully!
Press any key to continue . . .
```

**Linux/Mac Example:**
```bash
$ ./run.sh

========================================
QA Generator - Batch Processing
========================================

Starting QA generation...

[Output from QA generator...]

QA generation completed successfully!
```

---

### run_status.bat

**Purpose:** Check current progress without interrupting processing

**What it does:**
1. Reads progress files
2. Shows completion percentage
3. Shows active checkpoint
4. Lists completed PDFs

**Example Output:**
```
========================================
QA Generator - Status Check
========================================

============================================================
CURRENT PROGRESS STATUS
============================================================
Output Directory: data\output_qwen

Batch Progress:
  Total PDFs: 34
  Completed: 8
  Remaining: 26
  Completion: 23.5%

Active Checkpoint:
  PDF: Book9.pdf
  Pages Processed: 150/307
  QA Pairs: 284
  Last Updated: 2025-12-29T14:30:45

Completed PDFs:
  ✓ Book1
  ✓ Book2
  ✓ Book3
  ...
============================================================

Press any key to continue . . .
```

---

### run_fresh.bat

**Purpose:** Start from scratch, ignoring all checkpoints

**What it does:**
1. Asks for confirmation
2. Ignores `checkpoint.json` and `progress.json`
3. Re-processes all PDFs

**Example:**
```
========================================
QA Generator - Fresh Start
========================================

WARNING: This will ignore all existing checkpoints
and start processing from the beginning.

Are you sure? (Y/N): Y

Starting fresh QA generation...

[Processing starts...]
```

**⚠️ Warning:** This doesn't delete existing output files, just ignores progress tracking.

---

## Configuration

All run scripts use `config.yaml` by default.

**To use different config:**

**Windows:**
```cmd
python scripts\qa_generator.py --config my_config.yaml
```

**Linux/Mac:**
```bash
python scripts/qa_generator.py --config my_config.yaml
```

---

## Customizing Run Scripts

### Windows (run.bat)

Edit `run.bat` to customize:

```batch
REM Use different config
python scripts\qa_generator.py --config configs\my_config.yaml

REM Add command-line options
python scripts\qa_generator.py --config config.yaml --qa-multiplier 3.0
```

### Linux/Mac (run.sh)

Edit `run.sh` to customize:

```bash
# Use different config
python3 scripts/qa_generator.py --config configs/my_config.yaml

# Add command-line options
python3 scripts/qa_generator.py --config config.yaml --qa-multiplier 3.0
```

---

## Creating Custom Run Scripts

### Windows: run_custom.bat

```batch
@echo off
echo Starting Custom QA Generation...
cd /d "%~dp0"

REM Use custom config
python scripts\qa_generator.py --config configs\custom.yaml

pause
```

### Linux/Mac: run_custom.sh

```bash
#!/bin/bash
echo "Starting Custom QA Generation..."
cd "$(dirname "$0")"

# Use custom config
python3 scripts/qa_generator.py --config configs/custom.yaml
```

**Make executable:**
```bash
chmod +x run_custom.sh
```

---

## Running in Background

### Windows

**Using start command:**
```cmd
start /B python scripts\qa_generator.py --config config.yaml > output.log 2>&1
```

**Check if running:**
```cmd
tasklist | findstr python
```

**Stop background process:**
```cmd
taskkill /IM python.exe /F
```

### Linux/Mac

**Run in background:**
```bash
nohup ./run.sh > output.log 2>&1 &
```

**Check if running:**
```bash
ps aux | grep qa_generator
```

**Stop background process:**
```bash
pkill -f qa_generator.py
```

---

## Scheduled Runs

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 2 AM)
4. Action: Start a program
5. Program: `C:\LLM\pdf_rag_finetuning\run.bat`

### Linux/Mac (cron)

**Edit crontab:**
```bash
crontab -e
```

**Add line:**
```cron
# Run daily at 2 AM
0 2 * * * cd /path/to/pdf_rag_finetuning && ./run.sh
```

---

## Error Handling

### Python Not Found

**Error:**
```
ERROR: Python is not installed or not in PATH
```

**Solution:**
- Install Python 3.8+
- Add Python to PATH
- Restart terminal

### Config File Not Found

**Error:**
```
ERROR: config.yaml not found
```

**Solution:**
- Create `config.yaml` from template
- Or specify different config:
  ```cmd
  python scripts\qa_generator.py --config path\to\config.yaml
  ```

### Script Won't Run (Linux/Mac)

**Error:**
```
Permission denied: ./run.sh
```

**Solution:**
```bash
chmod +x run.sh
```

---

## Advanced Usage

### Run with Logging

**Windows:**
```cmd
run.bat > logfile.txt 2>&1
```

**Linux/Mac:**
```bash
./run.sh > logfile.txt 2>&1
```

### Run Multiple Configs Sequentially

**Windows (run_all.bat):**
```batch
@echo off
echo Running all configurations...

python scripts\qa_generator.py --config configs\qwen_2x.yaml
python scripts\qa_generator.py --config configs\qwen_3x.yaml
python scripts\qa_generator.py --config configs\llama_fast.yaml

echo All configurations complete!
pause
```

**Linux/Mac (run_all.sh):**
```bash
#!/bin/bash
echo "Running all configurations..."

python3 scripts/qa_generator.py --config configs/qwen_2x.yaml
python3 scripts/qa_generator.py --config configs/qwen_3x.yaml
python3 scripts/qa_generator.py --config configs/llama_fast.yaml

echo "All configurations complete!"
```

---

## Best Practices

### 1. Always Check Status First

Before resuming:
```cmd
run_status.bat
```

### 2. Keep Terminal Open

Don't close the terminal while processing - progress will be lost.

### 3. Use Screen/tmux for Long Runs

**Linux/Mac:**
```bash
# Start screen session
screen -S qa_gen

# Run script
./run.sh

# Detach: Ctrl+A, then D

# Reattach later
screen -r qa_gen
```

### 4. Monitor Disk Space

Ensure enough space for output files before starting.

### 5. Test with Small Dataset First

Use `--target-qa 5` to test configuration before full run.

---

## Summary

**Essential Commands:**

```bash
# Windows
run.bat              # Start/resume
run_status.bat       # Check progress
run_fresh.bat        # Start fresh
Ctrl+C               # Stop

# Linux/Mac
./run.sh             # Start/resume
Ctrl+C               # Stop
```

**Files:**
- `run.bat` - Windows run script
- `run_status.bat` - Windows status check
- `run_fresh.bat` - Windows fresh start
- `run.sh` - Linux/Mac run script
- `config.yaml` - Configuration file

All scripts use `config.yaml` for settings.
