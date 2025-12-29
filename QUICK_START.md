# Quick Start Guide

## 3-Step Setup

### Step 1: Install Prerequisites

```bash
# Install Ollama
# Download from: https://ollama.ai

# Pull the model
ollama pull qwen2.5:14b

# Verify installation
ollama list
```

### Step 2: Start Processing

```bash
cd c:\LLM\pdf_rag_finetuning
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

### Step 3: Monitor Progress

```bash
# Check status anytime
python scripts/qa_generator.py --status -o data/output_qwen

# Stop processing
Press Ctrl+C

# Resume processing
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

---

## That's It!

The script will:
- ✅ Process all 34 PDFs automatically
- ✅ Generate 2x QA pairs per page
- ✅ Save progress after each batch
- ✅ Resume automatically if interrupted

---

## Common Commands

```bash
# Status check
python scripts/qa_generator.py --status -o data/output_qwen

# Start/Resume
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen

# Generate 3x QA pairs
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --qa-multiplier 3.0

# Start fresh
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --no-resume
```

---

## Output Location

Your generated files will be in:
```
data/output_qwen/
├── checkpoint.json
├── progress.json
├── Book1_qa.jsonl
├── Book2_qa.jsonl
├── ...
└── all_books_combined_qa.jsonl
```

---

## Expected Time

- **Per PDF:** 4-8 hours
- **All 34 PDFs:** 5-7 days
- **Total QA Pairs:** ~10,000-14,000

---

## Need Help?

1. **Commands:** See [COMMANDS.md](COMMANDS.md)
2. **Features:** See [FEATURES.md](FEATURES.md)
3. **Issues:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Details:** See [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md)
