#!/bin/bash
# Fix Multi-GPU Processing Script
# Run this on RunPod to restart both GPUs properly

set -e

cd /workspace/pdf_rag_finetuning

echo "============================================================"
echo "Multi-GPU Fix and Restart Script"
echo "============================================================"
echo ""

# Step 1: Kill all existing processes
echo "Step 1: Stopping all processes..."
pkill -9 python 2>/dev/null || true
pkill -9 ollama 2>/dev/null || true
sleep 3
echo "✓ All processes stopped"

# Step 2: Start Ollama on both GPUs
echo ""
echo "Step 2: Starting Ollama on both GPUs..."
CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST="0.0.0.0:11434" nohup ollama serve > /workspace/ollama_gpu0.log 2>&1 &
sleep 5
CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST="0.0.0.0:11435" nohup ollama serve > /workspace/ollama_gpu1.log 2>&1 &
sleep 5

# Verify both Ollama instances
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ GPU 0 Ollama running (port 11434)"
else
    echo "✗ GPU 0 Ollama failed"
    exit 1
fi

if curl -s http://localhost:11435/api/tags > /dev/null 2>&1; then
    echo "✓ GPU 1 Ollama running (port 11435)"
else
    echo "✗ GPU 1 Ollama failed"
    exit 1
fi

# Step 3: Check and distribute PDFs if needed
echo ""
echo "Step 3: Checking PDFs..."
GPU0_COUNT=$(ls -1 data/temp_input_gpu0/*.pdf 2>/dev/null | wc -l)
GPU1_COUNT=$(ls -1 data/temp_input_gpu1/*.pdf 2>/dev/null | wc -l)
MAIN_COUNT=$(ls -1 data/input/*.pdf 2>/dev/null | wc -l)

echo "Main input folder: $MAIN_COUNT PDFs"
echo "GPU 0 temp folder: $GPU0_COUNT PDFs"
echo "GPU 1 temp folder: $GPU1_COUNT PDFs"

# If temp folders are empty, distribute PDFs
if [ "$GPU0_COUNT" -eq 0 ] && [ "$GPU1_COUNT" -eq 0 ] && [ "$MAIN_COUNT" -gt 0 ]; then
    echo ""
    echo "Distributing PDFs across GPUs..."

    # Create temp directories
    rm -rf data/temp_input_gpu0 data/temp_input_gpu1 2>/dev/null || true
    mkdir -p data/temp_input_gpu0 data/temp_input_gpu1

    # Calculate distribution
    PDFS_PER_GPU=$((MAIN_COUNT / 2))
    REMAINDER=$((MAIN_COUNT % 2))
    GPU0_TARGET=$((PDFS_PER_GPU + REMAINDER))
    GPU1_TARGET=$PDFS_PER_GPU

    echo "Distributing: GPU 0 = $GPU0_TARGET PDFs, GPU 1 = $GPU1_TARGET PDFs"

    # Get all PDFs and distribute
    mapfile -t ALL_PDFS < <(ls -1 data/input/*.pdf)

    pdf_idx=0
    for ((i=0; i<$GPU0_TARGET; i++)); do
        ln -sf "$(realpath "${ALL_PDFS[$pdf_idx]}")" data/temp_input_gpu0/
        pdf_idx=$((pdf_idx + 1))
    done

    for ((i=0; i<$GPU1_TARGET; i++)); do
        ln -sf "$(realpath "${ALL_PDFS[$pdf_idx]}")" data/temp_input_gpu1/
        pdf_idx=$((pdf_idx + 1))
    done

    GPU0_COUNT=$GPU0_TARGET
    GPU1_COUNT=$GPU1_TARGET
    echo "✓ PDFs distributed"
fi

# Step 4: Start processing on both GPUs
echo ""
echo "Step 4: Starting processing on both GPUs..."

if [ "$GPU0_COUNT" -gt 0 ]; then
    OLLAMA_HOST=localhost:11434 nohup python scripts/qa_generator.py data/temp_input_gpu0 \
        -o data/output \
        --model qwen2.5:32b \
        --qa-multiplier 2.0 > qa_generation_gpu0.log 2>&1 &
    GPU0_PID=$!
    echo "✓ GPU 0 processing started (PID: $GPU0_PID, $GPU0_COUNT PDFs)"
else
    echo "✗ No PDFs for GPU 0"
fi

if [ "$GPU1_COUNT" -gt 0 ]; then
    OLLAMA_HOST=localhost:11435 nohup python scripts/qa_generator.py data/temp_input_gpu1 \
        -o data/output \
        --model qwen2.5:32b \
        --qa-multiplier 2.0 > qa_generation_gpu1.log 2>&1 &
    GPU1_PID=$!
    echo "✓ GPU 1 processing started (PID: $GPU1_PID, $GPU1_COUNT PDFs)"
else
    echo "✗ No PDFs for GPU 1"
fi

# Step 5: Wait and verify GPU utilization
echo ""
echo "Step 5: Waiting 30 seconds for GPU initialization..."
sleep 30

echo ""
echo "============================================================"
echo "GPU Status:"
echo "============================================================"
nvidia-smi

echo ""
echo "============================================================"
echo "✓ Multi-GPU Processing Started!"
echo "============================================================"
echo ""
echo "Monitor Progress:"
echo "  GPU 0 log: tail -f qa_generation_gpu0.log"
echo "  GPU 1 log: tail -f qa_generation_gpu1.log"
echo ""
echo "Check GPU Usage:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "Expected: Both GPUs should show 90-97% utilization"
echo ""
echo "When complete, cleanup temp files:"
echo "  rm -rf data/temp_input_gpu*"
echo ""
echo "============================================================"
