#!/bin/bash
# RunPod Multi-GPU Setup Script
# Optimizes QA generation across multiple GPUs

set -e

echo "============================================================"
echo "PDF RAG Fine-tuning - Multi-GPU Setup"
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
MODEL_NAME="${MODEL_NAME:-qwen2.5:14b}"
QA_MULTIPLIER="${QA_MULTIPLIER:-2.0}"
BASE_PORT=11434

# Detect GPUs
echo "Step 1: Detecting GPUs..."
if ! command -v nvidia-smi &> /dev/null; then
    print_error "No NVIDIA GPUs detected!"
    exit 1
fi

GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
print_success "Detected $GPU_COUNT GPU(s)"

if [ "$GPU_COUNT" -eq 0 ]; then
    print_error "No GPUs available!"
    exit 1
fi

# Display GPU information
echo ""
echo "GPU Information:"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader | nl -v 0
echo ""

# Ask user how many GPUs to use
read -p "How many GPUs to use for parallel processing? [1-$GPU_COUNT] (default: $GPU_COUNT): " USE_GPUS
USE_GPUS=${USE_GPUS:-$GPU_COUNT}

if [ "$USE_GPUS" -gt "$GPU_COUNT" ]; then
    print_error "Cannot use $USE_GPUS GPUs, only $GPU_COUNT available"
    USE_GPUS=$GPU_COUNT
fi

print_info "Will use $USE_GPUS GPU(s) for parallel processing"

# Run base setup
echo ""
echo "Step 2: Running base setup..."
if [ -f "$WORKSPACE_DIR/runpod_setup.sh" ]; then
    cd "$WORKSPACE_DIR"
    bash runpod_setup.sh
else
    print_error "runpod_setup.sh not found. Please run base setup first."
    exit 1
fi

# Stop default Ollama service
echo ""
echo "Step 3: Configuring multi-GPU Ollama instances..."
pkill ollama 2>/dev/null || true
sleep 2

# Start Ollama on each GPU
for ((i=0; i<$USE_GPUS; i++)); do
    PORT=$((BASE_PORT + i))
    LOG_FILE="/workspace/ollama_gpu${i}.log"

    print_info "Starting Ollama on GPU $i (port $PORT)..."

    # Set GPU and start Ollama
    CUDA_VISIBLE_DEVICES=$i OLLAMA_HOST="0.0.0.0:$PORT" nohup ollama serve > "$LOG_FILE" 2>&1 &

    sleep 3

    # Verify Ollama started
    if curl -s "http://localhost:$PORT/api/tags" > /dev/null 2>&1; then
        print_success "Ollama running on GPU $i (port $PORT)"
    else
        print_error "Failed to start Ollama on GPU $i"
    fi
done

echo ""
echo "Step 4: Downloading model on all GPU instances..."

# Pull model on each Ollama instance
for ((i=0; i<$USE_GPUS; i++)); do
    PORT=$((BASE_PORT + i))
    print_info "Pulling $MODEL_NAME on GPU $i..."
    OLLAMA_HOST="localhost:$PORT" ollama pull "$MODEL_NAME" &
done

# Wait for all downloads to complete
wait
print_success "Model downloaded on all GPU instances"

# Count PDFs
echo ""
echo "Step 5: Preparing PDF distribution..."
mkdir -p "$WORKSPACE_DIR/data/input" "$WORKSPACE_DIR/data/output"

