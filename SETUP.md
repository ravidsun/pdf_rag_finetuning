# Setup Guide - New System Installation

This guide will help you set up the PDF RAG Fine-tuning QA Generator on a new system.

## Prerequisites

Before you begin, ensure you have the following installed:

### 1. Python (3.8 or higher)

Check if Python is installed:
```bash
python --version
```

If not installed, download from: https://www.python.org/downloads/

### 2. Ollama (Local LLM Server)

Download and install Ollama:
- **Windows/Mac/Linux**: https://ollama.ai

Verify installation:
```bash
ollama --version
```

### 3. Download the Model

Pull the qwen2.5:14b model:
```bash
ollama pull qwen2.5:14b
```

Verify the model is downloaded:
```bash
ollama list
```

---

## Installation Steps

### Step 1: Clone or Copy the Project

If you haven't already, get the project on your new system:
```bash
cd d:\MyProjects
# If using git:
git clone <repository-url> pdf_rag_finetuning
cd pdf_rag_finetuning
```

### Step 2: Install Python Dependencies

```bash
cd d:\MyProjects\pdf_rag_finetuning
pip install -r requirements.txt
```

This will install all required packages including:
- PDF processing libraries (PyPDF2, pdfplumber, PyMuPDF)
- Data processing (numpy, pandas)
- Configuration management (pyyaml, python-dotenv)
- Progress tracking (tqdm, colorama)

### Step 3: Configure Paths (IMPORTANT!)

#### Option A: Using .env file (Recommended)

1. The project already has a `.env` file created. Open it in a text editor:
   ```
   d:\MyProjects\pdf_rag_finetuning\.env
   ```

2. Update the following paths for your system:

   ```env
   # Input PDF folder - WHERE YOUR PDF FILES ARE LOCATED
   INPUT_FOLDER=./input
   # Change to your actual path, for example:
   # INPUT_FOLDER=C:/Users/YourName/Documents/pdfs
   # INPUT_FOLDER=D:/MyProjects/pdfs

   # Output folder - WHERE GENERATED FILES WILL BE SAVED
   OUTPUT_FOLDER=./data/output_qwen
   # Or use absolute path:
   # OUTPUT_FOLDER=C:/Users/YourName/Documents/output

   # Log file location
   LOG_FILE=qa_generation.log
   ```

3. **Path Format Tips**:
   - Use forward slashes `/` (works on both Windows and Linux)
   - OR use double backslashes `\\\\` on Windows
   - Relative paths start with `./` (relative to project root)
   - Absolute paths: `C:/Users/...` or `/home/...`

#### Option B: Using config.yaml

Alternatively, you can edit [config.yaml](config.yaml) directly:

```yaml
paths:
  input_folder: "C:/Users/YourName/Documents/pdfs"
  output_folder: "./data/output_qwen"
  log_file: "qa_generation.log"
```

**Note**: .env file takes precedence over config.yaml

### Step 4: Create Required Folders

Create the input and output folders if they don't exist:

```bash
# Using relative paths (from project root)
mkdir input
mkdir -p data\output_qwen

# Or create your custom folders
# mkdir C:\Users\YourName\Documents\pdfs
# mkdir C:\Users\YourName\Documents\output
```

### Step 5: Add Your PDF Files

Copy your PDF files to the input folder specified in your `.env` file.

```bash
# Example:
# copy "C:\Downloads\*.pdf" "d:\MyProjects\pdf_rag_finetuning\input\"
```

---

## Verify Configuration

Before running, verify your setup:

### Check Python and Dependencies
```bash
python --version
python -c "import yaml, dotenv; print('Dependencies OK')"
```

### Check Ollama Service
```bash
ollama list
# Should show qwen2.5:14b in the list
```

### Check Paths Configuration
Open `.env` and verify:
- [ ] `INPUT_FOLDER` points to folder with your PDFs
- [ ] `OUTPUT_FOLDER` path is writable
- [ ] Folders exist or will be created

