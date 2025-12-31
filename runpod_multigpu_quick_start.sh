#!/bin/bash
# Quick Multi-GPU Start Script for RunPod
# Assumes base setup is already done and models downloaded

set -e

echo "============================================================"
echo "PDF RAG Fine-tuning - Multi-GPU Quick Start"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }

# Configuration
WORKSPACE_DIR="/workspace/pdf_rag_finetuning"
MODEL_NAME="${MODEL_NAME:-qwen2.5:32b}"
QA_MULTIPLIER="${QA_MULTIPLIER:-2.0}"
BASE_PORT=11434
USE_GPUS=2

cd "$WORKSPACE_DIR"

# Step 1: Stop any existing Ollama
echo "Step 1: Stopping existing Ollama processes..."
pkill ollama 2>/dev/null || true
sleep 3
print_success "Cleaned up existing processes"

# Step 2: Start Ollama on both GPUs
echo ""
echo "Step 2: Starting Ollama on 2 GPUs..."

# GPU 0
print_info "Starting Ollama on GPU 0 (port 11434)..."
CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST="0.0.0.0:11434" nohup ollama serve > /workspace/ollama_gpu0.log 2>&1 &
sleep 3

if curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
    print_success "Ollama running on GPU 0"
else
    print_error "Failed to start Ollama on GPU 0"
    exit 1
fi

# GPU 1
print_info "Starting Ollama on GPU 1 (port 11435)..."
CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST="0.0.0.0:11435" nohup ollama serve > /workspace/ollama_gpu1.log 2>&1 &
sleep 3

if curl -s "http://localhost:11435/api/tags" > /dev/null 2>&1; then
    print_success "Ollama running on GPU 1"
else
    print_error "Failed to start Ollama on GPU 1"
    exit 1
fi

# Step 3: Verify models are available
echo ""
echo "Step 3: Verifying models..."

if OLLAMA_HOST="localhost:11434" ollama list | grep -q "$MODEL_NAME"; then
    print_success "Model $MODEL_NAME available on GPU 0"
else
    print_error "Model not found on GPU 0, pulling..."
    OLLAMA_HOST="localhost:11434" ollama pull "$MODEL_NAME"
fi

if OLLAMA_HOST="localhost:11435" ollama list | grep -q "$MODEL_NAME"; then
    print_success "Model $MODEL_NAME available on GPU 1"
else
    print_error "Model not found on GPU 1, pulling..."
    OLLAMA_HOST="localhost:11435" ollama pull "$MODEL_NAME"
fi

# Step 4: Count and distribute PDFs
echo ""
echo "Step 4: Distributing PDFs across GPUs..."

PDF_COUNT=$(ls -1 data/input/*.pdf 2>/dev/null | wc -l)

if [ "$PDF_COUNT" -eq 0 ]; then
    print_error "No PDFs found in data/input/"
    exit 1
fi

print_success "Found $PDF_COUNT PDFs"

# Calculate distribution
PDFS_PER_GPU=$((PDF_COUNT / USE_GPUS))
REMAINDER=$((PDF_COUNT % USE_GPUS))

GPU0_COUNT=$((PDFS_PER_GPU + REMAINDER))
GPU1_COUNT=$PDFS_PER_GPU

print_info "GPU 0 will process: $GPU0_COUNT PDFs"
print_info "GPU 1 will process: $GPU1_COUNT PDFs"

# Create temp directories
rm -rf data/temp_input_gpu* 2>/dev/null || true
mkdir -p data/temp_input_gpu0 data/temp_input_gpu1

# Distribute PDFs
mapfile -t ALL_PDFS < <(ls -1 data/input/*.pdf)

pdf_idx=0
for ((i=0; i<$GPU0_COUNT; i++)); do
    ln -sf "$(realpath "${ALL_PDFS[$pdf_idx]}")" data/temp_input_gpu0/
    pdf_idx=$((pdf_idx + 1))
done

for ((i=0; i<$GPU1_COUNT; i++)); do
    ln -sf "$(realpath "${ALL_PDFS[$pdf_idx]}")" data/temp_input_gpu1/
    pdf_idx=$((pdf_idx + 1))
done

print_success "PDFs distributed"

# Step 5: Start processing on both GPUs
echo ""
echo "Step 5: Starting parallel processing..."

# GPU 0
screen -dmS qa_gen_gpu0 bash -c "
    cd $WORKSPACE_DIR
    export OLLAMA_HOST=localhost:11434
    python scripts/qa_generator.py data/temp_input_gpu0 \
        -o data/output \
        --model $MODEL_NAME \
        --qa-multiplier $QA_MULTIPLIER 2>&1 | tee qa_generation_gpu0.log
    echo 'GPU 0 completed! Press any key to exit.'
    read
"

sleep 2
print_success "Started processing on GPU 0"

# GPU 1
screen -dmS qa_gen_gpu1 bash -c "
    cd $WORKSPACE_DIR
    export OLLAMA_HOST=localhost:11435
    python scripts/qa_generator.py data/temp_input_gpu1 \
        -o data/output \
        --model $MODEL_NAME \
        --qa-multiplier $QA_MULTIPLIER 2>&1 | tee qa_generation_gpu1.log
    echo 'GPU 1 completed! Press any key to exit.'
    read
"

sleep 2
print_success "Started processing on GPU 1"

# Display summary
echo ""
echo "============================================================"
print_success "Multi-GPU Processing Started!"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  QA Multiplier: $QA_MULTIPLIER"
echo "  Total PDFs: $PDF_COUNT"
echo "  GPU 0: $GPU0_COUNT PDFs (port 11434)"
echo "  GPU 1: $GPU1_COUNT PDFs (port 11435)"
echo ""
echo "Monitor Progress:"
echo "  GPU 0: screen -r qa_gen_gpu0"
echo "         tail -f qa_generation_gpu0.log"
echo ""
echo "  GPU 1: screen -r qa_gen_gpu1"
echo "         tail -f qa_generation_gpu1.log"
echo ""
echo "Monitor All GPUs:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "Expected Completion:"
echo "  Time: 19-38 hours (50% faster than single GPU!)"
echo "  QA Pairs: ~19,648 total"
echo "  Cost: $27-53 (on-demand) or $11-21 (spot)"
echo ""
echo "When complete, cleanup temp files:"
echo "  rm -rf data/temp_input_gpu*"
echo ""
echo "============================================================"
