# Multi-GPU Optimization Guide for RunPod

This guide shows you how to leverage multiple GPUs on RunPod to process your 32 PDFs significantly faster through parallel processing.

## Performance Comparison

### Single GPU vs Multi-GPU (32 PDFs, 2.0x Multiplier)

| Configuration | Processing Time | Cost (A40) | Speedup |
|---------------|----------------|------------|---------|
| **1x A40** | 19-38 hours (0.8-1.6 days) | $11-30 | 1x baseline |
| **2x A40** | **10-19 hours** (0.4-0.8 days) | $22-60 | **2x faster** |
| **4x A40** | **5-10 hours** (0.2-0.4 days) | $44-120 | **4x faster** |
| **8x A40** | **2.5-5 hours** | $88-240 | **8x faster** |

### Cost Per Hour vs Total Cost

While hourly costs increase linearly, **total costs remain similar** because processing finishes faster:

```
1 GPU × 30 hours × $0.70/hr = $21
2 GPUs × 15 hours × $0.70/hr = $21 (same cost, 2x faster!)
4 GPUs × 7.5 hours × $0.70/hr = $21 (same cost, 4x faster!)
```

**Key Insight**: Multi-GPU doesn't cost more, it just finishes faster!

## Two Multi-GPU Strategies

### Strategy 1: Multiple GPUs on One Pod (Recommended)

**How it works:**
- Deploy single pod with 2-8 GPUs
- Run multiple Ollama instances (one per GPU)
- Distribute PDFs across GPUs automatically

**Pros:**
✅ Automatic PDF distribution
✅ Shared storage (no file transfers)
✅ Single pod management
✅ Cost-efficient

**Cons:**
❌ Limited GPU combinations available
❌ All GPUs must be same type

**Best for:**
- 8+ PDFs
- Want simplicity
- Need fastest processing

### Strategy 2: Multiple Separate Pods

**How it works:**
- Deploy 2-4 separate pods with 1 GPU each
- Manually split PDFs across pods
- Download results from each pod

**Pros:**
✅ More flexible GPU selection
✅ Can mix GPU types
✅ Better spot instance availability

**Cons:**
❌ Manual PDF distribution required
❌ Multiple pod management
❌ Need to download from each pod separately

**Best for:**
- Spot instance availability issues
- Want different GPU types
- Need maximum flexibility

---

## Method 1: Multiple GPUs on Single Pod (Automated)

### Step 1: Deploy Multi-GPU Pod on RunPod

1. Go to RunPod → **Deploy**
2. **Select GPU Configuration:**
   - For 32 PDFs: **4x A40** (recommended)
   - Budget: **2x RTX 4090**
   - Premium: **4x A100**

3. **Configure Pod:**
   - vCPUs: 8+ (2 per GPU minimum)
   - RAM: 64GB+ for 4 GPUs
   - Disk: 100GB+
   - Template: **RunPod Pytorch**

4. Click **Deploy**

### Step 2: Run Automated Setup

SSH into your pod and run:

```bash
# Clone repository
git clone https://github.com/ravidsun/pdf_rag_finetuning.git
cd pdf_rag_finetuning
git checkout feature/runpod-setup

# Run multi-GPU setup
chmod +x runpod_multigpu_setup.sh
./runpod_multigpu_setup.sh
```

The script will:
- Detect all available GPUs
- Start separate Ollama instance on each GPU
- Download model on each GPU
- Prepare for parallel processing

### Step 3: Upload PDFs

```bash
# From your local machine
scp "D:\MyProjects\data\input\*.pdf" root@runpod-ip:/workspace/pdf_rag_finetuning/data/input/
```

Or use RunPod web interface (Jupyter Lab).

### Step 4: Start Parallel Processing

```bash
cd /workspace/pdf_rag_finetuning

# This will automatically distribute PDFs across GPUs
bash runpod_multigpu_run.sh
```

The script will:
- Detect number of GPUs
- Split 32 PDFs evenly (e.g., 8 PDFs per GPU on 4 GPUs)
- Start parallel processing on each GPU
- Run each in a separate screen session

### Step 5: Monitor Progress

**Monitor all GPUs:**
```bash
watch -n 1 nvidia-smi
```

**Monitor individual GPU logs:**
```bash
# GPU 0
tail -f qa_generation_gpu0.log

# GPU 1
tail -f qa_generation_gpu1.log

# etc.
```

**Attach to specific GPU screen:**
```bash
# View GPU 0 progress
screen -r qa_gen_gpu0

# Detach: Ctrl+A then D
```

**Check completion status:**
```bash
# Count generated QA pairs
wc -l data/output/*.jsonl
```

### Step 6: Download Results

After all GPUs complete:

```bash
# Cleanup temporary files
bash runpod_multigpu_cleanup.sh

# Download results (from local machine)
scp root@runpod-ip:/workspace/pdf_rag_finetuning/data/output/*.jsonl "D:\MyProjects\data\output\"
```

---

## Method 2: Multiple Separate Pods (Manual)

### Step 1: Split PDFs Locally

Split your 32 PDFs into groups:
```
Batch 1: PDFs 1-8   → Pod 1
Batch 2: PDFs 9-16  → Pod 2
Batch 3: PDFs 17-24 → Pod 3
Batch 4: PDFs 25-32 → Pod 4
```

### Step 2: Deploy Multiple Pods