---

## Running the Project

### Method 1: Using Batch Scripts (Windows)

#### First Run (Fresh Start)
Double-click [run_fresh.bat](run_fresh.bat) or run:
```bash
run_fresh.bat
```

#### Resume Processing
Double-click [run.bat](run.bat) or run:
```bash
run.bat
```

#### Check Status
Double-click [run_status.bat](run_status.bat) or run:
```bash
run_status.bat
```

### Method 2: Using Python Directly

#### Start Processing
```bash
python scripts\qa_generator.py --config config.yaml
```

#### Start Fresh (Ignore Checkpoints)
```bash
python scripts\qa_generator.py --config config.yaml --no-resume
```

#### Check Status
```bash
python scripts\qa_generator.py --status -o data\output_qwen
```

### Method 3: Using Command-Line Arguments

Override config with command-line arguments:
```bash
python scripts\qa_generator.py "C:/path/to/pdfs" -o "C:/path/to/output"
```

---

## Configuration Options

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `INPUT_FOLDER` | Where PDF files are located | `./input` or `C:/Users/Name/pdfs` |
| `OUTPUT_FOLDER` | Where JSONL files will be saved | `./data/output_qwen` |
| `MODEL_NAME` | Ollama model to use | `qwen2.5:14b` |
| `QA_MULTIPLIER` | QA pairs per page | `2.0` (default) |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `RESUME_ENABLED` | Auto-resume from checkpoint | `true` or `false` |

### Config Priority

Configuration is loaded in this order (later overrides earlier):
1. Default values in code
2. `.env` file
3. `config.yaml` file
4. Command-line arguments

---

## Troubleshooting

### Issue: "Python is not installed or not in PATH"
**Solution**: Install Python from python.org and ensure "Add to PATH" is checked during installation.

### Issue: "Ollama connection error"
**Solution**:
1. Make sure Ollama is running: `ollama serve`
2. Check if model is downloaded: `ollama list`
3. Verify `OLLAMA_BASE_URL` in `.env` is correct

### Issue: "Input folder not found"
**Solution**:
1. Check the path in `.env` file
2. Ensure the folder exists
3. Use absolute paths if relative paths aren't working
4. Check path format (use `/` or `\\\\`)

### Issue: "Permission denied" when writing output
**Solution**:
1. Ensure output folder is writable
2. Run with appropriate permissions
3. Check if folder exists or create it manually

### Issue: "Module not found" errors
**Solution**: Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

---

## Next Steps

After successful setup:

1. **Test Run**: Start with a small test (1-2 PDFs)
2. **Monitor Progress**: Check logs in `qa_generation.log`
3. **Review Output**: Check generated JSONL files in output folder
4. **Adjust Settings**: Modify `.env` if needed (QA_MULTIPLIER, etc.)

---

## Output Files

Your generated files will be in the output folder:

```
output_folder/
├── checkpoint.json          # Resume checkpoint
├── progress.json            # Overall progress
├── Book1_qa.jsonl          # Individual book outputs
├── Book2_qa.jsonl
├── ...
└── all_books_combined_qa.jsonl  # Combined output
```

---

## Support

For more help, see:
- [README.md](Readme.md) - Project overview
- [COMMANDS.md](.github/COMMANDS.md) - Command reference
- [QUICK_START.md](.github/QUICK_START.md) - Quick start guide
- [TROUBLESHOOTING.md](.github/TROUBLESHOOTING.md) - Common issues

---

## Summary Checklist

- [ ] Python 3.8+ installed
- [ ] Ollama installed and running
- [ ] qwen2.5:14b model downloaded
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with correct paths
- [ ] Input folder created and contains PDF files
- [ ] Output folder created (or will be auto-created)
- [ ] Tested: `python scripts\qa_generator.py --help` works

Ready to run! 🚀
