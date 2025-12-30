#!/bin/bash
# RunPod Setup Script for PDF RAG Fine-tuning QA Generator
# This script automates the setup process on RunPod GPU instances

set -e  # Exit on error

echo "============================================================"
echo "PDF RAG Fine-tuning - RunPod Setup Script"
echo "============================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
WORKSPACE_DIR="/workspace/pdf_rag_finetuning"
MODEL_NAME="${MODEL_NAME:-qwen2.5:14b}"
QA_MULTIPLIER="${QA_MULTIPLIER:-2.0}"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Step 1: Update system packages
echo "Step 1: Updating system packages..."
apt-get update -qq && apt-get install -y -qq git wget curl > /dev/null 2>&1
print_success "System packages updated"

# Step 2: Install Ollama
echo ""
echo "Step 2: Installing Ollama..."
if command -v ollama &> /dev/null; then
    print_info "Ollama already installed"
else
    curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1
    print_success "Ollama installed"
fi

# Step 3: Start Ollama service
echo ""
echo "Step 3: Starting Ollama service..."
pkill ollama 2>/dev/null || true
nohup ollama serve > /workspace/ollama.log 2>&1 &
sleep 5

# Verify Ollama is running
if pgrep -x "ollama" > /dev/null; then
    print_success "Ollama service started"
else
    print_error "Failed to start Ollama service"
    exit 1
fi

# Step 4: Install Python dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
pip install -q PyPDF2 pdfplumber pypdf pyyaml python-dotenv tqdm colorama jsonschema pandas numpy Pillow ollama langchain-ollama langchain-core langchain-text-splitters
print_success "Python dependencies installed"

# Step 5: Clone repository (if not already present)
echo ""
echo "Step 5: Setting up project directory..."
if [ -d "$WORKSPACE_DIR" ]; then
    print_info "Project directory already exists"
    cd "$WORKSPACE_DIR"
    git pull origin main 2>/dev/null || print_info "Using existing local files"
else
    cd /workspace
    git clone https://github.com/ravidsun/pdf_rag_finetuning.git
    cd pdf_rag_finetuning
    print_success "Repository cloned"
fi

# Step 6: Create data directories
echo ""
echo "Step 6: Creating data directories..."
mkdir -p data/input data/output
print_success "Data directories created"

# Step 7: Download Ollama model
echo ""
echo "Step 7: Downloading Ollama model ($MODEL_NAME)..."
print_info "This may take a few minutes depending on the model size..."
if ollama list | grep -q "$MODEL_NAME"; then
    print_info "Model $MODEL_NAME already downloaded"
else
    ollama pull "$MODEL_NAME"
    print_success "Model $MODEL_NAME downloaded"
fi

# Step 8: Update config.yaml for RunPod
echo ""
echo "Step 8: Updating configuration for RunPod..."
cat > config.yaml << EOF
# QA Generator Configuration File
# Auto-configured for RunPod

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

model:
  # Ollama model to use
  name: "$MODEL_NAME"

  # Ollama server URL
  base_url: "http://localhost:11434"

  # Model temperature (0.0-1.0, lower = more focused)
  temperature: 0.1

  # Maximum tokens to generate
  max_tokens: 4096

# ============================================================================
# PROCESSING CONFIGURATION
# ============================================================================

processing:
  # Generate this many QA pairs per page (default: 2.0)
  qa_multiplier: $QA_MULTIPLIER

  # Fixed number of QA pairs per book (overrides qa_multiplier if set)
  target_qa_count: null

  # Text chunk size in characters
  chunk_size: 4000

  # Overlap between chunks
  chunk_overlap: 400

  # Delay between LLM calls in seconds (rate limiting)
  rate_limit_delay: 0.5

# ============================================================================
# PATHS CONFIGURATION
# ============================================================================

paths:
  # Input folder containing PDFs
  input_folder: "$WORKSPACE_DIR/data/input"

  # Output folder for generated JSONL files
  output_folder: "$WORKSPACE_DIR/data/output"

  # Log file location
  log_file: "qa_generation.log"

