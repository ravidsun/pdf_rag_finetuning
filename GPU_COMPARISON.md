# Complete GPU & CPU Comparison Guide

This guide provides a comprehensive comparison of all processing options for your 32 PDFs with different multipliers.

## Executive Summary

**Best Overall Choice: 4x A40 (Multi-GPU) with Spot Pricing**
- **Time**: 5-10 hours for all 32 PDFs
- **Cost**: $18-48
- **QA Pairs**: 19,648 (2.0x) or 39,296 (4.0x)
- **Speedup**: 4x faster than single GPU

---

## Quick Reference Table (32 PDFs)

### 2.0x Multiplier (19,648 QA pairs total)

| Hardware | Time | On-Demand Cost | Spot Cost | Best For |
|----------|------|----------------|-----------|----------|
| **Local CPU** | 320-448 hours (13-18 days) | Free | - | Zero budget |
| **1x RTX 4090** | 32-64 hours (1.3-2.6 days) | $13-38 | $5-15 | Budget |
| **1x A40** | 19-38 hours (0.8-1.6 days) | $11-30 | $4-12 | Good value |
| **1x A100** | 16-32 hours (0.6-1.3 days) | $30-80 | $12-32 | Premium speed |
| **2x A40** | 10-19 hours (0.4-0.8 days) | $22-60 | $9-24 | 2x speedup |
| **4x A40** ⭐ | **5-10 hours** | $44-120 | **$18-48** | **Recommended** |
| **8x A40** | 2.5-5 hours | $88-240 | $35-96 | Maximum speed |

### 4.0x Multiplier (39,296 QA pairs total)

| Hardware | Time | On-Demand Cost | Spot Cost | Best For |
|----------|------|----------------|-----------|----------|
| **Local CPU** | 640-896 hours (26-37 days) | Free | - | Zero budget |
| **1x RTX 4090** | 64-128 hours (2.6-5.3 days) | $26-77 | $10-31 | Budget |
| **1x A40** | 38-77 hours (1.6-3.2 days) | $23-62 | $9-25 | Good value |
| **1x A100** | 32-64 hours (1.3-2.6 days) | $60-159 | $24-64 | Premium speed |
| **2x A40** | 19-38 hours (0.8-1.6 days) | $46-120 | $18-48 | 2x speedup |
| **4x A40** ⭐ | **10-19 hours** | $88-240 | **$35-96** | **Recommended** |
| **8x A40** | 5-10 hours | $176-480 | $70-192 | Maximum speed |

---

## Detailed Hardware Specifications

### Consumer GPUs

#### RTX 3090
- **VRAM**: 24GB
- **Best For**: qwen2.5:14b, budget option
- **Hourly Cost**: $0.30-0.50 (on-demand), $0.12-0.20 (spot)
- **Speed**: ~0.75-1.25 hours per PDF (2.0x)

#### RTX 4090
- **VRAM**: 24GB
- **Best For**: qwen2.5:14b/32b, best consumer value
- **Hourly Cost**: $0.40-0.60 (on-demand), $0.16-0.24 (spot)
- **Speed**: ~0.5-1 hour per PDF (2.0x)

### Professional/Data Center GPUs

#### A40
- **VRAM**: 48GB
- **Best For**: qwen2.5:32b, sweet spot for multi-GPU
- **Hourly Cost**: $0.60-0.80 (on-demand), $0.24-0.32 (spot)
- **Speed**: ~0.6-1.2 hours per PDF (2.0x)

#### A100 40GB
- **VRAM**: 40GB
- **Best For**: qwen2.5:72b, maximum speed
- **Hourly Cost**: $1.89-2.49 (on-demand), $0.76-1.00 (spot)
- **Speed**: ~0.5-1 hour per PDF (2.0x)

#### A100 80GB
- **VRAM**: 80GB
- **Best For**: qwen2.5:72b+, largest models
- **Hourly Cost**: $2.29-2.99 (on-demand), $0.92-1.20 (spot)
- **Speed**: ~0.5-1 hour per PDF (2.0x)

---

## Model-Specific Recommendations

