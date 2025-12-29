# Resumable Batch Processing Guide

## Overview

The QA generator now supports **resumable batch processing** with automatic checkpointing. You can pause/stop anytime and resume exactly where you left off!

## Key Features

✅ **Auto-Resume**: Automatically resumes from last checkpoint
✅ **Per-Page Checkpoints**: Saves progress after each 50-page batch
✅ **Per-PDF Tracking**: Tracks which PDFs are completed
✅ **Incremental Saves**: JSONL files update continuously
✅ **Graceful Interruption**: Press Ctrl+C to pause safely
✅ **Status Monitoring**: Check progress anytime

---

## Quick Start

### 1. Start Batch Processing (All PDFs)

```bash
cd c:\LLM\pdf_rag_finetuning
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**What happens:**
- Processes all 34 PDFs sequentially
- Generates 2x QA pairs per page (default)
- Saves progress automatically
- Can be stopped and resumed anytime

---

### 2. Check Progress Status

```bash
python scripts/qa_generator_ollama.py --status -o data/output_qwen
```

**Output shows:**
- Total PDFs and completion percentage
- Which PDFs are completed
- Current checkpoint (if processing)
- Pages processed in current PDF
- QA pairs generated so far

---

### 3. Resume After Interruption

**Just run the same command again:**

```bash
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**The script will:**
- Skip already completed PDFs
- Resume current PDF from last checkpoint
- Continue where it left off

---

### 4. Start Fresh (Clear All Progress)

```bash
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --no-resume
```

This ignores all checkpoints and starts from scratch.

---

## How It Works

### Checkpoint System

**Two levels of checkpoints:**

1. **PDF-Level Progress** (`progress.json`)
   - Tracks which PDFs are fully completed
   - Persists across sessions
   - Prevents re-processing completed books

2. **Page-Level Checkpoint** (`checkpoint.json`)
   - Tracks progress within current PDF
   - Saves after each 50-page batch
   - Allows resume mid-PDF

### File Structure

```
data/output_qwen/
├── checkpoint.json          # Current page-level progress
├── progress.json            # Overall batch progress
├── Book1_qa.jsonl          # Individual book outputs
├── Book2_qa.jsonl
├── ...
└── all_books_combined_qa.jsonl  # Created at end
```

---

## Usage Examples

### Example 1: Process with Custom Multiplier

```bash
# Generate 3x QA pairs per page
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --qa-multiplier 3.0
```

### Example 2: Process Specific Number

```bash
# Fixed 500 QA pairs per book
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --target-qa 500
```

### Example 3: Process Single PDF

```bash
# Process one book only
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input\An Introduction to Jyotish_ A Journey into the World of Jyotish (In Search of Jyotish Book 1)_nodrm.pdf" -o data/output_qwen
```

---

## Interrupting and Resuming

### How to Pause/Stop

**Option 1: Press Ctrl+C**
- Gracefully stops after current chunk
- Saves checkpoint automatically
- Safe to resume

**Option 2: Close Terminal**
- Last checkpoint will be from last batch
- May lose progress from current 50-page batch

### When to Resume

Resume automatically happens when you:
1. Re-run the same command
2. Script detects existing `checkpoint.json` or `progress.json`
3. Continues from last saved point

---

## Monitoring Progress

### Real-Time Logs

Watch the log file:
```bash
tail -f qa_generation_ollama.log
```

Shows:
- Current PDF being processed
- Pages extracted
- Chunks processed
- QA pairs generated
- Checkpoints saved

### Status Command

```bash
python scripts/qa_generator_ollama.py --status -o data/output_qwen
```

**Example Output:**
```
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
  PDF: An_Introduction_to_Jyotish_Book_9.pdf
  Pages Processed: 150/307
  QA Pairs: 284
  Last Updated: 2025-12-29T14:30:45

Completed PDFs:
  ✓ Book1
  ✓ Book2
  ...
============================================================
```

---

## Advanced Options

### Adjust Processing Speed

```bash
# Slower rate (1 second delay between LLM calls)
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --rate-limit 1.0

# Faster rate (0.2 second delay)
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --rate-limit 0.2
```

### Change Chunk Size

```bash
# Larger chunks for more context
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --chunk-size 6000

# Smaller chunks for faster processing
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --chunk-size 3000
```

### Use Different Model

```bash
# Use llama3.1:8b instead
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --model llama3.1:8b
```

---

## Troubleshooting

### Issue: Script doesn't resume

**Solution:**
- Check if `checkpoint.json` or `progress.json` exist in output directory
- Run with `--status` to see current state
- If corrupted, delete checkpoint files and restart

### Issue: Want to restart a specific PDF

**Solution:**
1. Delete the PDF's JSONL file from output directory
2. Remove PDF name from `progress.json`'s `completed_pdfs` list
3. Re-run the command

### Issue: Checkpoint from wrong PDF

**Solution:**
- Delete `checkpoint.json`
- The script will continue with next PDF from `progress.json`

---

## Best Practices

### 1. Use Descriptive Output Directories

```bash
# Good practice
python scripts/qa_generator_ollama.py INPUT -o data/output_qwen_2x_v1
python scripts/qa_generator_ollama.py INPUT -o data/output_qwen_3x_v2
```

### 2. Check Status Before Resuming

```bash
# Always check first
python scripts/qa_generator_ollama.py --status -o data/output_qwen

# Then resume
python scripts/qa_generator_ollama.py INPUT -o data/output_qwen
```

### 3. Keep Logs for Reference

```bash
# Logs auto-save to qa_generation_ollama.log
# Archive them per run:
copy qa_generation_ollama.log logs\run_2025-12-29.log
```

### 4. Monitor System Resources

- Watch CPU/RAM usage
- Ensure Ollama has enough resources
- Adjust `--rate-limit` if system is overloaded

---

## Expected Timeline

For **34 Jyotish PDFs** (~5,000-7,000 total pages):

| QA Multiplier | Total QA Pairs | Est. Time |
|---------------|----------------|-----------|
| 2.0x (default) | ~10,000-14,000 | 5-7 days |
| 3.0x | ~15,000-21,000 | 7-10 days |
| 1.5x | ~7,500-10,500 | 4-5 days |

**Per PDF average:** 4-8 hours (varies by page count)

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `--status` | Check current progress |
| `--no-resume` | Start fresh, ignore checkpoints |
| `--qa-multiplier 3.0` | Generate 3x QA pairs per page |
| `--target-qa 500` | Fixed QA count per book |
| `--rate-limit 1.0` | Delay between LLM calls (seconds) |
| `--chunk-size 6000` | Text chunk size |
| `--model llama3.1:8b` | Use different Ollama model |
| `-o data/output` | Output directory |

---

## Summary

**Start processing:**
```bash
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**Check status:**
```bash
python scripts/qa_generator_ollama.py --status -o data/output_qwen
```

**Stop anytime:** Press `Ctrl+C`

**Resume:** Run the same command again

The script handles everything automatically! 🚀