# ============================================================================
# RESUME/CHECKPOINT CONFIGURATION
# ============================================================================

resume:
  # Enable automatic resume from checkpoint
  enabled: true

  # Checkpoint file name
  checkpoint_file: "checkpoint.json"

  # Progress file name
  progress_file: "progress.json"

# ============================================================================
# SYSTEM PROMPT CONFIGURATION
# ============================================================================

system_prompt: |
  You are an expert in {domain} creating high-quality training data for fine-tuning language models.
  Your task is to generate diverse, educational question-answer pairs from the provided text.

  CRITICAL REQUIREMENTS:
  1. Preserve ALL technical terms with their exact formatting
  2. Include proper domain-specific terminology
  3. Create self-contained, educational answers (2-4 sentences)
  4. Extract actual evidence quotes from the source text
  5. Mix difficulty levels and question types
  6. Questions should be specific and educational, not generic

  QA TYPES TO USE:
  {qa_types}

  OUTPUT FORMAT - Return ONLY a valid JSON array (no markdown, no code blocks):
  [
    {{
      "question": "Clear, specific question about the content",
      "answer": "Comprehensive, accurate answer with technical details (2-4 sentences)",
      "qa_type": "one of the types listed above",
      "difficulty": "easy|medium|hard",
      "tags": ["relevant", "topic", "tags"],
      "evidence": ["Exact quote from source supporting this QA"]
    }}
  ]

  DIFFICULTY GUIDELINES:
  - easy: Basic definitions, simple classifications, fundamental terms
  - medium: Relationships between concepts, characteristics
  - hard: Complex combinations, multi-factor analysis, advanced topics

  Generate 3-6 high-quality QA pairs from the provided text. Focus on educational value and accuracy.

# ============================================================================
# DOMAIN CONFIGURATION
# ============================================================================

domain:
  # Domain name for system prompt
  name: "Jyotish (Vedic Astrology)"

  # QA types to generate
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

  # Special instructions for this domain
  special_instructions: "Preserve ALL Sanskrit terms with their exact diacritical marks (ā, ī, ū, ṛ, ṣ, ś, ñ, etc.)"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging:
  # Log level: DEBUG, INFO, WARNING, ERROR
  level: "INFO"

  # Log format
  format: "%(asctime)s - %(levelname)s - %(message)s"

  # Enable file logging
  file_enabled: true

  # Enable console logging
  console_enabled: true
EOF

print_success "Configuration updated for RunPod"

# Step 9: Check GPU availability
echo ""
echo "Step 9: Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    print_success "GPU detected and available"
else
    print_error "No GPU detected - performance will be slower"
fi

# Step 10: Display next steps
echo ""
echo "============================================================"
print_success "RunPod Setup Complete!"
echo "============================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Upload your PDF files to: $WORKSPACE_DIR/data/input/"
echo "   - Use RunPod web interface, or"
echo "   - Use scp from local machine:"
echo "     scp your-file.pdf root@runpod-ip:$WORKSPACE_DIR/data/input/"
echo ""
echo "2. Run the QA generator:"
echo "   cd $WORKSPACE_DIR"
echo "   python scripts/qa_generator.py data/input -o data/output --model $MODEL_NAME --qa-multiplier $QA_MULTIPLIER"
echo ""
echo "3. Or use screen to run in background:"
echo "   screen -S qa_gen"
echo "   python scripts/qa_generator.py data/input -o data/output --model $MODEL_NAME --qa-multiplier $QA_MULTIPLIER"
echo "   # Press Ctrl+A then D to detach"
echo "   # Use 'screen -r qa_gen' to reattach"
echo ""
echo "4. Monitor progress:"
echo "   tail -f qa_generation.log"
echo ""
echo "5. Download results when complete:"
echo "   scp root@runpod-ip:$WORKSPACE_DIR/data/output/*.jsonl /local/path/"
echo ""
echo "GPU Performance Estimate:"
echo "  - Expected speed: ~0.3-0.7 min/chunk (5-10x faster than CPU)"
echo "  - Estimated time for 300 chunks: ~1.5-3.5 hours"
echo ""
echo "============================================================"
