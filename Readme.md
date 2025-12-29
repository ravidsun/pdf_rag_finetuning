# PDF RAG Fine-tuning - Jyotish QA Dataset Generator

Generate high-quality question-answer pairs from Jyotish (Vedic Astrology) PDFs using **qwen2.5:14b** via Ollama.

## Features

✅ **Automatic Resume** - Stop and resume anytime without losing progress
✅ **2x QA Pairs Per Page** - Generates at least 2 QA pairs for every PDF page
✅ **Checkpoint System** - Saves progress after each 50-page batch
✅ **Incremental Saves** - JSONL files update continuously
✅ **Progress Tracking** - Monitor status across sessions
✅ **Graceful Interruption** - Press Ctrl+C to pause safely

---

## Quick Start

### 1. Prerequisites

- **Ollama installed**: https://ollama.ai
- **qwen2.5:14b model** downloaded: `ollama pull qwen2.5:14b`
- **Python dependencies** installed: `pip install -r requirements.txt`

### 2. Start Processing

```bash
cd c:\LLM\pdf_rag_finetuning
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

### 3. Check Progress

```bash
python scripts/qa_generator.py --status -o data/output_qwen
```

### 4. Stop and Resume

- **Stop**: Press `Ctrl+C`
- **Resume**: Run the same command again (auto-resumes)

---

## Documentation

| Document | Description |
|----------|-------------|
| [COMMANDS.md](COMMANDS.md) | Complete command reference |
| [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md) | Detailed batch processing guide |
| [FEATURES.md](FEATURES.md) | Feature descriptions and technical details |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |

---

## Project Structure

```
pdf_rag_finetuning/
├── scripts/
│   └── qa_generator.py      # Main QA generation script
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
│   └── utils/                      # Helper functions
├── BATCH_PROCESSING_GUIDE.md       # Resumable processing guide
├── COMMANDS.md                     # Command reference
├── FEATURES.md                     # Feature documentation
├── TROUBLESHOOTING.md              # Troubleshooting guide
└── README.md                       # This file
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
# Start batch processing
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen

# Check status
python scripts/qa_generator.py --status -o data/output_qwen

# Generate 3x QA pairs per page
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --qa-multiplier 3.0

# Start fresh (ignore checkpoints)
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --no-resume
```

See [COMMANDS.md](COMMANDS.md) for complete reference.

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
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md)
3. Check logs: `qa_generation_ollama.log`

---

## License

This project is for educational and research purposes.
