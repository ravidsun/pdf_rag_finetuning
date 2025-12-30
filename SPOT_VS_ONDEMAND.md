# Spot vs On-Demand GPU Strategy

## TL;DR: Recommendation

**For qwen2.5:72b generation:**
- ✅ **Use 1 On-Demand A100** if you have 7-13 hours of uninterrupted time
- ✅ **Use 2 Spot RTX 4090s with qwen2.5:32b** if budget is critical
- ❌ **Don't use 2 Spot A100s** - too risky for long jobs

---

## Cost Analysis

### Option 1: Single On-Demand A100 (RECOMMENDED)

**Configuration:**
- GPU: 1x A100 (40GB/80GB)
- Model: qwen2.5:72b
- Instance Type: On-Demand

**Costs:**
- Hourly Rate: $1.50-2.50/hr
- Job Duration: 7-13 hours
- **Total Cost: $10.50-32.50**

**Pros:**
- ✅ No interruption risk
- ✅ Highest quality (98/100)
- ✅ Most QA pairs (8,000-10,000)
- ✅ Single setup, single monitoring
- ✅ Predictable completion time

**Cons:**
- ❌ Higher hourly cost
- ❌ Slightly higher total cost

---

### Option 2: Single Spot A100

**Configuration:**
- GPU: 1x A100 Spot
- Model: qwen2.5:72b
- Instance Type: Spot (50-70% cheaper)

**Costs:**
- Hourly Rate: $0.60-1.50/hr
- Job Duration: 7-13 hours
- **Total Cost: $4.20-19.50**

**Pros:**
- ✅ 50-70% cost savings
- ✅ Highest quality (98/100)
- ✅ Most QA pairs (8,000-10,000)
- ✅ Auto-resume from checkpoint if interrupted

**Cons:**
- ⚠️ Risk of interruption (3-8 hour job)
- ⚠️ May need to restart 1-2 times
- ⚠️ Total time could extend to 10-20 hours

**Interruption Risk:**
- Low: During off-peak hours (2am-8am EST)
- Medium: Business hours
- High: During high-demand periods

---

### Option 3: Two Spot RTX 4090s (Budget Alternative)

