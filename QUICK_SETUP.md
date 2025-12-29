# Quick Setup - 5 Minutes

Fast setup guide for running this project on a new system.

## 1. Install Prerequisites (5 min)

```bash
# Install Ollama from https://ollama.ai
# Download and install for your platform

# Pull the model (required, ~8GB download)
ollama pull qwen2.5:14b

# Verify
ollama list
```

## 2. Install Python Dependencies (1 min)

```bash
cd d:\MyProjects\pdf_rag_finetuning
pip install -r requirements.txt
```

## 3. Configure Paths (1 min)

Open [.env](.env) file and update these two lines:

```env
INPUT_FOLDER=./input          # Change to where your PDFs are
OUTPUT_FOLDER=./data/output_qwen   # Change to where you want output
```

**Examples**:
- `INPUT_FOLDER=C:/Users/YourName/Documents/pdfs`
- `INPUT_FOLDER=D:/MyData/pdfs`
- `INPUT_FOLDER=./input` (relative to project)

**Important**: Use forward slashes `/` or double backslashes `\\\\`

## 4. Create Folders

```bash
# Create folders if they don't exist
mkdir input
mkdir -p data\output_qwen
```

## 5. Add Your PDFs

Copy your PDF files to the input folder:
```bash
# Example:
# copy "C:\Downloads\*.pdf" "d:\MyProjects\pdf_rag_finetuning\input\"
```

## 6. Run!

### Windows (Easy Way)
Double-click [run_fresh.bat](run_fresh.bat)

### Command Line
```bash
python scripts\qa_generator.py --config config.yaml
```

## Done!

The script will:
- ✅ Process all PDFs automatically
- ✅ Generate 2 QA pairs per page
- ✅ Save progress every 50 pages
- ✅ Resume automatically if interrupted

---

## Quick Tips

**Stop Processing**: Press `Ctrl+C`

**Resume**: Run the same command again

**Check Status**:
```bash
python scripts\qa_generator.py --status -o data\output_qwen
```

**Change QA Multiplier**: Edit `.env` file:
```env
QA_MULTIPLIER=3.0  # 3 QA pairs per page
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python from python.org |
| "Ollama connection error" | Start Ollama: `ollama serve` |
| "Input folder not found" | Check path in `.env` file |
| "Module not found" | Run: `pip install -r requirements.txt` |

---

## Need More Help?

See [SETUP.md](SETUP.md) for detailed setup instructions.
