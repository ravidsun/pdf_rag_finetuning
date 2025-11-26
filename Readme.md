# PDF to Llama 3.1 Fine-tuning Pipeline

A production-ready pipeline for processing domain-specific PDFs into training data for Llama 3.1 fine-tuning using QLoRA on RunPod.

## 🚀 Features

- **Multi-method PDF extraction** with automatic fallback (PyMuPDF, pdfplumber, pdfminer, PyPDF2)
- **OCR support** for scanned PDFs using Tesseract
- **Domain-specific text cleaning** with customizable rules
- **Smart chunking** with overlap for context preservation
- **JSONL formatting** compatible with Llama 3.1 training formats (Alpaca, ChatML, Raw)
- **SQLite database** for persistent storage and deduplication
- **Batch processing** with memory management
- **Quality validation** and statistics reporting
- **Progress tracking** and comprehensive logging

## 📋 Requirements

- Python 3.8+
- 8GB+ RAM recommended
- Optional: Tesseract for OCR support

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/pdf-llama-finetuning.git
cd pdf-llama-finetuning
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Install Tesseract for OCR
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

## 📁 Project Structure

```
pdf-llama-finetuning/
├── config/
│   └── settings.yaml          # Configuration settings
├── scripts/
│   ├── process_pdfs.py        # Main processing script
│   ├── validate_data.py       # Data validation
│   └── export_training.py     # Export to JSONL
├── src/
│   ├── extractors/            # PDF extraction modules
│   ├── processors/            # Text processing
│   ├── database/              # Database management
│   └── utils/                 # Utility functions
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # Documentation
```

## 🔧 Configuration

Edit `config/settings.yaml` to customize:

- **Extraction settings**: OCR, batch size, timeout
- **Text cleaning**: Domain terms, minimum lengths
- **Formatting**: Chunk size, overlap, output format
- **Database**: Path, backup settings
- **Processing**: Quality thresholds, retry logic

## 📊 Database Storage

All database artifacts are stored under the shared tools directory:
- **Location**: `C:\LLM\tools\pdf_rag_db\processed_pdfs.db`
- **Configurable**: Set `DATABASE_PATH` in `.env` or adjust `config/settings.yaml`

## 📁 Input / Output Folders

Place PDFs to be processed in `C:\LLM\tools\pdf_rag_in_out\input`. Each processed PDF writes its JSONL outputs and stats to `C:\LLM\tools\pdf_rag_in_out\output\<PDF_NAME>\`, so multiple JSON artifacts for one document stay grouped together.

## 🚦 Quick Start

### Process a directory of PDFs
```bash
python scripts/process_pdfs.py --input-dir /path/to/pdfs --batch-size 5
```

### Process a single PDF
```bash
python scripts/process_pdfs.py --single-pdf document.pdf
```

### Validate processed data
```bash
python scripts/validate_data.py output/training_data.jsonl
```

### Export training data
```bash
python scripts/export_training.py --output training_data.jsonl
```

### Export with train/validation split
```bash
python scripts/export_training.py --output data.jsonl --split-validation 0.1
```

## 📈 Workflow

1. **Extract** - Multiple extraction methods with automatic fallback
2. **Clean** - Domain-specific text preprocessing
3. **Chunk** - Smart text segmentation with overlap
4. **Format** - Convert to training format (Alpaca/ChatML)
5. **Store** - Save to database with deduplication
6. **Validate** - Quality checks and statistics
7. **Export** - Generate JSONL for training

## 🎯 Training Formats

### Alpaca Format
```json
{
    "instruction": "Analyze the following text",
    "input": "Document content here",
    "output": "Expected response"
}
```

### ChatML Format
```json
{
    "messages": [
        {"role": "system", "content": "You are an expert assistant"},
        {"role": "user", "content": "Question about document"},
        {"role": "assistant", "content": "Response"}
    ]
}
```

## 🏃 RunPod Integration

After processing your PDFs:

1. **Upload JSONL** to RunPod storage
2. **Launch instance** with RTX 4090
3. **Install dependencies**:
```bash
pip install transformers accelerate peft bitsandbytes
```

4. **Start fine-tuning** with your processed data

## 📊 Monitoring

### Check database statistics
```bash
python scripts/process_pdfs.py --db-stats
```

### View processing logs
```bash
tail -f pdf_processing.log
```

## 🐛 Troubleshooting

### OCR not working
- Install Tesseract: `sudo apt-get install tesseract-ocr`
- Set path in `.env`: `TESSERACT_PATH=/usr/bin/tesseract`

### Memory errors
- Reduce batch size in `config/settings.yaml`
- Process larger PDFs individually

### Poor extraction quality
- Enable OCR: Set `use_ocr: true` in settings
- Try different extraction methods
- Check PDF encryption/permissions

## 📚 Best Practices

1. **Start small** - Process 3-5 PDFs first
2. **Review quality** - Check extracted text samples
3. **Adjust settings** - Tune for your domain
4. **Monitor progress** - Watch logs for issues
5. **Validate data** - Run validation before training
6. **Backup database** - Regular backups recommended

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Anthropic Claude for AI assistance
- PyMuPDF, pdfplumber teams for excellent libraries
- RunPod for GPU infrastructure
- Meta for Llama models

## 📧 Support

For issues or questions:
- Open a GitHub issue
- Check BEST_PRACTICES.md for domain-specific guidance
- Review logs for debugging information