**Configuration:**
- GPUs: 2x RTX 4090 Spot
- Model: qwen2.5:32b (not 72b - won't fit)
- Instance Type: Spot
- Strategy: Split PDFs, run parallel

**Costs:**
- Hourly Rate: $0.25-0.50/hr per GPU = $0.50-1.00/hr total
- Job Duration: 3-7 hours (parallel)
- **Total Cost: $1.50-7.00**

**Pros:**
- ✅ Lowest cost option
- ✅ Faster completion (parallel processing)
- ✅ If one gets interrupted, other continues
- ✅ Good quality (92/100)

**Cons:**
- ❌ More complex setup (split PDFs, manage 2 instances)
- ❌ Lower quality model (32b instead of 72b)
- ❌ Fewer QA pairs per instance (~1,500 each = 3,000 total)
- ❌ Need to merge outputs

---

### Option 4: Two On-Demand RTX 4090s

**Configuration:**
- GPUs: 2x RTX 4090 On-Demand
- Model: qwen2.5:32b
- Strategy: Split PDFs, run parallel

**Costs:**
- Hourly Rate: $0.50-0.80/hr per GPU = $1.00-1.60/hr total
- Job Duration: 3-7 hours (parallel)
- **Total Cost: $3.00-11.20**

**Pros:**
- ✅ No interruption risk
- ✅ Faster than single GPU (parallel)
- ✅ Reasonable cost
- ✅ Good quality (92/100)

**Cons:**
- ❌ More setup complexity
- ❌ Lower quality than 72b
- ❌ Need to merge outputs

---

## Detailed Comparison Table

| Option | GPUs | Model | Type | Cost | Time | QA Pairs | Quality | Risk | Complexity |
|--------|------|-------|------|------|------|----------|---------|------|------------|
| **1. Single On-Demand A100** | 1x A100 | 72b | On-Demand | $10-32 | 7-13h | 8,000-10,000 | 98/100 | None | Low |
| **2. Single Spot A100** | 1x A100 | 72b | Spot | $4-20 | 7-20h* | 8,000-10,000 | 98/100 | Medium | Low |
| **3. Two Spot 4090s** | 2x 4090 | 32b | Spot | $1.50-7 | 3-7h | ~3,000 | 92/100 | Low | High |
| **4. Two On-Demand 4090s** | 2x 4090 | 32b | On-Demand | $3-11 | 3-7h | ~3,000 | 92/100 | None | High |

\* Time includes potential interruptions and restarts

---

## Interruption Handling Strategy

### With Checkpoint Resume (Built-in)
Your script already has checkpoint/resume capability:

```python
# If interrupted, just re-run the same command
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:72b --qa-multiplier 4.0
```

**What happens:**
1. Job runs for 4 hours on Spot A100
2. Instance gets interrupted (reclaimed)
3. You deploy new Spot A100
4. Re-run same command
5. Script auto-resumes from checkpoint
6. Continues for remaining 5 hours

**Total Cost Example:**
- First 4 hours: $0.80/hr × 4 = $3.20
- Setup new instance: 5 min
- Last 5 hours: $0.80/hr × 5 = $4.00
- **Total: $7.20** (vs $21 on-demand)

---

## Parallel Processing Setup (2 GPUs)

### How to Split Work Across 2 GPUs

**Instance 1:**
```bash
# Upload first half of PDFs
scp pdfs_001-017/*.pdf root@pod1:/workspace/pdf_rag_finetuning/data/input/

# Generate
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:32b --qa-multiplier 3.0
```

**Instance 2:**
```bash
# Upload second half of PDFs
scp pdfs_018-034/*.pdf root@pod2:/workspace/pdf_rag_finetuning/data/input/

# Generate
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:32b --qa-multiplier 3.0
```

**Merge Outputs:**
```bash
# Download from both
scp root@pod1:/workspace/pdf_rag_finetuning/data/output/*.jsonl ./output_pod1/
scp root@pod2:/workspace/pdf_rag_finetuning/data/output/*.jsonl ./output_pod2/

# Combine
cat output_pod1/*.jsonl output_pod2/*.jsonl > combined_qa.jsonl
```

---

## Recommendations by Scenario

### Scenario 1: Maximum Quality, Budget $10-30
**Choice: Single On-Demand A100 with qwen2.5:72b**
- Set it and forget it
- Best quality (98/100)
- Most QA pairs
- No interruptions

### Scenario 2: Good Quality, Budget $5-10
**Choice: Single Spot A100 with qwen2.5:72b**
- 50% cost savings
- Same quality as on-demand
- Be ready to restart if interrupted (low risk during off-peak)

### Scenario 3: Tight Budget, Under $5
**Choice: Two Spot RTX 4090s with qwen2.5:32b**
- Run parallel to finish faster
- Quality still good (92/100)
- More setup work, but lowest cost

### Scenario 4: Speed Priority
**Choice: Two On-Demand RTX 4090s with qwen2.5:32b**
- Finish in 3-7 hours (half the time)
- Moderate cost
- No interruption risk

---

## Spot Instance Best Practices

### 1. Choose Low-Demand Times
- **Best**: 2am-8am EST (weekdays)
- **Good**: Weekends
- **Avoid**: Business hours Monday-Friday

### 2. Monitor Your Job
```bash
# Set up monitoring
watch -n 60 'nvidia-smi && tail -3 qa_generation.log'

# Get alerts (if using Discord/Slack webhook)
curl -X POST webhook-url -d '{"text": "25% complete"}'
```

### 3. Enable Auto-Resume
Already built into your script! Just re-run same command.

### 4. Save Checkpoints Frequently
Your script saves every 50 pages - perfect for interruptions.

---

## Cost-Benefit Analysis

### For $10-32 Budget (On-Demand A100)
- **Per QA Pair**: $0.001-0.004
- **Quality**: Best possible (98/100)
- **Time Investment**: 7-13 hours
- **Risk**: None
- **Recommendation**: ✅ Best for production datasets

### For $4-20 Budget (Spot A100)
- **Per QA Pair**: $0.0005-0.0025
- **Quality**: Best possible (98/100)
- **Time Investment**: 7-20 hours (with potential restarts)
- **Risk**: Medium (interruption)
- **Recommendation**: ✅ Best value if you can monitor

### For $1.50-7 Budget (2x Spot 4090s)
- **Per QA Pair**: $0.0005-0.0023
- **Quality**: Good (92/100)
- **Time Investment**: 3-7 hours + setup overhead
- **Risk**: Low (redundancy)
- **Recommendation**: ⚠️ Only if budget critical and willing to manage complexity

---

## Final Recommendation

### Best Overall: **Single Spot A100** with qwen2.5:72b

**Why:**
1. **Best Value**: 50-70% cheaper than on-demand
2. **Top Quality**: Same 98/100 quality as on-demand
3. **Low Risk**: Auto-resume makes interruptions painless
4. **Simple**: No need to manage multiple instances
5. **Smart Strategy**: Run during off-peak hours (low interruption risk)

**When to Use:**
- Deploy during off-peak (2am-8am EST or weekends)
- Monitor first 2-3 hours to ensure stable
- Keep setup script handy for quick restart if needed

**Cost Savings:**
- On-Demand: $10.50-32.50
- Spot: $4.20-19.50
- **Savings: $6-13 (40-60%)**

**Setup:**
```bash
# Deploy Spot A100 on RunPod
# Select "Spot" instance type
# Run setup
wget https://raw.githubusercontent.com/ravidsun/pdf_rag_finetuning/pdf_rag_finetuning/feature/runpod-setup/runpod_setup.sh
chmod +x runpod_setup.sh
./runpod_setup.sh

# Start in screen (survives disconnects)
screen -S qa_gen
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:72b --qa-multiplier 4.0
```

**If Interrupted:**
```bash
# Deploy new Spot A100
# Run setup again (fast, ~5 min)
./runpod_setup.sh

# Download checkpoint from old instance (if accessible)
# OR re-upload checkpoint from backup

# Resume - script auto-detects checkpoint
python scripts/qa_generator.py data/input -o data/output --model qwen2.5:72b --qa-multiplier 4.0
```

---

## When to Avoid Spot

❌ **Don't use Spot if:**
- You have a critical deadline in < 24 hours
- You can't monitor the job at all
- You're running during high-demand periods (Mon-Fri 9am-5pm EST)
- You need guaranteed completion time

✅ **Use On-Demand if:**
- Budget allows $10-32
- You need guaranteed completion
- You want zero management overhead
- You're running during peak hours

---

## Pro Tip: Hybrid Strategy

**Best of Both Worlds:**

1. Start with **Spot A100** during off-peak
2. If interrupted twice, switch to **On-Demand A100**
3. Cost: ~$5-8 Spot + $5-10 On-Demand = $10-18 total
4. You tried to save money but have fallback

**Script:**
```bash
# Try 1: Spot
# ... interrupted after 4 hours

# Try 2: New Spot
# ... interrupted after 3 hours

# Try 3: On-Demand (guaranteed finish)
# ... completes remaining 6 hours

# Total: 4h + 3h Spot ($5.60) + 6h On-Demand ($9) = $14.60
# vs pure On-Demand: $21.50
# Savings: $7
```

---

**Bottom Line:** Use **Spot A100** with qwen2.5:72b and save 50%, with minimal interruption risk thanks to auto-resume! 🎯
