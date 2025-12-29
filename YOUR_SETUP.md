# Your System Configuration

This file documents the specific configuration for your system.

## Configured Paths

| Setting | Path |
|---------|------|
| **Input Folder** | `D:/MyProjects/data/input` |
| **Output Folder** | `D:/MyProjects/data/output` |
| **Project Root** | `d:\MyProjects\pdf_rag_finetuning` |

## Folder Status

✅ Input folder created: `D:\MyProjects\data\input`
✅ Output folder created: `D:\MyProjects\data\output`

## Configuration Files

1. **[.env](.env)** - Environment variables (PRIMARY)
   ```env
   INPUT_FOLDER=D:/MyProjects/data/input
   OUTPUT_FOLDER=D:/MyProjects/data/output
   ```

2. **[config.yaml](config.yaml)** - YAML configuration (SECONDARY)
   ```yaml
   paths:
     input_folder: "D:/MyProjects/data/input"
     output_folder: "D:/MyProjects/data/output"
   ```

## Next Steps

### 1. Add Your PDF Files

Copy your PDF files to the input folder:
```bash
# Example:
copy "C:\Downloads\*.pdf" "D:\MyProjects\data\input\"
```

Or manually drag and drop PDFs into: `D:\MyProjects\data\input`

### 2. Verify Ollama is Running

```bash
# Check if Ollama is installed
ollama --version

# Check if model is downloaded
ollama list

# Should see: qwen2.5:14b
```

If model is not downloaded:
```bash
ollama pull qwen2.5:14b
```

### 3. Run the Project

#### Option A: Using Batch Script (Easiest)
Double-click: [run_fresh.bat](run_fresh.bat)

#### Option B: Using Command Line
```bash
cd d:\MyProjects\pdf_rag_finetuning
python scripts\qa_generator.py --config config.yaml
```

#### Option C: Direct Command
```bash
python scripts\qa_generator.py "D:/MyProjects/data/input" -o "D:/MyProjects/data/output"
```

## Expected Output

Generated files will be saved to: `D:\MyProjects\data\output`

```
D:\MyProjects\data\output\
├── checkpoint.json              # Resume checkpoint
├── progress.json                # Overall progress
├── qa_generation.log            # Log file
├── Book1_qa.jsonl              # Individual book outputs
├── Book2_qa.jsonl
├── ...
└── all_books_combined_qa.jsonl  # Combined output
```

## Quick Commands

### Check Status
```bash
python scripts\qa_generator.py --status -o "D:/MyProjects/data/output"
```

### Resume Processing
```bash
python scripts\qa_generator.py --config config.yaml
```

### Start Fresh (Ignore Checkpoints)
```bash
python scripts\qa_generator.py --config config.yaml --no-resume
```

### Generate More QA Pairs Per Page
Edit [.env](.env) and change:
```env
QA_MULTIPLIER=3.0  # 3 QA pairs per page instead of 2
```

## Troubleshooting

### If input folder is not found:
1. Check path in [.env](.env): `INPUT_FOLDER=D:/MyProjects/data/input`
2. Verify folder exists: `dir "D:\MyProjects\data\input"`
3. Make sure PDFs are in the folder

### If Ollama connection fails:
1. Start Ollama service: `ollama serve`
2. Verify in [.env](.env): `OLLAMA_BASE_URL=http://localhost:11434`
3. Check model is downloaded: `ollama list`

### If permissions error on output:
1. Check folder is writable: `dir "D:\MyProjects\data\output"`
2. Run terminal as Administrator (if needed)

## System Requirements

- ✅ Python 3.8+ installed
- ✅ Ollama installed and running
- ✅ qwen2.5:14b model downloaded (~8GB)
- ✅ Python dependencies installed: `pip install -r requirements.txt`
- ✅ Input folder: `D:\MyProjects\data\input`
- ✅ Output folder: `D:\MyProjects\data\output`

## Ready to Run!

Your system is configured and ready. Just add your PDF files to:
```
D:\MyProjects\data\input
```

Then run:
```bash
run_fresh.bat
```

---

For more help, see:
- [SETUP.md](SETUP.md) - Detailed setup guide
- [QUICK_SETUP.md](QUICK_SETUP.md) - 5-minute quick start
- [README.md](README.md) - Project overview
