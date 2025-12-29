# Configuration Guide

Complete guide to configuring the QA Generator using config files and environment variables.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Files](#configuration-files)
- [Configuration Options](#configuration-options)
- [Running with Config](#running-with-config)
- [Examples](#examples)
- [Multiple Configurations](#multiple-configurations)

---

## Quick Start

### Option 1: Using config.yaml (Recommended)

1. **Edit `config.yaml`**:
   ```yaml
   model:
     name: "qwen2.5:14b"

   paths:
     input_folder: "c:\\LLM\\tools\\pdf_rag_in_out\\input"
     output_folder: "data\\output_qwen"
   ```

2. **Run**:
   ```bash
   # Windows
   run.bat

   # Linux/Mac
   ./run.sh
   ```

### Option 2: Using .env file

1. **Copy `.env.example` to `.env`**:
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env`**:
   ```env
   MODEL_NAME=qwen2.5:14b
   INPUT_FOLDER=c:\LLM\tools\pdf_rag_in_out\input
   OUTPUT_FOLDER=data\output_qwen
   ```

3. **Run**:
   ```bash
   python scripts/qa_generator.py --config-env .env
   ```

---

## Configuration Files

### config.yaml (Recommended)

**Advantages:**
- ✅ Human-readable
- ✅ Supports comments
- ✅ Hierarchical structure
- ✅ Multi-model presets
- ✅ System prompt customization

**Location:** `c:\LLM\pdf_rag_finetuning\config.yaml`

### .env file

**Advantages:**
- ✅ Simple key=value pairs
- ✅ Easy to version control (with .gitignore)
- ✅ Standard format
- ✅ Good for CI/CD

**Location:** `c:\LLM\pdf_rag_finetuning\.env`

### Priority

If both files exist:
1. **config.yaml** settings take precedence
2. **.env** provides defaults
3. Command-line arguments override both

---

## Configuration Options

### Model Configuration

#### config.yaml
```yaml
model:
  name: "qwen2.5:14b"           # Ollama model name
  base_url: "http://localhost:11434"  # Ollama server
  temperature: 0.3               # 0.0-1.0 (lower = focused)
  max_tokens: 4096              # Maximum response length
```

#### .env
```env
MODEL_NAME=qwen2.5:14b
OLLAMA_BASE_URL=http://localhost:11434
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=4096
```

**Available Models:**
- `qwen2.5:14b` - Best quality (default)
- `llama3.1:8b` - Good quality, faster
- `mistral` - Fast, good quality
- `phi3` - Very fast, testing
- `gemma2` - Fast, very good quality

---

### Processing Configuration

#### config.yaml
```yaml
processing:
  qa_multiplier: 2.0           # QA pairs per page
  target_qa_count: null        # Fixed count (overrides multiplier)
  chunk_size: 4000             # Text chunk size
  chunk_overlap: 400           # Overlap between chunks
  rate_limit_delay: 0.5        # Delay between LLM calls (seconds)
```

#### .env
```env
QA_MULTIPLIER=2.0
TARGET_QA_COUNT=              # Leave empty for multiplier mode
CHUNK_SIZE=4000
CHUNK_OVERLAP=400
RATE_LIMIT_DELAY=0.5
```

**Settings Explained:**

| Setting | Description | Recommended |
|---------|-------------|-------------|
| `qa_multiplier` | QA pairs generated per PDF page | `2.0` (twice page count) |
| `target_qa_count` | Fixed number regardless of pages | `null` (use multiplier) |
| `chunk_size` | Characters per text chunk | `4000` (more context) |
| `chunk_overlap` | Overlap to maintain context | `400` (10% of chunk) |
| `rate_limit_delay` | Pause between LLM calls | `0.5` (moderate) |

---

### Paths Configuration

#### config.yaml
```yaml
paths:
  input_folder: "c:\\LLM\\tools\\pdf_rag_in_out\\input"
  output_folder: "data\\output_qwen"
  log_file: "qa_generation.log"
```

#### .env
```env
INPUT_FOLDER=c:\LLM\tools\pdf_rag_in_out\input
OUTPUT_FOLDER=data\output_qwen
LOG_FILE=qa_generation.log
```

**Path Format:**
- Windows: Use `\\` or `/` in YAML, `\` in .env
- Linux/Mac: Use `/`

---

### Resume Configuration

#### config.yaml
```yaml
resume:
  enabled: true                # Enable auto-resume
  checkpoint_file: "checkpoint.json"
  progress_file: "progress.json"
```

#### .env
```env
RESUME_ENABLED=true
```

---

### Domain Configuration

#### config.yaml
```yaml
domain:
  name: "Jyotish (Vedic Astrology)"
  qa_types:
    - "definition"
    - "concept"
    - "rule"
    - "procedure"
    - "comparison"
    - "example"
    - "interpretation"
    - "checklist"
    - "common_mistake"
  special_instructions: "Preserve ALL Sanskrit terms with diacritical marks"
```

#### .env
```env
DOMAIN_NAME=Jyotish (Vedic Astrology)
DOMAIN_SPECIAL_INSTRUCTIONS=Preserve ALL Sanskrit terms with diacritical marks
```

---

### Logging Configuration

#### config.yaml
```yaml
logging:
  level: "INFO"                # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(levelname)s - %(message)s"
  file_enabled: true
  console_enabled: true
```

**Log Levels:**
- `DEBUG` - Detailed information
- `INFO` - General progress (default)
- `WARNING` - Warning messages only
- `ERROR` - Errors only

---

### System Prompt (config.yaml only)

```yaml
system_prompt: |
  You are an expert in {domain} creating training data.

  Generate high-quality QA pairs with:
  1. Clear questions
  2. Detailed answers (2-4 sentences)
  3. Proper evidence from source

  Use these QA types: {qa_types}
```

**Placeholders:**
- `{domain}` - Replaced with `domain.name`
- `{qa_types}` - Replaced with `domain.qa_types`
- `{difficulties}` - Replaced with difficulty levels

---

## Running with Config

### Using config.yaml

```bash
# Use default config.yaml
run.bat                    # Windows
./run.sh                   # Linux/Mac

# Use specific config file
python scripts/qa_generator.py --config my_config.yaml

# Check status
run_status.bat             # Windows
python scripts/qa_generator.py --config config.yaml --status
```

### Using .env

```bash
# Use .env in current directory
python scripts/qa_generator.py --config-env .env

# Use specific .env file
python scripts/qa_generator.py --config-env production.env
```

### Combining Files

```bash
# Use both (YAML overrides .env)
python scripts/qa_generator.py --config config.yaml --config-env .env
```

### Command-Line Override

```bash
# Override model from command line
python scripts/qa_generator.py --config config.yaml --model llama3.1:8b

# Override multiplier
python scripts/qa_generator.py --config config.yaml --qa-multiplier 3.0
```

**Priority Order:**
1. Command-line arguments (highest)
2. config.yaml
3. .env
4. Defaults (lowest)

---

## Examples

### Example 1: High Quality Dataset (qwen2.5:14b, 3x)

**config.yaml:**
```yaml
model:
  name: "qwen2.5:14b"

processing:
  qa_multiplier: 3.0
  rate_limit_delay: 1.0    # Slower for quality

paths:
  output_folder: "data/output_qwen_3x"
```

**Run:**
```bash
run.bat
```

---

### Example 2: Fast Processing (llama3.1:8b, 1.5x)

**config.yaml:**
```yaml
model:
  name: "llama3.1:8b"

processing:
  qa_multiplier: 1.5
  rate_limit_delay: 0.2    # Faster

paths:
  output_folder: "data/output_llama_fast"
```

**Run:**
```bash
run.bat
```

---

### Example 3: Fixed Count Per Book

**config.yaml:**
```yaml
model:
  name: "qwen2.5:14b"

processing:
  target_qa_count: 500     # Exactly 500 per book
  qa_multiplier: null      # Ignored

paths:
  output_folder: "data/output_fixed_500"
```

---

### Example 4: Different Domains

**Medical Domain (config_medical.yaml):**
```yaml
model:
  name: "qwen2.5:14b"

domain:
  name: "Medical Science"
  qa_types:
    - "diagnosis"
    - "treatment"
    - "symptom"
    - "definition"
  special_instructions: "Preserve all medical terminology and drug names exactly"

paths:
  input_folder: "c:\\PDFs\\medical"
  output_folder: "data/medical_output"
```

**Run:**
```bash
python scripts/qa_generator.py --config config_medical.yaml
```

---

### Example 5: Development vs Production

**config_dev.yaml:**
```yaml
model:
  name: "phi3"             # Fast model for testing

processing:
  target_qa_count: 10      # Just 10 QA pairs for quick test
  rate_limit_delay: 0.1

logging:
  level: "DEBUG"           # Verbose logging
```

**config_prod.yaml:**
```yaml
model:
  name: "qwen2.5:14b"

processing:
  qa_multiplier: 2.0
  rate_limit_delay: 0.5

logging:
  level: "INFO"
```

**Run:**
```bash
# Development
python scripts/qa_generator.py --config config_dev.yaml

# Production
python scripts/qa_generator.py --config config_prod.yaml
```

---

## Multiple Configurations

### Managing Multiple Configs

Create a `configs/` folder:

```
pdf_rag_finetuning/
├── configs/
│   ├── qwen_2x.yaml
│   ├── qwen_3x.yaml
│   ├── llama_fast.yaml
│   ├── medical.yaml
│   └── legal.yaml
├── config.yaml          # Default
└── .env
```

**Run specific config:**
```bash
python scripts/qa_generator.py --config configs/qwen_3x.yaml
```

### Template Configs

**configs/qwen_2x.yaml:**
```yaml
model:
  name: "qwen2.5:14b"
processing:
  qa_multiplier: 2.0
paths:
  output_folder: "data/output_qwen_2x"
```

**configs/qwen_3x.yaml:**
```yaml
model:
  name: "qwen2.5:14b"
processing:
  qa_multiplier: 3.0
paths:
  output_folder: "data/output_qwen_3x"
```

**configs/llama_fast.yaml:**
```yaml
model:
  name: "llama3.1:8b"
processing:
  qa_multiplier: 1.5
  rate_limit_delay: 0.2
paths:
  output_folder: "data/output_llama_fast"
```

---

## Best Practices

### 1. Use Version Control

```bash
# .gitignore
.env
*.log
data/output_*/
```

Keep `.env.example` and `config.yaml` in git.

### 2. Document Custom Configs

Add comments to your config files:

```yaml
model:
  name: "qwen2.5:14b"     # Best quality for production

processing:
  qa_multiplier: 2.0      # Tested optimal value
  rate_limit_delay: 0.5   # Prevents API overload
```

### 3. Test Before Production

```yaml
# config_test.yaml - Quick validation
processing:
  target_qa_count: 5      # Just 5 QA pairs
```

### 4. Environment-Specific Configs

- `config_dev.yaml` - Development settings
- `config_staging.yaml` - Staging environment
- `config_prod.yaml` - Production settings

### 5. Keep Sensitive Data in .env

```env
# .env (not in git)
OLLAMA_BASE_URL=http://private-server:11434
API_KEY=secret_key
```

```yaml
# config.yaml (in git)
model:
  base_url: "${OLLAMA_BASE_URL}"  # Reference .env variable
```

---

## Troubleshooting

### Config File Not Found

```bash
ERROR: Config file not found: config.yaml
```

**Solution:** Create `config.yaml` or specify path:
```bash
python scripts/qa_generator.py --config path/to/config.yaml
```

### Invalid YAML Syntax

```bash
ERROR: Failed to load YAML config
```

**Solution:** Validate YAML syntax:
- Use proper indentation (2 spaces)
- Quote strings with special characters
- Check for missing colons

### Environment Variable Not Loading

**Solution:** Check `.env` format:
```env
# Correct
MODEL_NAME=qwen2.5:14b

# Incorrect (no spaces around =)
MODEL_NAME = qwen2.5:14b
```

---

## Summary

**Quick Commands:**

```bash
# Use config.yaml
run.bat

# Use custom config
python scripts/qa_generator.py --config my_config.yaml

# Use .env
python scripts/qa_generator.py --config-env .env

# Check current config
python scripts/qa_generator.py --config config.yaml --status
```

**Files:**
- `config.yaml` - Main configuration (recommended)
- `.env` - Environment variables (optional)
- `.env.example` - Template for .env
- `run.bat` / `run.sh` - Run with default config
