# PDF RAG Fine-tuning - Jyotish QA Dataset Generator

Generate high-quality question-answer pairs from Jyotish (Vedic Astrology) PDFs using **qwen2.5:32b** via Ollama.

## Features

✅ **Automatic Resume** - Stop and resume anytime without losing progress
✅ **2x QA Pairs Per Page** - Generates at least 2 QA pairs for every PDF page
✅ **Checkpoint System** - Saves progress after each 50-page batch
✅ **Incremental Saves** - JSONL files update continuously
✅ **Progress Tracking** - Monitor status across sessions
✅ **Graceful Interruption** - Press Ctrl+C to pause safely

---

## Quick Start

> **New System?** See [SETUP.md](SETUP.md) for complete installation guide.

### 1. Prerequisites

- **Ollama installed**: https://ollama.ai (see [INSTALL_OLLAMA.md](INSTALL_OLLAMA.md))
- **qwen2.5:32b model** downloaded: `ollama pull qwen2.5:32b`
- **Python dependencies** installed: `pip install -r requirements.txt`

### 2. Configure Paths (First Time)

Edit [.env](.env) file and set your paths:

```env
# Where your PDF files are located
INPUT_FOLDER=./input

# Where generated JSONL files will be saved
OUTPUT_FOLDER=./data/output_qwen
```

**Tip**: Use forward slashes `/` for paths on all platforms.

### 3. Start Processing

```bash
# Using config file (reads .env automatically)
python scripts/qa_generator.py --config config.yaml
```

Or use batch scripts on Windows:
- **Fresh start**: Double-click [run_fresh.bat](run_fresh.bat)
- **Resume**: Double-click [run.bat](run.bat)
- **Check status**: Double-click [run_status.bat](run_status.bat)

### 4. Check Progress

```bash
python scripts/qa_generator.py --status -o data/output_qwen
```

### 5. Stop and Resume

- **Stop**: Press `Ctrl+C`
- **Resume**: Run the same command again (auto-resumes)

---

## Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](SETUP.md) | **New system setup guide** |
| [QUICK_START.md](.github/QUICK_START.md) | Quick start guide |
| [COMMANDS.md](.github/COMMANDS.md) | Complete command reference |
| [BATCH_PROCESSING_GUIDE.md](.github/BATCH_PROCESSING_GUIDE.md) | Detailed batch processing guide |
| [FEATURES.md](.github/FEATURES.md) | Feature descriptions and technical details |
| [TROUBLESHOOTING.md](.github/TROUBLESHOOTING.md) | Common issues and solutions |
| [CONFIGURATION_GUIDE.md](.github/CONFIGURATION_GUIDE.md) | Configuration options |

---

## Project Structure

```
pdf_rag_finetuning/
├── scripts/
│   └── qa_generator.py             # Main QA generation script
├── data/
│   ├── output_qwen/                # Generated JSONL files
│   │   ├── checkpoint.json         # Current checkpoint
│   │   ├── progress.json           # Overall progress
│   │   ├── Book1_qa.jsonl         # Individual outputs
│   │   └── all_books_combined_qa.jsonl
│   └── training_sample.jsonl       # Sample data
├── src/
│   ├── extractors/                 # PDF extraction modules
│   ├── processors/                 # Processing utilities
│   └── utils/                      # Helper functions (config_loader.py)
├── .github/                        # Documentation
│   ├── BATCH_PROCESSING_GUIDE.md
│   ├── COMMANDS.md
│   ├── CONFIGURATION_GUIDE.md
│   ├── FEATURES.md
│   ├── QUICK_START.md
│   └── TROUBLESHOOTING.md
├── .env                            # Environment variables (customize!)
├── .env.example                    # Environment template
├── config.yaml                     # Configuration file
├── SETUP.md                        # New system setup guide
├── README.md                       # This file
├── run.bat                         # Windows: Resume processing
├── run_fresh.bat                   # Windows: Fresh start
└── run_status.bat                  # Windows: Check status
```

---

## Output Format

Each JSONL file contains entries like:

```json
{
  "id": "An_Introduction_to_Jyotish_p10_0_abc123",
  "source": {
    "pdf_name": "An_Introduction_to_Jyotish_..._nodrm.pdf",
    "page_start": 10,
    "page_end": 12,
    "section_title": "Introduction to Jyotisha"
  },
  "question": "What is Jyotisha according to Vedic tradition?",
  "answer": "Jyotisha is the Science of Tracking Time using Astronomical Events...",
  "qa_type": "definition",
  "difficulty": "easy",
  "tags": ["jyotisha", "vedanga", "fundamentals"],
  "evidence": ["Jyotisha is the Science of Tracking Time..."]
}
```

---

## Key Commands

```bash
# Start/Resume processing (uses config.yaml and .env)
python scripts/qa_generator.py --config config.yaml

# Check status
python scripts/qa_generator.py --status -o data/output_qwen

# Generate 3x QA pairs per page
python scripts/qa_generator.py --config config.yaml --qa-multiplier 3.0

# Start fresh (ignore checkpoints)
python scripts/qa_generator.py --config config.yaml --no-resume

# Override with command-line paths
python scripts/qa_generator.py "C:/path/to/pdfs" -o data/output_qwen
```

**Windows Users**: Use the batch scripts [run.bat](run.bat), [run_fresh.bat](run_fresh.bat), or [run_status.bat](run_status.bat)

See [COMMANDS.md](.github/COMMANDS.md) for complete reference.

---

## Expected Timeline

For **34 Jyotish PDFs** (~5,000-7,000 total pages):

| QA Multiplier | Total QA Pairs | Est. Time |
|---------------|----------------|-----------|
| 2.0x (default) | ~10,000-14,000 | 5-7 days |
| 3.0x | ~15,000-21,000 | 7-10 days |
| 1.5x | ~7,500-10,500 | 4-5 days |

---

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](.github/TROUBLESHOOTING.md)
2. Review [BATCH_PROCESSING_GUIDE.md](.github/BATCH_PROCESSING_GUIDE.md)
3. Check logs: `qa_generation_ollama.log`

---

## License

This project is for educational and research purposes.