Deploy 4 separate single-GPU pods:
- Each with 1x A40 or RTX 4090
- Use spot instances for cost savings

### Step 3: Setup Each Pod

On each pod:

```bash
# Run standard setup
git clone https://github.com/ravidsun/pdf_rag_finetuning.git
cd pdf_rag_finetuning
git checkout feature/runpod-setup
./runpod_setup.sh
```

### Step 4: Upload Different PDFs to Each Pod

```bash
# Pod 1 - Upload PDFs 1-8
scp pdf1.pdf pdf2.pdf ... pdf8.pdf root@pod1-ip:/workspace/pdf_rag_finetuning/data/input/

# Pod 2 - Upload PDFs 9-16
scp pdf9.pdf pdf10.pdf ... pdf16.pdf root@pod2-ip:/workspace/pdf_rag_finetuning/data/input/

# etc.
```

### Step 5: Start Processing on All Pods

SSH into each pod and start:

```bash
screen -S qa_gen
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:14b --qa-multiplier 2.0
# Ctrl+A then D to detach
```

### Step 6: Download Results from All Pods

```bash
# Download from each pod
scp root@pod1-ip:/workspace/pdf_rag_finetuning/data/output/*.jsonl batch1/
scp root@pod2-ip:/workspace/pdf_rag_finetuning/data/output/*.jsonl batch2/
scp root@pod3-ip:/workspace/pdf_rag_finetuning/data/output/*.jsonl batch3/
scp root@pod4-ip:/workspace/pdf_rag_finetuning/data/output/*.jsonl batch4/
```

---

## Cost Comparison: Single Pod vs Multiple Pods

### 4x GPUs on Single Pod (Method 1)

| Config | Time | On-Demand Cost | Spot Cost |
|--------|------|----------------|-----------|
| **4x A40** | 5-10 hours | $44-120 | $18-48 |
| **4x RTX 4090** | 8-16 hours | $52-152 | $21-61 |
| **4x A100** | 4-8 hours | $240-640 | $96-256 |

### 4 Separate Pods (Method 2)

| Config | Time | On-Demand Cost | Spot Cost |
|--------|------|----------------|-----------|
| **4x A40** (separate) | 5-10 hours | $44-120 | $18-48 |
| **4x RTX 4090** (separate) | 8-16 hours | $52-152 | $21-61 |
| **4x A100** (separate) | 4-8 hours | $240-640 | $96-256 |

**Total costs are the same!** Choose based on convenience.

---

## GPU Recommendations by Budget

### Budget: ~$20-30
- **2x RTX 4090** (single pod) - Spot instance
- **Time**: 16-32 hours (~1-1.3 days)
- **2x speedup**

### Mid-Range: ~$40-60
- **4x A40** (single pod) - Spot instance
- **Time**: 5-10 hours (~0.2-0.4 days)
- **4x speedup** ⭐ **Recommended**

### Premium: ~$100-150
- **8x A40** (single pod) - Spot instance
- **Time**: 2.5-5 hours
- **8x speedup**

### Maximum Speed: ~$100-250
- **4x A100** (single pod) - Spot instance
- **Time**: 4-8 hours
- **Fastest option**

---

## Troubleshooting Multi-GPU Setup

### Ollama Not Starting on All GPUs

```bash
# Check which GPUs have Ollama running
ps aux | grep ollama

# Manually start on specific GPU
CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST="0.0.0.0:11435" ollama serve &
```

### GPUs Not Being Utilized

```bash
# Verify GPU assignment
nvidia-smi

# Check Ollama is using GPU
curl http://localhost:11434/api/tags  # GPU 0
curl http://localhost:11435/api/tags  # GPU 1
```

### Uneven PDF Distribution

The script automatically balances PDFs across GPUs. If manual adjustment needed:

```bash
# Move PDFs between temp directories
mv data/temp_input_gpu0/some.pdf data/temp_input_gpu1/
```

### Out of Memory on One GPU

```bash
# Reduce PDFs on that GPU
# Or use smaller model: qwen2.5:7b
```

---

## Advanced: Mixed GPU Types

You can use different GPU types on separate pods:

```
Pod 1: 1x A100 (fastest) → 12 PDFs
Pod 2: 1x A40  → 10 PDFs
Pod 3: 1x RTX 4090 → 10 PDFs
```

This maximizes speed while managing costs.

---

## Summary

**For 32 PDFs with 2.0x multiplier:**

| Method | Time | Cost | Complexity | Best For |
|--------|------|------|------------|----------|
| **1 GPU** | 19-38 hours | $11-30 | ⭐ Simple | Budget/Learning |
| **2 GPUs (single pod)** | 10-19 hours | $22-60 | ⭐⭐ Easy | Good balance |
| **4 GPUs (single pod)** | 5-10 hours | $44-120 | ⭐⭐ Easy | **Recommended** |
| **8 GPUs (single pod)** | 2.5-5 hours | $88-240 | ⭐⭐⭐ Moderate | Maximum speed |
| **4 Separate pods** | 5-10 hours | $44-120 | ⭐⭐⭐⭐ Complex | Flexibility |

**My recommendation: 4x A40 on single pod with spot pricing**
- Cost: ~$18-48
- Time: ~5-10 hours (completes in half a day!)
- Easy setup with automated script
- Best price/performance ratio
