# Troubleshooting Guide

## Table of Contents

- [Common Issues](#common-issues)
- [Checkpoint Problems](#checkpoint-problems)
- [Performance Issues](#performance-issues)
- [Model Issues](#model-issues)
- [Output Issues](#output-issues)
- [System Issues](#system-issues)
- [FAQ](#faq)

---

## Common Issues

### Issue: Script doesn't resume from checkpoint

**Symptoms:**
- Restarts from beginning
- Ignores existing checkpoint
- Re-processes completed PDFs

**Solutions:**

1. **Check output directory path:**
   ```bash
   # Make sure you're using the same output directory
   python scripts/qa_generator_ollama.py --status -o data/output_qwen
   ```

2. **Verify checkpoint files exist:**
   ```bash
   dir data\output_qwen\checkpoint.json
   dir data\output_qwen\progress.json
   ```

3. **Check checkpoint content:**
   ```bash
   python -m json.tool data\output_qwen\checkpoint.json
   python -m json.tool data\output_qwen\progress.json
   ```

4. **If files are corrupted, delete and start fresh:**
   ```bash
   del data\output_qwen\checkpoint.json
   del data\output_qwen\progress.json
   python scripts/qa_generator_ollama.py INPUT -o data/output_qwen
   ```

---

### Issue: "No such file or directory" error

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Solutions:**

1. **Check PDF path exists:**
   ```bash
   dir "c:\LLM\tools\pdf_rag_in_out\input"
   ```

2. **Use absolute paths:**
   ```bash
   # Instead of relative paths
   python scripts/qa_generator_ollama.py "c:\LLM\tools\pdf_rag_in_out\input" -o data/output_qwen
   ```

3. **Check for spaces in path:**
   ```bash
   # Always quote paths with spaces
   python scripts/qa_generator_ollama.py "c:\Path With Spaces\input" -o data/output_qwen
   ```

---

### Issue: Ollama connection failed

**Symptoms:**
```
Failed to initialize Ollama: Connection refused
```

**Solutions:**

1. **Check if Ollama is running:**
   ```bash
   ollama list
   ```

2. **Start Ollama service:**
   ```bash
   # Ollama should auto-start, but if not:
   ollama serve
   ```

3. **Verify model is available:**
   ```bash
   ollama list
   # Should show qwen2.5:14b
   ```

4. **Pull model if missing:**
   ```bash
   ollama pull qwen2.5:14b
   ```

---

### Issue: Out of memory errors

**Symptoms:**
```
MemoryError
Killed
System runs out of RAM
```

**Solutions:**

1. **Reduce chunk size:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --chunk-size 3000
   ```

2. **Increase rate limit (slower processing):**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --rate-limit 1.5
   ```

3. **Use smaller model:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --model llama3.1:8b
   ```

4. **Process one PDF at a time:**
   ```bash
   python scripts/qa_generator_ollama.py "path/to/single.pdf" -o OUTPUT
   ```

---

## Checkpoint Problems

### Issue: Checkpoint from wrong PDF

**Symptoms:**
- Resuming wrong PDF
- Checkpoint PDF doesn't match current batch

**Solution:**

```bash
# Delete checkpoint, keep progress
del data\output_qwen\checkpoint.json

# Continue with next PDF in batch
python scripts/qa_generator_ollama.py INPUT -o data/output_qwen
```

---

### Issue: Want to restart specific PDF

**Symptoms:**
- PDF marked complete but want to regenerate
- Need to redo a specific book

**Solution:**

1. **Delete the PDF's output file:**
   ```bash
   del "data\output_qwen\Book_Name_qa.jsonl"
   ```

2. **Edit progress.json to remove from completed list:**
   ```bash
   # Open data\output_qwen\progress.json
   # Remove "Book_Name" from "completed_pdfs" array
   ```

3. **Resume processing:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o data/output_qwen
   ```

---

### Issue: Corrupt checkpoint file

**Symptoms:**
```
Failed to load checkpoint: Expecting value: line 1 column 1
```

**Solution:**

```bash
# Delete corrupt checkpoint
del data\output_qwen\checkpoint.json

# Resume from progress.json
python scripts/qa_generator_ollama.py INPUT -o data/output_qwen
```

---

## Performance Issues

### Issue: Processing very slow

**Symptoms:**
- Takes more than 5 minutes per chunk
- System is very sluggish

**Solutions:**

1. **Check system resources:**
   ```bash
   # Windows
   taskmgr
   # Check CPU and RAM usage
   ```

2. **Reduce load:**
   ```bash
   # Increase delay between calls
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --rate-limit 1.5

   # Reduce chunk size
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --chunk-size 3000
   ```

3. **Use faster model:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --model llama3.1:8b
   ```

4. **Close other applications**

---

### Issue: LLM responses timeout

**Symptoms:**
```
Generation error (attempt 1): Timeout
```

**Solutions:**

1. **Check Ollama is responsive:**
   ```bash
   ollama run qwen2.5:14b "What is 2+2?"
   ```

2. **Restart Ollama:**
   ```bash
   # Stop Ollama (close terminal where it's running)
   # Restart
   ollama serve
   ```

3. **Increase rate limit:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --rate-limit 2.0
   ```

---

## Model Issues

### Issue: Model not found

**Symptoms:**
```
Error: model 'qwen2.5:14b' not found
```

**Solution:**

```bash
# Pull the model
ollama pull qwen2.5:14b

# Verify it's installed
ollama list
```

---

### Issue: Model produces poor quality QA

**Symptoms:**
- Questions are too generic
- Answers are incomplete
- Sanskrit terms missing

**Solutions:**

1. **Try different model:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --model qwen2.5:14b
   ```

2. **Increase chunk size for more context:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --chunk-size 6000
   ```

3. **Adjust QA multiplier:**
   ```bash
   # Generate fewer, higher quality
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT --qa-multiplier 1.5
   ```

---

## Output Issues

### Issue: JSONL file is empty

**Symptoms:**
- File exists but has 0 bytes
- No QA pairs generated

**Solutions:**

1. **Check if processing actually ran:**
   ```bash
   # Look at logs
   type qa_generation_ollama.log
   ```

2. **Verify PDF has text:**
   ```bash
   # Some PDFs are scanned images without text
   # Check PDF manually
   ```

3. **Check for errors in logs:**
   ```bash
   findstr /i "error" qa_generation_ollama.log
   ```

---

### Issue: Duplicate QA pairs

**Symptoms:**
- Same question appears multiple times
- Same ID in file

**Solution:**

This shouldn't happen due to unique ID generation. If it does:

```bash
# Deduplicate using Python
python -c "
import json
seen = set()
with open('data/output_qwen/Book_qa.jsonl', 'r', encoding='utf-8') as f:
    lines = [line for line in f if line.strip()]
with open('data/output_qwen/Book_qa_dedup.jsonl', 'w', encoding='utf-8') as out:
    for line in lines:
        qa = json.loads(line)
        if qa['id'] not in seen:
            seen.add(qa['id'])
            out.write(line)
"
```

---

### Issue: Missing evidence field

**Symptoms:**
- Some QA pairs have empty evidence array
- Evidence field missing

**This is normal** - The LLM may not always provide evidence. If you need evidence:

1. Increase chunk size for more context
2. Use a better model (qwen2.5:14b)
3. Accept that some QA pairs won't have evidence

---

## System Issues

### Issue: Permission denied

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

1. **Run as administrator** (if on Windows)

2. **Check file permissions:**
   ```bash
   # Make sure you have write access to output directory
   ```

3. **Close files that might be locked:**
   - Close Excel/editors viewing JSONL files
   - Close log viewers

---

### Issue: Disk full

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**

1. **Check disk space:**
   ```bash
   # Windows
   dir c:\
   ```

2. **Clean up old outputs:**
   ```bash
   del data\old_output\*
   ```

3. **Use different output directory:**
   ```bash
   # Use drive with more space
   python scripts/qa_generator_ollama.py INPUT -o d:\output_qwen
   ```

---

### Issue: Script crashes unexpectedly

**Symptoms:**
- No error message
- Sudden termination
- No checkpoint saved

**Solutions:**

1. **Check system logs:**
   ```bash
   # Windows Event Viewer
   eventvwr
   ```

2. **Run with verbose logging:**
   ```bash
   python scripts/qa_generator_ollama.py INPUT -o OUTPUT 2>&1 | tee output.log
   ```

3. **Check Ollama logs:**
   ```bash
   # Ollama logs location varies by system
   ```

4. **Test with single PDF:**
   ```bash
   python scripts/qa_generator_ollama.py "single.pdf" -o test_output
   ```

---

## FAQ

### Q: Can I run multiple instances in parallel?

**A:** Yes, but use different output directories:

```bash
# Terminal 1
python scripts/qa_generator_ollama.py PDF1 -o data/output1

# Terminal 2
python scripts/qa_generator_ollama.py PDF2 -o data/output2
```

---

### Q: How do I restart from beginning?

**A:** Use `--no-resume` flag:

```bash
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --no-resume
```

Or delete checkpoint/progress files:

```bash
del data\output_qwen\checkpoint.json
del data\output_qwen\progress.json
```

---

### Q: Can I change settings mid-processing?

**A:** No. Stop current run, delete checkpoints, start with new settings:

```bash
# Stop current (Ctrl+C)
del data\output_qwen\*.json
python scripts/qa_generator_ollama.py INPUT -o OUTPUT --qa-multiplier 3.0
```

---

### Q: How do I merge multiple output directories?

**A:**

```bash
# Combine all JSONL files
copy data\output1\*_qa.jsonl + data\output2\*_qa.jsonl data\combined\all_qa.jsonl
```

---

### Q: Script says "All PDFs already processed" but I want to reprocess

**A:**

```bash
# Delete progress file
del data\output_qwen\progress.json

# Rerun
python scripts/qa_generator_ollama.py INPUT -o data/output_qwen
```

---

### Q: How to validate JSONL files?

**A:**

```bash
# Check JSON syntax
python -m json.tool data\output_qwen\Book_qa.jsonl > nul

# Count lines
python -c "print(sum(1 for line in open('data/output_qwen/Book_qa.jsonl')))"

# Check required fields
python -c "
import json
with open('data/output_qwen/Book_qa.jsonl') as f:
    for i, line in enumerate(f, 1):
        qa = json.loads(line)
        assert 'id' in qa, f'Line {i}: missing id'
        assert 'question' in qa, f'Line {i}: missing question'
        assert 'answer' in qa, f'Line {i}: missing answer'
print('All entries valid')
"
```

---

### Q: Can I pause and resume on a different computer?

**A:** Yes! Copy these files to the new computer:

1. `data/output_qwen/checkpoint.json`
2. `data/output_qwen/progress.json`
3. `data/output_qwen/*_qa.jsonl` (all JSONL files)

Then run the same command on the new system.

---

### Q: How to skip a problematic PDF?

**A:**

1. Note the PDF filename from status
2. Delete its JSONL file (if exists)
3. Add it to completed list in `progress.json`
4. Resume processing

Or just let it fail and move to next automatically.

---

## Getting Help

If issue persists:

1. **Check logs:** `qa_generation_ollama.log`
2. **Run status:** `--status` command
3. **Test single PDF:** Isolate the problem
4. **Check Ollama:** `ollama list` and test model
5. **Review documentation:** README.md, FEATURES.md

---

## Diagnostic Commands

```bash
# Full system check
ollama list
python --version
python -c "import langchain_ollama; print('OK')"
python scripts/qa_generator_ollama.py --help

# Check specific issue
python scripts/qa_generator_ollama.py --status -o data/output_qwen
type qa_generation_ollama.log
dir data\output_qwen

# Test Ollama connection
ollama run qwen2.5:14b "Test"
```
