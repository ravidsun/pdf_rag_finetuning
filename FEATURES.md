# Features Documentation

## Overview

This document provides detailed information about all features of the Jyotish QA Dataset Generator.

---

## Table of Contents

1. [Resumable Processing](#resumable-processing)
2. [Automatic QA Calculation](#automatic-qa-calculation)
3. [Checkpoint System](#checkpoint-system)
4. [Progress Tracking](#progress-tracking)
5. [Incremental Saves](#incremental-saves)
6. [Graceful Interruption](#graceful-interruption)
7. [Status Monitoring](#status-monitoring)
8. [Model Selection](#model-selection)
9. [Output Formats](#output-formats)

---

## Resumable Processing

### Description

The script automatically saves progress and resumes from where it left off if interrupted.

### How It Works

**Two-Level Checkpointing:**

1. **PDF-Level Progress** (`progress.json`)
   - Tracks which PDFs are fully completed
   - Persists across all sessions
   - Prevents re-processing finished books

2. **Page-Level Checkpoint** (`checkpoint.json`)
   - Tracks progress within current PDF
   - Saves after each 50-page batch
   - Allows mid-PDF resume

### Usage

```bash
# Start processing
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen

# Stop anytime (Ctrl+C)

# Resume - just run the same command
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

### Files Created

- `checkpoint.json` - Current page-level progress
- `progress.json` - Overall batch progress

---

## Automatic QA Calculation

### Description

Automatically calculates target QA pairs based on PDF page count using a multiplier.

### Default Behavior

- **Multiplier:** 2.0 (2x QA pairs per page)
- **Example:** 100-page PDF → 200 QA pairs target

### Customization

#### Use Different Multiplier
```bash
# 3x QA pairs per page
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --qa-multiplier 3.0

# 1.5x QA pairs per page
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --qa-multiplier 1.5
```

#### Use Fixed Target
```bash
# Always generate 500 QA pairs per book
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --target-qa 500
```

### Calculation Logic

```python
if target_qa_count is None:
    target_qa_count = int(total_pages * qa_multiplier)
```

---

## Checkpoint System

### Description

Saves processing state at multiple points to prevent data loss.

### Checkpoint Frequency

1. **After Each Chunk** - JSONL file updated
2. **After Each 50-Page Batch** - Checkpoint saved
3. **After Each PDF** - Progress file updated

### Checkpoint Structure

```json
{
  "pdf_name": "An_Introduction_to_Jyotish_..._nodrm.pdf",
  "total_pages": 307,
  "pages_processed": 150,
  "qa_pairs_count": 284,
  "last_page_range": [100, 150],
  "timestamp": "2025-12-29T14:30:45"
}
```

### Automatic Cleanup

- Checkpoint cleared when PDF completes
- Checkpoint cleared when target reached
- Only one active checkpoint at a time

---

## Progress Tracking

### Description

Tracks overall batch progress across all PDFs and sessions.

### Progress Structure

```json
{
  "completed_pdfs": ["Book1", "Book2", "Book3"],
  "total_pdfs": 34,
  "completion_percentage": 8.8,
  "timestamp": "2025-12-29T15:00:00"
}
```

### View Progress

```bash
python scripts/qa_generator_ollama.py --status -o data/output_qwen
```

### Progress Display

```
============================================================
CURRENT PROGRESS STATUS
============================================================
Output Directory: data\output_qwen

Batch Progress:
  Total PDFs: 34
  Completed: 3
  Remaining: 31
  Completion: 8.8%

Active Checkpoint:
  PDF: An_Introduction_to_Jyotish_Book_4.pdf
  Pages Processed: 150/307
  QA Pairs: 284
  Last Updated: 2025-12-29T14:30:45

Completed PDFs:
  ✓ Book1
  ✓ Book2
  ✓ Book3
============================================================
```

---

## Incremental Saves

### Description

JSONL output files are updated after every chunk, ensuring no data loss.

### How It Works

1. **Generate QA Pairs** from chunk
2. **Append to in-memory list**
3. **Overwrite JSONL file** with all pairs
4. **Continue to next chunk**

### Benefits

- No data loss if interrupted
- Can inspect output while processing
- Partial results always available

### File Format

```jsonl
{"id": "...", "source": {...}, "question": "...", "answer": "...", ...}
{"id": "...", "source": {...}, "question": "...", "answer": "...", ...}
{"id": "...", "source": {...}, "question": "...", "answer": "...", ...}
```

One JSON object per line.

---

## Graceful Interruption

### Description

Handles user interruption (Ctrl+C) gracefully without data corruption.

### What Happens

1. **User presses Ctrl+C**
2. **Current chunk completes** (if in progress)
3. **Checkpoint saved** automatically
4. **JSONL file saved** with all QA pairs so far
5. **Progress file updated**
6. **Clean exit** with summary

### Output Example

```
⚠️  Process interrupted by user!
Progress saved. Resume by running the same command.
Completed: 3/34 PDFs
💾 Checkpoint saved: Book4.pdf (150/307 pages, 284 QA pairs)
```

### Resume After Interruption

```bash
# Just run the same command
python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
```

---

## Status Monitoring

### Description

Real-time status checking without affecting running processes.

### Status Command

```bash
python scripts/qa_generator_ollama.py --status -o data/output_qwen
```

### Information Shown

- Total PDFs in batch
- Completed PDFs count
- Remaining PDFs count
- Completion percentage
- Active checkpoint details
- List of completed PDFs

### Use Cases

1. **Check progress** while processing runs in background
2. **Verify state** before resuming
3. **Monitor multiple** batch jobs
4. **Generate reports** on processing status

---

## Model Selection

### Description

Support for multiple Ollama models with easy switching.

### Default Model

- **qwen2.5:14b** - Optimized for quality

### Supported Models

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| qwen2.5:14b | 9 GB | Medium | Excellent |
| llama3.1:8b | 4.7 GB | Fast | Very Good |
| mistral | 4.1 GB | Fast | Good |
| phi3 | 2.3 GB | Very Fast | Good |
| gemma2 | 5.4 GB | Fast | Very Good |

### Change Model

```bash
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --model llama3.1:8b
```

### Model Configuration

```python
self.llm = ChatOllama(
    model=model,
    base_url="http://localhost:11434",
    temperature=0.3,
    num_predict=4096
)
```

---

## Output Formats

### Description

Structured JSONL format optimized for fine-tuning and analysis.

### Output Files

1. **Individual Book Files**
   - `Book1_qa.jsonl`
   - `Book2_qa.jsonl`
   - etc.

2. **Combined File**
   - `all_books_combined_qa.jsonl`
   - Created at end of batch

3. **Metadata Files**
   - `checkpoint.json`
   - `progress.json`

### JSONL Entry Structure

```json
{
  "id": "Book1_p10_0_abc123",
  "source": {
    "pdf_name": "Book1.pdf",
    "page_start": 10,
    "page_end": 12,
    "section_title": "Introduction"
  },
  "question": "What is Jyotisha?",
  "answer": "Jyotisha is the Science of Tracking Time...",
  "qa_type": "definition",
  "difficulty": "easy",
  "tags": ["jyotisha", "vedanga"],
  "evidence": ["Jyotisha is the Science..."]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for QA pair |
| `source.pdf_name` | string | Source PDF filename |
| `source.page_start` | int | First page of source text |
| `source.page_end` | int | Last page of source text |
| `source.section_title` | string | Section/chapter title (if detected) |
| `question` | string | Generated question |
| `answer` | string | Generated answer (2-4 sentences) |
| `qa_type` | string | Type: definition, concept, rule, etc. |
| `difficulty` | string | easy, medium, or hard |
| `tags` | array | Topic tags for categorization |
| `evidence` | array | Direct quotes supporting the QA |

### QA Types

- **definition** - Define terms or concepts
- **concept** - Explain abstract principles
- **rule** - Describe rules or combinations
- **procedure** - Step-by-step methods
- **comparison** - Compare/contrast elements
- **example** - Practical applications
- **interpretation** - How to interpret
- **checklist** - Multiple factors to consider
- **common_mistake** - Errors to avoid

---

## Advanced Features

### Rate Limiting

Control LLM call frequency to manage system load:

```bash
# 1 second delay
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --rate-limit 1.0

# 0.2 second delay (faster)
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --rate-limit 0.2
```

### Chunk Size Adjustment

Control context window size:

```bash
# Larger context (6000 chars)
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --chunk-size 6000

# Smaller context (3000 chars)
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --chunk-size 3000
```

### Fresh Start Mode

Ignore all existing progress:

```bash
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --no-resume
```

---

## Performance Optimization

### Automatic Optimizations

1. **Smart Chunking** - Breaks at paragraph/sentence boundaries
2. **Exponential Backoff** - Retries with increasing delays
3. **Section Detection** - Identifies document structure
4. **Error Recovery** - Continues on single-chunk failures

### User-Controlled Optimizations

1. **Rate Limiting** - Prevent system overload
2. **Chunk Size** - Balance context vs speed
3. **Model Selection** - Trade quality for speed
4. **Target QA Count** - Control processing depth

---

## Logging

### Log File

- **Location:** `qa_generation_ollama.log`
- **Format:** Timestamped entries with log levels
- **Rotation:** Appends to existing file

### Log Levels

- **INFO** - Normal progress updates
- **WARNING** - Recoverable errors
- **ERROR** - Serious errors (with stack traces)

### Sample Log Entry

```
2025-12-29 12:15:30,123 - INFO - Processing: Book1.pdf
2025-12-29 12:15:30,124 - INFO - Total Pages: 307
2025-12-29 12:15:30,124 - INFO - Target QA Pairs: 614 (2.0x pages)
2025-12-29 12:15:45,678 - INFO - Created 49 chunks
2025-12-29 12:16:20,345 - INFO -   Generated 4 QA pairs (Total: 4)
2025-12-29 12:17:50,567 - INFO - 💾 Checkpoint saved: Book1.pdf (50/307 pages, 21 QA pairs)
```

---

## Error Handling

### Automatic Retry

- **JSON Parse Errors:** Retries up to 3 times
- **LLM Errors:** Exponential backoff
- **Network Issues:** Automatic reconnection

### Graceful Degradation

- **Failed Chunk:** Skips and continues
- **Failed PDF:** Logs error and moves to next
- **Partial Success:** Saves what was generated

### User Notification

- Errors logged to file
- Critical errors shown in terminal
- Progress preserved despite errors
