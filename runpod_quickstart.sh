#!/bin/bash
# RunPod Quick Start - One-line setup and run

set -e

echo "🚀 RunPod Quick Start for PDF RAG Fine-tuning"
echo ""

# Run setup
bash runpod_setup.sh

echo ""
echo "============================================================"
echo "📁 Waiting for PDF files..."
echo "============================================================"
echo ""
echo "Please upload your PDF files to: /workspace/pdf_rag_finetuning/data/input/"
echo ""
echo "Methods:"
echo "  1. Use RunPod web interface (Jupyter Lab)"
echo "  2. Use SCP: scp your-file.pdf root@runpod-ip:/workspace/pdf_rag_finetuning/data/input/"
echo "  3. Use wget: cd /workspace/pdf_rag_finetuning/data/input/ && wget <url>"
echo ""
read -p "Press ENTER when you've uploaded your PDF files..."

# Check if PDFs exist
PDF_COUNT=$(ls -1 /workspace/pdf_rag_finetuning/data/input/*.pdf 2>/dev/null | wc -l)

if [ "$PDF_COUNT" -eq 0 ]; then
    echo "❌ No PDF files found in data/input/"
    echo "Please upload PDF files and run this script again."
    exit 1
fi

echo ""
echo "✓ Found $PDF_COUNT PDF file(s)"
echo ""

# Ask user for preferences
echo "Select model:"
echo "  1. qwen2.5:14b (recommended - balanced speed/quality)"
echo "  2. qwen2.5:7b (faster, slightly lower quality)"
echo "  3. qwen2.5:32b (highest quality, slower)"
read -p "Enter choice [1-3] (default: 1): " MODEL_CHOICE

case $MODEL_CHOICE in
    2)
        MODEL="qwen2.5:7b"
        echo "Downloading qwen2.5:7b model..."
        ollama pull qwen2.5:7b
        ;;
    3)
        MODEL="qwen2.5:32b"
        echo "Downloading qwen2.5:32b model..."
        ollama pull qwen2.5:32b
        ;;
    *)
        MODEL="qwen2.5:14b"
        ;;
esac

echo ""
read -p "QA multiplier (default: 2.0): " QA_MULT
QA_MULT=${QA_MULT:-2.0}

echo ""
echo "============================================================"
echo "🎬 Starting QA Generation"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  - Model: $MODEL"
echo "  - QA Multiplier: $QA_MULT"
echo "  - PDF Files: $PDF_COUNT"
echo ""
read -p "Start processing? [Y/n]: " CONFIRM

if [[ $CONFIRM =~ ^[Nn]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Starting in screen session 'qa_gen'..."
echo "  - Detach: Ctrl+A then D"
echo "  - Reattach: screen -r qa_gen"
echo "  - Monitor: tail -f qa_generation.log"
echo ""
sleep 3

# Start in screen
cd /workspace/pdf_rag_finetuning
screen -dmS qa_gen bash -c "python scripts/qa_generator.py data/input -o data/output --model $MODEL --qa-multiplier $QA_MULT; echo 'Job completed! Press any key to exit.'; read"

# Attach to screen
screen -r qa_gen