PDF_COUNT=$(ls -1 "$WORKSPACE_DIR/data/input"/*.pdf 2>/dev/null | wc -l)

if [ "$PDF_COUNT" -eq 0 ]; then
    print_error "No PDFs found in data/input/"
    echo ""
    echo "Please upload PDFs and run the processing script manually:"
    echo "  bash runpod_multigpu_run.sh"
    exit 0
fi

print_success "Found $PDF_COUNT PDF(s)"

# Calculate PDFs per GPU
PDFS_PER_GPU=$((PDF_COUNT / USE_GPUS))
REMAINDER=$((PDF_COUNT % USE_GPUS))

echo ""
echo "Distribution Plan:"
echo "  Total PDFs: $PDF_COUNT"
echo "  GPUs: $USE_GPUS"
echo "  PDFs per GPU: $PDFS_PER_GPU (+ $REMAINDER extra on first GPU)"
echo ""

# Create processing script
cat > "$WORKSPACE_DIR/runpod_multigpu_run.sh" << 'EORUN'
#!/bin/bash
# Multi-GPU Processing Runner

set -e

WORKSPACE_DIR="/workspace/pdf_rag_finetuning"
MODEL_NAME="${MODEL_NAME:-qwen2.5:14b}"
QA_MULTIPLIER="${QA_MULTIPLIER:-2.0}"
BASE_PORT=11434

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }

# Detect running Ollama instances
OLLAMA_COUNT=$(pgrep -c ollama || echo "0")
if [ "$OLLAMA_COUNT" -eq 0 ]; then
    echo "No Ollama instances running. Please run runpod_multigpu_setup.sh first"
    exit 1
fi

USE_GPUS=$OLLAMA_COUNT

cd "$WORKSPACE_DIR"

# Get all PDFs
mapfile -t ALL_PDFS < <(ls -1 data/input/*.pdf 2>/dev/null)
PDF_COUNT=${#ALL_PDFS[@]}

if [ "$PDF_COUNT" -eq 0 ]; then
    echo "No PDFs found in data/input/"
    exit 1
fi

print_info "Processing $PDF_COUNT PDFs across $USE_GPUS GPUs"

# Split PDFs across GPUs
PDFS_PER_GPU=$((PDF_COUNT / USE_GPUS))
REMAINDER=$((PDF_COUNT % USE_GPUS))

# Create temporary directories for each GPU
for ((i=0; i<$USE_GPUS; i++)); do
    mkdir -p "data/temp_input_gpu${i}"
done

# Distribute PDFs
pdf_idx=0
for ((gpu=0; gpu<$USE_GPUS; gpu++)); do
    count=$PDFS_PER_GPU
    if [ $gpu -lt $REMAINDER ]; then
        count=$((count + 1))
    fi

    print_info "GPU $gpu will process $count PDFs"

    for ((j=0; j<$count; j++)); do
        if [ $pdf_idx -lt $PDF_COUNT ]; then
            ln -sf "$(realpath "${ALL_PDFS[$pdf_idx]}")" "data/temp_input_gpu${gpu}/"
            pdf_idx=$((pdf_idx + 1))
        fi
    done
done

# Start processing on each GPU in background
for ((i=0; i<$USE_GPUS; i++)); do
    PORT=$((BASE_PORT + i))

    print_info "Starting processing on GPU $i (port $PORT)..."

    screen -dmS "qa_gen_gpu${i}" bash -c "
        cd $WORKSPACE_DIR
        export OLLAMA_HOST=localhost:$PORT
        python scripts/qa_generator.py data/temp_input_gpu${i} \
            -o data/output \
            --model $MODEL_NAME \
            --qa-multiplier $QA_MULTIPLIER 2>&1 | tee qa_generation_gpu${i}.log
        echo 'GPU $i completed! Press any key to exit.'
        read
    "

    sleep 2
done

print_success "All GPU processes started!"
echo ""
echo "Monitor progress:"
for ((i=0; i<$USE_GPUS; i++)); do
    echo "  GPU $i: screen -r qa_gen_gpu${i}"
    echo "         tail -f qa_generation_gpu${i}.log"
done
echo ""
echo "Monitor all GPUs:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "When all complete, cleanup:"
echo "  bash runpod_multigpu_cleanup.sh"
EORUN

chmod +x "$WORKSPACE_DIR/runpod_multigpu_run.sh"

# Create cleanup script
cat > "$WORKSPACE_DIR/runpod_multigpu_cleanup.sh" << 'EOCLEAN'
#!/bin/bash
# Cleanup temporary directories after multi-GPU processing

WORKSPACE_DIR="/workspace/pdf_rag_finetuning"
cd "$WORKSPACE_DIR"

echo "Cleaning up temporary directories..."

# Remove temp input directories
rm -rf data/temp_input_gpu*

echo "✓ Cleanup complete!"
echo ""
echo "All generated QA pairs are in: data/output/"
EOCLEAN

chmod +x "$WORKSPACE_DIR/runpod_multigpu_cleanup.sh"

# Display summary
echo ""
echo "============================================================"
print_success "Multi-GPU Setup Complete!"
echo "============================================================"
echo ""
echo "Ollama instances running:"
for ((i=0; i<$USE_GPUS; i++)); do
    PORT=$((BASE_PORT + i))
    echo "  GPU $i: http://localhost:$PORT"
done
echo ""
echo "Next Steps:"
echo ""
echo "1. Upload your PDF files to: $WORKSPACE_DIR/data/input/"
echo ""
echo "2. Start parallel processing:"
echo "   cd $WORKSPACE_DIR"
echo "   bash runpod_multigpu_run.sh"
echo ""
echo "3. Monitor progress:"
echo "   watch -n 1 nvidia-smi"
echo ""
echo "4. After completion, cleanup:"
echo "   bash runpod_multigpu_cleanup.sh"
echo ""
echo "Performance Estimate:"
echo "  GPUs: $USE_GPUS"
echo "  Expected speedup: ${USE_GPUS}x faster"
echo "  Est. time (2.0x multiplier): $((20/USE_GPUS))-$((40/USE_GPUS)) hours for 32 PDFs"
echo ""
echo "============================================================"
