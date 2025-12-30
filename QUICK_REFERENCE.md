# Quick Reference Card - Optimal Setup

## 🎯 Current Configuration

```yaml
Model: qwen2.5:72b (98/100 quality)
QA Multiplier: 4.0 (4x more questions)
Chunk Size: 3000 (more chunks)
Temperature: 0.2 (focused generation)
Expected Output: 8,000-10,000 QA pairs
```

---

## 🚀 One-Command RunPod Setup

```bash
wget https://raw.githubusercontent.com/ravidsun/pdf_rag_finetuning/pdf_rag_finetuning/feature/runpod-setup/runpod_setup.sh && chmod +x runpod_setup.sh && ./runpod_setup.sh
```

---

## 💻 GPU Requirements

| Model | GPU | VRAM | RunPod Cost/hr |
|-------|-----|------|----------------|
| **qwen2.5:72b** ⭐ | A100 | 48GB | $1.50-2.50 |
| qwen2.5:32b | RTX 4090 | 24GB | $0.50-0.80 |
| mixtral:8x7b | RTX 4090 | 26GB | $0.50-0.80 |

---

## ⚡ Quick Commands

### Start Generation
```bash
cd /workspace/pdf_rag_finetuning
screen -S qa_gen
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:72b --qa-multiplier 4.0
```

### Monitor Progress
```bash
tail -f qa_generation.log    # View logs
watch -n 1 nvidia-smi         # GPU usage
wc -l data/output/*.jsonl    # Count QA pairs
```

### Upload/Download
```bash
# Upload PDFs
scp local/*.pdf root@runpod:/workspace/pdf_rag_finetuning/data/input/

# Download results
scp root@runpod:/workspace/pdf_rag_finetuning/data/output/*.jsonl ./
```

---

## 🎛️ Alternative Models

### Switch to 32B (RTX 4090)
Edit config.yaml:
```yaml
model:
  name: "qwen2.5:32b"
processing:
  qa_multiplier: 3.0
```

### Switch to Llama 3.1:70B
Edit config.yaml:
```yaml
model:
  name: "llama3.1:70b"
processing:
  qa_multiplier: 3.5
```

---

## 📊 Expected Results

| Dataset Size | Time (A100) | Cost | QA Pairs |
|--------------|-------------|------|----------|
| Small (10 PDFs) | 2-4 hours | $3-10 | 2,000-3,000 |
| Medium (50 PDFs) | 10-20 hours | $15-50 | 10,000-15,000 |
| Large (100 PDFs) | 20-40 hours | $30-100 | 20,000-30,000 |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Out of Memory | Use qwen2.5:32b instead |
| Too slow | Use mixtral:8x7b for testing |
| Model not found | `ollama pull qwen2.5:72b` |
| Job interrupted | Re-run same command (auto-resumes) |

---

## 📚 Documentation

- **Full Guide**: [RUNPOD_GUIDE.md](RUNPOD_GUIDE.md)
- **Model Comparison**: [MODEL_COMPARISON.md](MODEL_COMPARISON.md)
- **Setup Summary**: [OPTIMAL_SETUP_SUMMARY.md](OPTIMAL_SETUP_SUMMARY.md)
- **Configuration**: [config.yaml](config.yaml)

---

**Ready to generate!** 🎉
