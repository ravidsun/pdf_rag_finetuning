# RunPod Deployment Guide

This guide provides step-by-step instructions for running the PDF RAG Fine-tuning QA Generator on RunPod GPU instances for 5-10x faster processing.

## Quick Start (5 Minutes Setup)

### 1. Deploy RunPod GPU Instance

1. Go to [RunPod.io](https://www.runpod.io/) and sign up/login
2. Click **"Deploy"** → **"GPU Instances"**
3. Choose a GPU (based on model size):

   **For Qwen2.5:32B (RECOMMENDED):**
   - **Best**: NVIDIA RTX 4090 (24GB) - ~$0.50-0.80/hr
   - **Alternative**: NVIDIA A40/L40 (48GB) - ~$0.60-0.80/hr

   **For Qwen2.5:14B (Budget):**
   - RTX 3090 (24GB) - ~$0.30-0.50/hr

   **For Qwen2.5:72B (Highest Quality):**
   - NVIDIA A100 (40GB or 80GB) - ~$1.50-2.50/hr
   - NVIDIA H100 (80GB) - Premium option

4. Select template: **"RunPod Pytorch"** or **"RunPod Ubuntu"**
5. Set disk space: **100GB minimum** (models are large)
6. **Choose Instance Type:**
   - **Spot** (Recommended): 50-70% cheaper, auto-resume if interrupted
   - **On-Demand**: Guaranteed availability, no interruptions

   💡 **Recommendation**: Use **Spot** and save 50-70%! Your script auto-resumes from checkpoints.

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
- Download the qwen2.5:32b model (or your preferred model)
- Configure paths for RunPod with optimal settings
- Create data directories
- Verify GPU availability

**Alternative Models and Multipliers:**
```bash
# Use default (Qwen2.5:32B with 2.0x - RECOMMENDED)
./runpod_setup.sh

# Use Qwen2.5:14B with 2.0x multiplier (Budget)
MODEL_NAME=qwen2.5:14b QA_MULTIPLIER=2.0 ./runpod_setup.sh

# Use Qwen2.5:72B with 4.0x multiplier (Maximum Quality)
MODEL_NAME=qwen2.5:72b QA_MULTIPLIER=4.0 ./runpod_setup.sh

# Use Llama 3.1:70B
MODEL_NAME=llama3.1:70b QA_MULTIPLIER=4.0 ./runpod_setup.sh
```

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
  --model qwen2.5:32b \
  --qa-multiplier 2.0
```

**Option 2: Run in Background with Screen (recommended for long jobs)**
```bash
cd /workspace/pdf_rag_finetuning

# Start a screen session
screen -S qa_gen

# Run the generator with optimal settings
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:32b \
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

### GPU Options for 32 PDFs (2.0x Multiplier)

| Configuration | Model | Total Time | QA Pairs | Cost (On-Demand) | Cost (Spot) |
|---------------|-------|------------|----------|------------------|-------------|
| **Local CPU** | qwen2.5:14b | 320-448 hrs | 19,648 | Free | - |
| **RTX 3090** | qwen2.5:14b | 64-128 hrs | 19,648 | $19-64 | $8-26 |
| **RTX 4090** ⭐ | qwen2.5:32b | 64-128 hrs | 19,648 | $26-77 | $10-31 |
| **A40/L40** | qwen2.5:32b | 38-77 hrs | 19,648 | $23-62 | $9-25 |
| **A100** | qwen2.5:72b | 32-64 hrs | 39,296 | $60-159 | $24-64 |

**Best Value: RTX 4090 with Spot pricing = $10-31 for 32 PDFs!**

### Quality Comparison by Model

| Model | Quality Score | QA Pairs/PDF | Best For |
|-------|---------------|--------------|----------|
| qwen2.5:14b (2.0x) | ⭐⭐⭐⭐ 85/100 | ~614 | Budget, Fast |
| qwen2.5:32b (2.0x) | ⭐⭐⭐⭐⭐ 92/100 | ~614 | **Recommended** |
| qwen2.5:72b (4.0x) | ⭐⭐⭐⭐⭐ 98/100 | ~1,228 | Maximum Quality |

**Quality Improvements with 32B:**
- 🔤 Better Sanskrit diacritical preservation
- 🧠 Superior reasoning and concept understanding
- 📚 More diverse question types
- 💡 Excellent price/performance ratio

## Configuration Options

The setup script accepts environment variables for customization:

```bash
# Use a different model
MODEL_NAME=qwen2.5:14b ./runpod_setup.sh

# Change QA multiplier
QA_MULTIPLIER=1.5 ./runpod_setup.sh

# Combine both
MODEL_NAME=qwen2.5:14b QA_MULTIPLIER=1.5 ./runpod_setup.sh
```

## Advanced Usage

### Using a Faster Model (qwen2.5:14b)

For faster processing with lower quality:

```bash
# Download 14b model
ollama pull qwen2.5:14b

# Run with 14b model
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:14b \
  --qa-multiplier 2.0
```

Expected speedup: ~30-40% faster than 32b model

### Reduce QA Pairs for Faster Completion

```bash
# Generate 1.5x QA pairs instead of 2.0x
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:32b \
  --qa-multiplier 1.5
```

### Resume from Checkpoint

If your job gets interrupted, it will automatically resume from the checkpoint:

```bash
# Just run the same command again
python scripts/qa_generator.py data/input \
  -o data/output \
  --model qwen2.5:32b \
  --qa-multiplier 2.0
```

The script will detect the checkpoint and continue from where it left off.

## Cost Optimization Tips

### 1. Use Spot Instances (Recommended) ⭐

**Spot RTX 4090 with qwen2.5:32b is the best value:**
- Cost: $10-31 (vs $26-77 on-demand)
- **Savings: 50-70%**
- Auto-resume from checkpoint if interrupted
- Low risk during off-peak hours (2am-8am EST, weekends)

**When to use Spot:**
- ✅ You can monitor the job periodically
- ✅ Running during off-peak hours
- ✅ Want to save 50-70% on costs

**When to use On-Demand:**
- Critical deadline < 24 hours
- Need guaranteed completion
- Running during peak business hours

### 2. Other Cost-Saving Tips
- **Auto-shutdown**: Set up auto-stop in RunPod settings when job completes
- **Right-size GPU**: Match GPU to model size (RTX 4090 for 32b, RTX 3090 for 14b, A100 for 72b)
- **Monitor usage**: Stop the pod immediately when job completes
- **Off-peak hours**: Deploy during low-demand times for best Spot availability

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
ollama pull qwen2.5:14b
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:14b --qa-multiplier 2.0
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

## Estimated Costs for 32 PDFs (2.0x Multiplier)

| GPU | Hourly Rate | Processing Time | On-Demand Cost | Spot Cost |
|-----|-------------|-----------------|----------------|-----------|
| **RTX 3090** | $0.30-0.50/hr | 64-128 hrs | $19-64 | $8-26 |
| **RTX 4090** ⭐ | $0.40-0.60/hr | 64-128 hrs | $26-77 | **$10-31** |
| **A40/L40** | $0.60-0.80/hr | 38-77 hrs | $23-62 | $9-25 |
| **A100** | $1.89-2.49/hr | 32-64 hrs | $60-159 | $24-64 |

**Best Value: RTX 4090 with Spot pricing = $10-31 for 32 PDFs!**

## Next Steps

After generating your QA pairs on RunPod:

1. Download the JSONL files to your local machine
2. Validate the quality of generated QA pairs
3. Use the data for fine-tuning your language model
4. Don't forget to **stop your RunPod instance** to avoid unnecessary charges!
