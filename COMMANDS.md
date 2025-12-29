# Complete Command Reference

## Table of Contents

- [Basic Commands](#basic-commands)
- [Status and Monitoring](#status-and-monitoring)
- [Advanced Options](#advanced-options)
- [Command Line Arguments](#command-line-arguments)
- [Examples](#examples)

---

## Basic Commands

### Start Batch Processing (All PDFs)

```bash
cd c:\LLM\pdf_rag_finetuning
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**What it does:**
- Processes all 34 PDFs in the input folder
- Generates 2x QA pairs per page (default)
- Auto-saves progress after each 50-page batch
- Can be stopped and resumed anytime

---

### Check Progress Status

```bash
python scripts/qa_generator.py --status -o data/output_qwen
```

**Output shows:**
- Total PDFs and completion percentage
- Which PDFs are completed
- Current checkpoint details
- Pages processed in active PDF
- QA pairs generated so far

---

### Stop Processing

**Press `Ctrl+C` in the terminal**

- Gracefully stops after current chunk
- Saves checkpoint automatically
- Safe to resume later

---

### Resume After Stopping

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**Same command as starting** - automatically resumes from checkpoint

---

### Start Fresh (Clear Progress)

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --no-resume
```

Ignores all checkpoints and starts from scratch

---

## Status and Monitoring

### Check Current Status

```bash
python scripts/qa_generator.py --status -o data/output_qwen
```

### View Real-Time Logs

```bash
# Windows (PowerShell)
Get-Content qa_generation_ollama.log -Wait -Tail 20

# Using tail (if available)
tail -f qa_generation_ollama.log
```

### Check Output Files

```bash
# List generated files
dir data\output_qwen\*.jsonl

# Count QA pairs in a file
python -c "import sys; print(sum(1 for line in open(sys.argv[1])))" data\output_qwen\Book1_qa.jsonl
```

---

## Advanced Options

### Custom QA Multiplier

#### Generate 3x QA pairs per page
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --qa-multiplier 3.0
```

#### Generate 1.5x QA pairs per page
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --qa-multiplier 1.5
```

#### Generate 4x QA pairs per page
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --qa-multiplier 4.0
```

---

### Fixed Target QA Count

#### 500 QA pairs per book
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --target-qa 500
```

#### 1000 QA pairs per book
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --target-qa 1000
```

---

### Process Single PDF

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input\An Introduction to Jyotish_ A Journey into the World of Jyotish (In Search of Jyotish Book 1)_nodrm.pdf" -o data/output_qwen
```

---

### Adjust Processing Speed

#### Slower (1 second delay between calls)
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --rate-limit 1.0
```

#### Faster (0.2 second delay)
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --rate-limit 0.2
```

#### Very slow (2 second delay)
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --rate-limit 2.0
```

---

### Change Chunk Size

#### Larger chunks (6000 chars - more context)
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --chunk-size 6000
```

#### Smaller chunks (3000 chars - faster)
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --chunk-size 3000
```

---

### Use Different Model

#### Use llama3.1:8b
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --model llama3.1:8b
```

#### Use mistral
```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --model mistral
```

---

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `input_path` | string | - | Path to PDF file or folder (required unless --status) |
| `--status` | flag | - | Show current progress and exit |
| `--no-resume` | flag | - | Start fresh, ignore checkpoints |
| `-o`, `--output` | string | `./output` | Output directory for JSONL files |
| `--qa-multiplier` | float | `2.0` | QA pairs per page (ignored if --target-qa set) |
| `--target-qa` | int | `None` | Fixed QA count per book (overrides multiplier) |
| `--chunk-size` | int | `4000` | Text chunk size in characters |
| `--rate-limit` | float | `0.5` | Delay between LLM calls (seconds) |
| `--model` | string | `qwen2.5:14b` | Ollama model to use |

---

## Examples

### Example 1: Standard Batch Processing

```bash
cd c:\LLM\pdf_rag_finetuning
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**Result:** Processes all PDFs with 2x QA pairs per page

---

### Example 2: High-Quality Dataset (3x multiplier)

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen_3x --qa-multiplier 3.0
```

**Result:** Generates ~15,000-21,000 QA pairs across all books

---

### Example 3: Quick Test Run (Single PDF)

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input\An Introduction to Jyotish_ A Journey into the World of Jyotish (In Search of Jyotish Book 1)_nodrm.pdf" -o data/test_output
```

**Result:** Processes one book to test configuration

---

### Example 4: Resource-Constrained System

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen --rate-limit 1.5 --chunk-size 3000
```

**Result:** Slower processing with smaller chunks, easier on system resources

---

### Example 5: Consistent Dataset Size

```bash
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen_fixed --target-qa 300
```

**Result:** Each book gets exactly 300 QA pairs (regardless of page count)

---

### Example 6: Monitor Existing Process

```bash
# Terminal 1: Check status
python scripts/qa_generator.py --status -o data/output_qwen

# Terminal 2: Watch logs
tail -f qa_generation_ollama.log

# Terminal 3: Check output files
dir data\output_qwen\*.jsonl
```

**Result:** Multi-terminal monitoring setup

---

### Example 7: Resume After System Restart

```bash
# After computer restart or terminal close
cd c:\LLM\pdf_rag_finetuning

# Check where you left off
python scripts/qa_generator.py --status -o data/output_qwen

# Resume processing
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

**Result:** Continues from last checkpoint

---

### Example 8: Different Model Comparison

```bash
# Run 1: qwen2.5:14b (default)
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen

# Run 2: llama3.1:8b
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_llama --model llama3.1:8b --no-resume

# Run 3: mistral
python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_mistral --model mistral --no-resume
```

**Result:** Compare QA quality across different models

---

## Quick Reference Table

| Task | Command |
|------|---------|
| **Start batch** | `python scripts/qa_generator.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen` |
| **Check status** | `python scripts/qa_generator.py --status -o data/output_qwen` |
| **Stop** | Press `Ctrl+C` |
| **Resume** | Run the same start command again |
| **Start fresh** | Add `--no-resume` to start command |
| **3x QA pairs** | Add `--qa-multiplier 3.0` |
| **Fixed 500 QA** | Add `--target-qa 500` |
| **Slower speed** | Add `--rate-limit 1.0` |
| **Single PDF** | Replace folder path with PDF file path |
| **Different model** | Add `--model llama3.1:8b` |

---

## Help Command

```bash
python scripts/qa_generator.py --help
```

Shows built-in help with all available options.