### qwen2.5:7b (Fastest, Budget)
- **Required VRAM**: 8GB
- **Best GPU**: RTX 3090 or RTX 4090
- **Quality**: ⭐⭐⭐ (Good)
- **Speed**: 40% faster than 14b
- **Use Case**: Quick prototyping, tight budget

### qwen2.5:14b (Balanced)
- **Required VRAM**: 16GB
- **Best GPU**: RTX 4090 or A40
- **Quality**: ⭐⭐⭐⭐ (Very Good)
- **Speed**: Standard baseline
- **Use Case**: Production use, good balance

### qwen2.5:32b (High Quality)
- **Required VRAM**: 32GB
- **Best GPU**: A40 (48GB) or A100
- **Quality**: ⭐⭐⭐⭐⭐ (Excellent)
- **Speed**: 30-40% slower than 14b
- **Use Case**: High-quality training data

### qwen2.5:72b (Maximum Quality)
- **Required VRAM**: 48GB+
- **Best GPU**: A100 40GB/80GB
- **Quality**: ⭐⭐⭐⭐⭐ (Outstanding)
- **Speed**: 50-60% slower than 14b
- **Use Case**: Maximum quality, worth the cost

---

## Multi-GPU vs Single GPU

### Single GPU Economics

For **1x A40** processing 32 PDFs with 2.0x multiplier:
```
Time: 30 hours
Hourly Rate: $0.70/hr
Total Cost: 30 × $0.70 = $21
```

### Multi-GPU Economics

For **4x A40** processing same 32 PDFs:
```
Time: 7.5 hours (4x faster)
Hourly Rate: $2.80/hr (4 GPUs × $0.70)
Total Cost: 7.5 × $2.80 = $21

Result: SAME COST, 4X FASTER! ⚡
```

**Key Insight**: Multi-GPU doesn't cost more, it just finishes proportionally faster!

---

## CPU Count Recommendations

### For Single GPU Pod

| Model Size | Recommended vCPUs | RAM |
|------------|-------------------|-----|
| **7b/14b** | 2 vCPUs | 16-24GB |
| **32b** | 2-4 vCPUs | 24-32GB |
| **72b** | 4 vCPUs | 48-64GB |

### For Multi-GPU Pod

| GPU Count | Recommended vCPUs | RAM |
|-----------|-------------------|-----|
| **2 GPUs** | 4 vCPUs (2 per GPU) | 32-48GB |
| **4 GPUs** | 8 vCPUs (2 per GPU) | 64-96GB |
| **8 GPUs** | 16 vCPUs (2 per GPU) | 128-192GB |

**Rule of Thumb**: Allocate **2 vCPUs per GPU** to prevent CPU bottlenecks.

---

## Cost Breakdown by Scenario

### Scenario 1: Budget Priority ($5-15)

**Configuration**: 1x RTX 4090, Spot, qwen2.5:14b, 2.0x multiplier

```
Time: 32-64 hours (~1.3-2.6 days)
Hourly Rate: $0.16-0.24/hr (spot)
Total Cost: $5-15
QA Pairs: 19,648
Cost per QA: $0.0003-0.0008
```

### Scenario 2: Balanced (Recommended) ($18-48)

**Configuration**: 4x A40, Spot, qwen2.5:14b, 2.0x multiplier

```
Time: 5-10 hours (~0.2-0.4 days)
Hourly Rate: $0.96-1.28/hr (spot, 4 GPUs)
Total Cost: $18-48
QA Pairs: 19,648
Cost per QA: $0.0009-0.0024
Speedup: 4x vs Budget
```

### Scenario 3: Maximum Quality ($60-160)

**Configuration**: 4x A100, Spot, qwen2.5:72b, 4.0x multiplier

```
Time: 10-20 hours (~0.4-0.8 days)
Hourly Rate: $3.04-4.00/hr (spot, 4 GPUs)
Total Cost: $60-160
QA Pairs: 39,296
Cost per QA: $0.0015-0.0041
Quality: Maximum (72b model)
```

### Scenario 4: Maximum Speed ($88-240)

**Configuration**: 8x A40, On-Demand, qwen2.5:32b, 2.0x multiplier

```
Time: 2.5-5 hours
Hourly Rate: $4.80-6.40/hr (8 GPUs)
Total Cost: $88-240
QA Pairs: 19,648
Cost per QA: $0.0045-0.0122
Speedup: 8x vs single GPU
Completes: In under 5 hours!
```

