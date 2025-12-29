# Install Ollama and Qwen2.5:32b Model

Your configuration has been updated to use **qwen2.5:32b** for better quality QA generation.

## Step 1: Install Ollama

### Windows Installation

1. **Download Ollama for Windows:**
   - Visit: https://ollama.ai/download
   - Click "Download for Windows"
   - Or direct link: https://ollama.ai/download/windows

2. **Run the Installer:**
   - Double-click the downloaded `OllamaSetup.exe`
   - Follow the installation wizard
   - Accept the default installation location

3. **Verify Installation:**
   ```cmd
   ollama --version
   ```

   You should see something like: `ollama version 0.x.x`

## Step 2: Pull the qwen2.5:32b Model

Once Ollama is installed, download the model:

```cmd
ollama pull qwen2.5:32b
```

**Expected:**
- Download size: ~19GB
- Time: Depends on your internet speed (10-30 minutes)
- Disk space needed: ~20GB

### Monitor Download Progress

The command will show progress:
```
pulling manifest
pulling 8934d96d3f08... 100% ▕████████████████▏ 19 GB
pulling 8c17c2ebb0ea... 100% ▕████████████████▏ 7.0 KB
pulling 7c23fb36d801... 100% ▕████████████████▏ 4.8 KB
pulling 2e0493f67d0c... 100% ▕████████████████▏  59 B
pulling fa8235e5b48f... 100% ▕████████████████▏ 486 B
verifying sha256 digest
writing manifest
success
```

## Step 3: Verify Model is Ready

```cmd
ollama list
```

**Expected Output:**
```
NAME                ID              SIZE      MODIFIED
qwen2.5:32b        abc123def       19 GB     2 minutes ago
```

## Step 4: Test the Model

Quick test to ensure it's working:

```cmd
ollama run qwen2.5:32b "What is Jyotish?"
```

You should get a response about Vedic Astrology.

Press `Ctrl+D` or type `/bye` to exit the chat.

## Step 5: Start Processing Your PDFs

Now you're ready to run the QA generator:

```bash
cd d:\MyProjects\pdf_rag_finetuning
python scripts\qa_generator.py --config config.yaml
```

Or use the batch script:
```bash
run_fresh.bat
```

## Configuration Summary

Your system is now configured to use:

✅ **Model**: qwen2.5:32b
✅ **Input Folder**: D:/MyProjects/data/input
✅ **Output Folder**: D:/MyProjects/data/output

## Troubleshooting

### Issue: "ollama: command not found" after installation

**Solution 1**: Restart your terminal/command prompt

**Solution 2**: Log out and log back in to Windows

**Solution 3**: Check if Ollama is in PATH:
```cmd
where ollama
```

If not found, add to PATH:
1. Search for "Environment Variables" in Windows
2. Edit "Path" variable
3. Add: `C:\Users\<YourUsername>\AppData\Local\Programs\Ollama\bin`

### Issue: Ollama service not running

**Solution**: Start Ollama service:
```cmd
ollama serve
```

Leave this terminal open, and run commands in a new terminal.

### Issue: Download is very slow

**Solution**:
- Check your internet connection
- Try again later
- The model is large (~19GB), so it will take time

### Issue: Not enough disk space

**Solution**:
- Free up at least 25GB of disk space
- Delete old/unused models: `ollama rm <model-name>`

## Alternative: Start with Smaller Model First

If you want to test before downloading 19GB:

```cmd
# Pull the 14b model (smaller, ~8GB)
ollama pull qwen2.5:14b

# Test with 14b first
# Then upgrade to 32b later
```

## System Requirements Check

✅ **Your System:**
- CPU: Intel Core Ultra 9 185H ✅
- RAM: 96GB ✅
- Recommended for: qwen2.5:32b or even 70b models

**You're all set for high-quality processing!**

## Expected Performance

With qwen2.5:32b on your system:

| Metric | Value |
|--------|-------|
| Processing Speed | ~30-45 seconds/page |
| RAM Usage | ~25GB |
| CPU Usage | 60-80% |
| Quality Improvement | 30-40% better than 14b |

## Next Steps

1. ✅ Install Ollama from https://ollama.ai/download
2. ✅ Run: `ollama pull qwen2.5:32b`
3. ✅ Verify: `ollama list`
4. ✅ Add your PDFs to: `D:\MyProjects\data\input`
5. ✅ Run: `run_fresh.bat` or `python scripts\qa_generator.py --config config.yaml`

## Support Links

- **Ollama Website**: https://ollama.ai
- **Ollama GitHub**: https://github.com/ollama/ollama
- **Model Library**: https://ollama.ai/library
- **Documentation**: https://github.com/ollama/ollama/tree/main/docs

---

**Your configuration files have already been updated to use qwen2.5:32b!**

Just install Ollama, pull the model, and you're ready to go! 🚀
