#!/bin/bash
# RunPod Cleanup Script
# Cleans up single GPU setup to prepare for multi-GPU deployment

set -e

echo "============================================================"
echo "PDF RAG Fine-tuning - Cleanup Script"
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

# Step 1: Stop all Ollama processes
echo "Step 1: Stopping all Ollama processes..."
pkill ollama 2>/dev/null || true
sleep 3

if pgrep -x "ollama" > /dev/null; then
    print_error "Some Ollama processes still running, forcing kill..."
    pkill -9 ollama 2>/dev/null || true
    sleep 2
fi

print_success "All Ollama processes stopped"

# Step 2: Clean up temporary files
echo ""
echo "Step 2: Cleaning up temporary files..."

# Remove checkpoint and progress files
rm -f checkpoint.json progress.json 2>/dev/null || true
print_info "Removed checkpoint files"

# Remove log files
rm -f qa_generation*.log ollama*.log 2>/dev/null || true
print_info "Removed log files"

# Remove temporary GPU input directories (from previous multi-GPU runs)
rm -rf data/temp_input_gpu* 2>/dev/null || true
print_info "Removed temporary GPU directories"

print_success "Cleanup complete"

# Step 3: Check downloaded models
echo ""
echo "Step 3: Checking downloaded models..."
if command -v ollama &> /dev/null; then
    # Start Ollama temporarily to check models
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3

    echo ""
    echo "Currently downloaded models:"
    ollama list
    echo ""

    read -p "Do you want to remove any models? (y/n): " remove_models
    if [[ "$remove_models" == "y" ]]; then
        echo ""
        echo "Available models:"
        ollama list | tail -n +2 | awk '{print $1}'
        echo ""
        read -p "Enter model name to remove (e.g., qwen2.5:72b) or 'skip': " model_to_remove

        if [[ "$model_to_remove" != "skip" && "$model_to_remove" != "" ]]; then
            ollama rm "$model_to_remove"
            print_success "Removed model: $model_to_remove"
        fi
    fi

    pkill ollama 2>/dev/null || true
else
    print_info "Ollama not installed yet"
fi

# Step 4: Display disk usage
echo ""
echo "Step 4: Checking disk usage..."
df -h /workspace 2>/dev/null || df -h .

echo ""
echo "============================================================"
print_success "Cleanup Complete!"
echo "============================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Run multi-GPU setup:"
echo "   cd /workspace/pdf_rag_finetuning"
echo "   chmod +x runpod_multigpu_setup.sh"
echo "   ./runpod_multigpu_setup.sh"
echo ""
echo "2. Upload your PDFs to: /workspace/pdf_rag_finetuning/data/input/"
echo ""
echo "3. Start multi-GPU processing:"
echo "   bash runpod_multigpu_run.sh"
echo ""
echo "============================================================"