---

## Decision Tree

```
START: Need to process 32 PDFs
│
├─ Budget < $20?
│  └─ YES → 1x RTX 4090 Spot ($5-15, 1.3-2.6 days)
│  └─ NO → Continue
│
├─ Need results in < 12 hours?
│  └─ YES → 4x A40 Spot ($18-48, 5-10 hours) ⭐ RECOMMENDED
│  └─ NO → Continue
│
├─ Need results in < 6 hours?
│  └─ YES → 8x A40 On-Demand ($88-240, 2.5-5 hours)
│  └─ NO → Continue
│
├─ Maximum quality needed?
│  └─ YES → 4x A100 + qwen2.5:72b ($60-160, 10-20 hours)
│  └─ NO → 1x A40 Spot ($4-12, 19-38 hours)
```

---

## Spot vs On-Demand Comparison

### Spot Instance Benefits
- ✅ **60-70% cheaper** than on-demand
- ✅ **Automatic resume** from checkpoints if interrupted
- ✅ **Low interruption risk** during off-peak hours
- ✅ **Same hardware** performance

### Spot Instance Risks
- ⚠️ Can be interrupted during peak demand
- ⚠️ May take longer to find availability
- ⚠️ Not guaranteed completion time

### When to Use Spot
- Budget-conscious projects
- Flexible timeline (can wait 1-3 days)
- Off-peak processing (nights/weekends)
- **Our checkpoint system handles interruptions perfectly!**

### When to Use On-Demand
- Critical deadline < 24 hours
- Peak business hours processing
- Guaranteed completion required
- Can't monitor job status

**Recommendation**: **Use Spot** for 32 PDFs. Even if interrupted once, you'll still save money and the checkpoint system makes resume seamless.

---

## Final Recommendations by Use Case

### 1. Student/Researcher (Budget < $20)
**Choice**: 1x RTX 4090 Spot
- Cost: $5-15
- Time: 1.3-2.6 days
- Quality: Very Good

### 2. Professional (Standard Timeline)
**Choice**: 4x A40 Spot ⭐ **RECOMMENDED**
- Cost: $18-48
- Time: 5-10 hours
- Quality: Very Good
- **Best Price/Performance**

### 3. Enterprise (High Quality)
**Choice**: 4x A100 Spot + qwen2.5:72b
- Cost: $60-160
- Time: 10-20 hours
- Quality: Outstanding

### 4. Urgent Deadline (<6 hours)
**Choice**: 8x A40 On-Demand
- Cost: $88-240
- Time: 2.5-5 hours
- Quality: Very Good
- **Fastest Option**

---

## Summary Table: All Configurations (2.0x Multiplier)

| Rank | Configuration | Time | Spot Cost | Best For |
|------|--------------|------|-----------|----------|
| 🥇 | **4x A40 Spot** | 5-10 hrs | **$18-48** | Best overall |
| 🥈 | 1x RTX 4090 Spot | 32-64 hrs | $5-15 | Budget |
| 🥉 | 2x A40 Spot | 10-19 hrs | $9-24 | Good balance |
| 4 | 1x A40 Spot | 19-38 hrs | $4-12 | Single GPU value |
| 5 | 8x A40 Spot | 2.5-5 hrs | $35-96 | Maximum speed |
| 6 | 1x A100 Spot | 16-32 hrs | $12-32 | Premium single |
| 7 | 4x A100 Spot | 4-8 hrs | $48-128 | Premium multi |

**Winner: 4x A40 Spot** offers the best balance of speed, cost, and convenience for 32 PDFs!

---

## Next Steps

1. Review this comparison
2. Choose configuration based on your budget and timeline
3. Follow the appropriate guide:
   - Single GPU: [RUNPOD_GUIDE.md](RUNPOD_GUIDE.md)
   - Multi-GPU: [MULTIGPU_GUIDE.md](MULTIGPU_GUIDE.md)
4. Deploy and start processing!

For questions or issues:
- GitHub Issues: https://github.com/ravidsun/pdf_rag_finetuning/issues
- RunPod Support: https://discord.gg/runpod
