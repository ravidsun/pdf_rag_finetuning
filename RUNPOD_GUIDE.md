# RunPod Deployment Guide

This guide provides step-by-step instructions for running the PDF RAG Fine-tuning QA Generator on RunPod GPU instances for 5-10x faster processing.

## Quick Start (5 Minutes Setup)

### 1. Deploy RunPod GPU Instance

1. Go to [RunPod.io](https://www.runpod.io/) and sign up/login
2. Click **"Deploy"** → **"GPU Instances"**
3. Choose a GPU:
   - **Recommended**: NVIDIA RTX 4090 (24GB VRAM) - Best price/performance
   - **Alternative**: NVIDIA A40 (48GB) or L40 (48GB)
   - **Budget**: RTX 3090 (24GB)
4. Select template: **"RunPod Pytorch"** or **"RunPod Ubuntu"**
5. Set disk space: **50GB minimum**
6. Click **"Deploy On-Demand"** (or "Deploy Spot" for cheaper rates)

### 2. Connect to Your Pod

Once deployed, click **"Connect"** and choose:
- **SSH** (recommended) - Copy the SSH command
- **Jupyter Lab** - Open in browser
- **VS Code** - Connect via SSH extension

### 3. Run Automated Setup Script

SSH into your pod and run:

```bash
# Download and run the setup script
wget https://raw.githubusercontent.com/ravidsun/pdf_rag_finetuning/feature/runpod-setup/runpod_setup.sh
chmod +x runpod_setup.sh
./runpod_setup.sh
```

**Or manually:**

```bash
# Clone the repository
git clone https://github.com/ravidsun/pdf_rag_finetuning.git
cd pdf_rag_finetuning

# Checkout the RunPod branch
git checkout feature/runpod-setup

# Run the setup script
chmod +x runpod_setup.sh
./runpod_setup.sh
```

The script will automatically:
- Install Ollama and start the service
- Install all Python dependencies
- Download the qwen2.5:14b model (or your preferred model)
- Configure paths for RunPod
- Create data directories
- Verify GPU availability

### 4. Upload Your PDF Files

**Option A: Using SCP (from your local machine)**
```bash
# Upload single file
scp "D:\MyProjects\data\input\your-file.pdf" root@runpod-ip:/workspace/pdf_rag_finetuning/data/input/

# Upload all PDFs
scp "D:\MyProjects\data\input\*.pdf" root@runpod-ip:/workspace/pdf_rag_finetuning/data/input/
```

**Option B: Using RunPod Web Interface**
1. Open Jupyter Lab from RunPod dashboard
2. Navigate to `/workspace/pdf_rag_finetuning/data/input/`
3. Click "Upload" and select your PDF files

**Option C: Using wget/curl (if PDF is hosted online)**
```bash
cd /workspace/pdf_rag_finetuning/data/input/
wget https://example.com/your-file.pdf
```

### 5. Run QA Generation

**Option 1: Run in Foreground (see progress in real-time)**
```bash
cd /workspace/pdf_rag_finetuning
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:14b \
  --qa-multiplier 2.0
```

**Option 2: Run in Background with Screen (recommended for long jobs)**
```bash
cd /workspace/pdf_rag_finetuning

# Start a screen session
screen -S qa_gen

# Run the generator
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:14b \
  --qa-multiplier 2.0

# Detach from screen: Press Ctrl+A then D
# Reattach anytime: screen -r qa_gen
```

### 6. Monitor Progress

**Check real-time progress:**
```bash
tail -f qa_generation.log
```

**Check GPU usage:**
```bash
watch -n 1 nvidia-smi
```

**Count generated QA pairs:**
```bash
wc -l data/output/*.jsonl
```

### 7. Download Results

**From your local machine:**
```bash
scp root@runpod-ip:/workspace/pdf_rag_finetuning/data/output/*.jsonl "D:\MyProjects\data\output\"
```

**Or push to GitHub:**
```bash
cd /workspace/pdf_rag_finetuning
git add data/output/*.jsonl
git commit -m "Add generated QA pairs from RunPod"
git push
```

## Performance Comparison

| Hardware | Speed per Chunk | Total Time (614 QA pairs) | Cost |
|----------|----------------|---------------------------|------|
| Local CPU (your current setup) | ~2.8 min | 10-14 hours | Free |
| RunPod RTX 4090 (GPU) | ~0.3-0.5 min | **1-2 hours** | $0.40-1.20 |
| RunPod A40/L40 (GPU) | ~0.4-0.7 min | **1.5-2.5 hours** | $0.90-2.00 |

**Speedup: 5-10x faster on GPU!**

## Configuration Options

The setup script accepts environment variables for customization:

```bash
# Use a different model
MODEL_NAME=qwen2.5:7b ./runpod_setup.sh

# Change QA multiplier
QA_MULTIPLIER=1.5 ./runpod_setup.sh

# Combine both
MODEL_NAME=qwen2.5:7b QA_MULTIPLIER=1.5 ./runpod_setup.sh
```

## Advanced Usage

### Using a Faster Model (qwen2.5:7b)

For even faster processing with slightly lower quality:

```bash
# Download 7b model
ollama pull qwen2.5:7b

# Run with 7b model
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:7b \
  --qa-multiplier 2.0
```

Expected speedup: ~40% faster than 14b model

### Reduce QA Pairs for Faster Completion

```bash
# Generate 1.5x QA pairs instead of 2.0x
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:14b \
  --qa-multiplier 1.5
```

### Resume from Checkpoint

If your job gets interrupted, it will automatically resume from the checkpoint:

```bash
# Just run the same command again
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:14b \
  --qa-multiplier 2.0
```

The script will detect the checkpoint and continue from where it left off.

## Cost Optimization Tips

1. **Use Spot Instances**: 50-70% cheaper than on-demand, but can be interrupted
2. **Auto-shutdown**: Set up auto-stop in RunPod settings when job completes
3. **Right-size GPU**: RTX 4090 offers best price/performance for this workload
4. **Monitor usage**: Stop the pod immediately when job completes
5. **Use cheaper models**: qwen2.5:7b is faster and cheaper to run

## Troubleshooting

### Ollama Service Not Running
```bash
# Restart Ollama
pkill ollama
nohup ollama serve > /workspace/ollama.log 2>&1 &
sleep 5
```

### Out of Memory Error
```bash
# Use a smaller model
ollama pull qwen2.5:7b
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:7b --qa-multiplier 2.0
```

### GPU Not Being Used
```bash
# Check if Ollama is using GPU
nvidia-smi

# Restart Ollama to ensure GPU detection
pkill ollama
nohup ollama serve > /workspace/ollama.log 2>&1 &
```

### Connection Lost During Processing
No problem! The script saves checkpoints automatically. Just SSH back in and run:
```bash
screen -r qa_gen
# Or start a new run - it will resume from checkpoint
```

## Support

- **RunPod Issues**: [RunPod Discord](https://discord.gg/runpod)
- **Project Issues**: [GitHub Issues](https://github.com/ravidsun/pdf_rag_finetuning/issues)

## Estimated Costs (as of 2024)

| GPU Type | Hourly Rate | Estimated Total Cost |
|----------|-------------|---------------------|
| RTX 4090 | $0.40-0.60/hr | $0.40-1.20 |
| RTX 3090 | $0.30-0.50/hr | $0.45-1.25 |
| A40 | $0.60-0.80/hr | $0.90-2.00 |
| L40 | $0.70-0.90/hr | $1.05-2.25 |

*Spot instances can be 50-70% cheaper*

## Next Steps

After generating your QA pairs on RunPod:

1. Download the JSONL files to your local machine
2. Validate the quality of generated QA pairs
3. Use the data for fine-tuning your language model
4. Don't forget to **stop your RunPod instance** to avoid unnecessary charges!
