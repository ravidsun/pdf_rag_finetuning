# Ollama Models Guide for Jyotish QA Generation

## Quick Reference

### Recommended Models (Your System: 15.6 GB RAM)

| Model | Command | Size | RAM Needed | Quality | Speed |
|-------|---------|------|------------|---------|-------|
| ✅ **qwen2.5:14b** (Best) | `ollama pull qwen2.5:14b` | 9GB | 12GB | ⭐⭐⭐⭐⭐ | Medium |
| ✅ **llama3.1:8b** (Fast) | `ollama pull llama3.1:8b` | 4.7GB | 6GB | ⭐⭐⭐⭐ | Fast |
| ✅ **mistral:7b** | `ollama pull mistral:7b` | 4.1GB | 6GB | ⭐⭐⭐ | Fast |
| ❌ **qwen2.5:32b** | Too large for your RAM | 19GB | 24GB | ⭐⭐⭐⭐⭐ | Slow |
| ❌ **llama3.1:70b** | Too large for your RAM | 40GB | 48GB | ⭐⭐⭐⭐⭐ | Very Slow |

## Using Different Models

### Method 1: Command Line
```bash
# Use qwen2.5:14b (recommended)
python scripts/qa_generator_ollama.py "C:\LLM\tools\pdf_rag_in_out\input" -o ./output --model qwen2.5:14b

# Use llama3.1:8b (faster)
python scripts/qa_generator_ollama.py "C:\LLM\tools\pdf_rag_in_out\input" -o ./output --model llama3.1:8b

# Use mistral
python scripts/qa_generator_ollama.py "C:\LLM\tools\pdf_rag_in_out\input" -o ./output --model mistral:7b
```

### Method 2: Test Individual Models

```bash
# Pull multiple models for comparison
ollama pull qwen2.5:14b
ollama pull llama3.1:8b
ollama pull mistral:7b

# Test each on a single PDF
python scripts/qa_generator_ollama.py "path/to/single.pdf" -o ./output_qwen --model qwen2.5:14b --target-qa 10
python scripts/qa_generator_ollama.py "path/to/single.pdf" -o ./output_llama --model llama3.1:8b --target-qa 10
python scripts/qa_generator_ollama.py "path/to/single.pdf" -o ./output_mistral --model mistral:7b --target-qa 10

# Compare the outputs!
```

## Why Qwen2.5 14B is Best for Jyotish

1. **Multilingual Excellence**: Better at preserving Sanskrit diacriticals (ā, ī, ū, ṛ, ṣ, ś, ñ)
2. **Technical Understanding**: Strong with specialized domain knowledge
3. **Reasoning**: Excellent at understanding complex Jyotish concepts (yogas, karaka relationships)
4. **Answer Quality**: Generates coherent, educational 2-4 sentence answers
5. **Evidence Extraction**: Good at finding relevant quotes from source text

## Sample Output Comparison

### Qwen2.5 14B (Best Quality)
```json
{
  "question": "What is the significance of the 2nd house from each Graha in determining specific aspects of family life?",
  "answer": "The 2nd house from each Graha acts as a tertiary Kāraka for specific family matters. For example, the 2nd from Sūrya indicates the right eye, from Candra the left eye, from Budha speech, from Bṛhaspati wealth (Dhana), from Śukra family comforts, and from Śani sorrow or poverty in the family. This system allows astrologers to assess different dimensions of family life through multiple reference points.",
  "qa_type": "concept",
  "difficulty": "medium"
}
```

### Llama 3.1 8B (Good Quality, Faster)
```json
{
  "question": "What does the 2nd house from Śani indicate in Jyotish?",
  "answer": "The 2nd house from Śani indicates sorrow in the family or poverty. This is because Śani represents hardship and limitations, so the 2nd from it reflects these qualities in family matters.",
  "qa_type": "definition",
  "difficulty": "easy"
}
```

### Mistral 7B (Basic Quality)
```json
{
  "question": "What are the different Kārakas for the 2nd house?",
  "answer": "Various Grahas act as Kārakas for different aspects related to the 2nd house, including eyes, speech, wealth, and family matters.",
  "qa_type": "definition",
  "difficulty": "easy"
}
```

## Performance Metrics (Estimated)

| Model | Time/PDF | Time for 34 PDFs | Quality Score |
|-------|----------|------------------|---------------|
| qwen2.5:14b | 3-5 min | ~2-3 hours | 95/100 |
| llama3.1:8b | 1-2 min | ~1 hour | 85/100 |
| mistral:7b | 1-2 min | ~1 hour | 75/100 |
| llama3.2:3b | <1 min | ~30 min | 65/100 |

## Advanced: Quantization Variants

If you want to try larger models with less RAM:

```bash
# Qwen2.5 32B quantized to 4-bit (might work on your system)
ollama pull qwen2.5:32b-q4_0

# Llama 3.1 70B quantized (probably too large still)
ollama pull llama3.1:70b-q4_0
```

**Note**: Quantized models (q4_0, q5_0) use less RAM but slightly lower quality.

## Testing Model Quality

Create a test script:

```bash
# test_models.sh
models=("qwen2.5:14b" "llama3.1:8b" "mistral:7b")
test_pdf="C:\LLM\tools\pdf_rag_in_out\input\The Karakatvas_..._nodrm.pdf"

for model in "${models[@]}"; do
    echo "Testing $model..."
    python scripts/qa_generator_ollama.py "$test_pdf" \
        -o "./test_output_${model}" \
        --model "$model" \
        --target-qa 5
done
```

## Troubleshooting

### Out of Memory Error
```
Error: model requires more memory than available
```
**Solution**: Use a smaller model (llama3.1:8b instead of qwen2.5:14b)

### Model Not Found
```
Error: model 'qwen2.5:14b' not found
```
**Solution**: Pull the model first: `ollama pull qwen2.5:14b`

### Slow Performance
**Solutions**:
1. Use smaller model (llama3.1:8b)
2. Reduce chunk size: `--chunk-size 2000`
3. Reduce target QA: `--target-qa 100`
4. Close other applications to free RAM

## Recommended Workflow

1. **Pull qwen2.5:14b**: `ollama pull qwen2.5:14b` (wait ~10 min)
2. **Test on 1 PDF**: Generate 10 QA pairs, review quality
3. **If satisfied**: Process all 34 PDFs (~2-3 hours)
4. **If not**: Try llama3.1:8b or adjust chunk size

## GPU Acceleration (If Available)

If you have an NVIDIA GPU with 8GB+ VRAM, Ollama will automatically use it for much faster processing!

Check: `nvidia-smi` (shows GPU memory)

With GPU:
- qwen2.5:14b: ~30-60 sec/PDF
- llama3.1:8b: ~15-30 sec/PDF

## Final Recommendation

**For best results with your system:**
```bash
# Pull the model
ollama pull qwen2.5:14b

# Process all PDFs
python scripts/qa_generator_ollama.py \
    "C:\LLM\tools\pdf_rag_in_out\input" \
    -o ./jyotish_qa_output \
    --model qwen2.5:14b \
    --target-qa 150 \
    --chunk-size 4000
```

Expected output: ~5,100 high-quality QA pairs (34 PDFs × 150 pairs)
Processing time: ~2-3 hours
