<!-- Copilot / AI agent instructions for contributors working on this repo -->

# Copilot Instructions — PDF -> Llama fine-tuning pipeline

Purpose: give an AI coding agent the minimal, concrete context to be productive in this repo.

- **Big picture**: PDF files are extracted (multiple fallback extractors) -> cleaned & chunked -> stored in an SQLite DB -> exported as JSONL for Llama fine-tuning. Key stages live under `src/extractors`, `src/processors`, `src/database`, and CLI scripts under `scripts/`.

- **Key files / classes to inspect before changing behavior**:
  - `src/extractors/pdf_extractor.py` - `PDFExtractor.extract_text()` returns a dict containing `text`, `file_hash`, `extraction_quality`, `pages`, `extraction_method`.
  - `src/database/db_manager.py` - `DatabaseManager` manages `documents`, `text_chunks`, and `training_data` tables and contains helpers: `insert_document`, `insert_text_chunks`, `insert_training_examples`, `export_training_data_to_jsonl`.
  - `src/processors/data_formatter.py` - `DataFormatter.format_for_training()` creates Alpaca/ChatML/raw examples, consumes pre-chunked text (if provided), and applies output quality guards to avoid input/output copying.
  - `src/processors/text_cleaner.py` - text normalization, special character cleanup, optional Sanskrit (Devanagari) romanization, and chunking helpers.
  - `scripts/process_pdfs.py` - top-level pipeline runner (CLI) that wires extractor, cleaner, formatter and DB.
  - `scripts/export_training.py` - export/validation CLI used to prepare final JSONL files for training.
  - `config/settings.yaml` - user-editable settings (extraction, cleaning, formatting, database). Loading helper is `src/utils/config.py`.

- **Data shapes & important fields** (refer to code when in doubt):
  - Extraction result: `{ 'filename','filepath','file_hash','text','pages', 'extraction_quality','extraction_method', ... }` — tools rely on `file_hash` for deduplication and `extraction_quality` for OCR fallback.
  - DB tables: `documents(file_hash UNIQUE)`, `text_chunks(chunk_hash UNIQUE)`, `training_data(example_hash UNIQUE)` — avoid creating duplicates; prefer DBManager helpers.

- **Developer workflows & CLI examples** (Windows PowerShell shown):
  - create venv and install deps:
    ```pwsh
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```
  - Process a directory of PDFs:
    ```pwsh
    python scripts/process_pdfs.py --input-dir C:\path\to\pdfs --output-dir .\output
    ```
  - Process a single PDF:
    ```pwsh
    python scripts/process_pdfs.py --single-pdf C:\path\to\doc.pdf
    ```
  - Default watch folders live under `C:\LLM\tools\pdf_rag_in_out`: drop PDFs into `input\`, outputs land per-document under `output\<PDF_NAME>\`.
  - Export training JSONL from DB:
    ```pwsh
    python scripts/export_training.py --output ./training_data.jsonl --split-validation 0.1
    ```
  - DB location: by default DB stored at `C:\LLM\tools\pdf_rag_db\processed_pdfs.db`. Override with `DATABASE_PATH` env var or `config/settings.yaml` -> `database.path`.

- **Project-specific conventions & patterns** (do not change these without cross-checking callers):
  - Multiple extractor fallbacks: `PDFExtractor` tries PyMuPDF, pdfplumber, pdfminer, PyPDF2 in order. Maintain the return structure and metadata fields if you add methods.
  - OCR fallback: controlled by `use_ocr` in config; `extraction_quality == 'poor'` triggers OCR attempt. OCR handler (if present) is `src/extractors/ocr_handler.py` and is imported lazily.
  - Chunking defaults: `chunk_size=1024`, `chunk_overlap=128`. `DataFormatter._create_text_chunks()` attempts sentence-boundary splits; preserve those semantics when changing partition logic.
  - Output quality guard: `DataFormatter` uses a similarity check to prevent outputs that mirror inputs; `formatting.include_continuation` controls whether continuation-style examples are emitted.
  - Text cleanup toggles: `cleaning.normalize_special_chars` and `cleaning.romanize_sanskrit` enable ASCII normalization and Devanagari romanization for Sanskrit content.
  - Database-first deduplication: `file_hash` and `chunk_hash`/`example_hash` are used to avoid duplicates - use DBManager helper methods instead of raw SQL where possible.
  - Logging: pipeline writes `pdf_processing.log` (see `scripts/process_pdfs.py` logging config). Keep log message formats stable for downstream parsing/monitoring.

- **Integration points & external dependencies**:
  - Heavy PDF libs: `PyMuPDF (fitz)`, `pdfplumber`, `pdfminer`, `PyPDF2`. Tesseract for OCR if `use_ocr` enabled.
  - Runtime assumptions: Python 3.8+, optional Tesseract binary on PATH for OCR.

- **When modifying export / format behavior**:
  - Keep `DataFormatter.save_to_jsonl()` output compatible with `DataFormatter.validate_jsonl()` expectations: Alpaca entries need `instruction`, `input`, `output`; ChatML entries need `messages` list.
  - Maintain `example_hash` determinism in `DatabaseManager.insert_training_examples()` to avoid duplicate examples across runs.
  - If adjusting training example generation, keep `max_output_similarity`, `max_summary_ratio`, and `include_continuation` in sync with `config/settings.yaml` defaults.

- **Tests / CI**: repository has a `tests/` folder but no visible tests — run manual end-to-end runs via `scripts/` CLIs for validation. Always validate exported JSONL with `DataFormatter.validate_jsonl()` after changes.

- **If you need to add new files or CLI flags**:
  - Add integration spots to `scripts/process_pdfs.py` and `scripts/export_training.py` (they centralize most user-facing behaviors).
  - Update `config/settings.yaml` and default-loading in `PDFProcessor._load_config()` to ensure flags are discoverable and documented.

If anything here is unclear or you'd like me to expand on a section (examples of extractor return values, DB schema notes, or CLI edge-cases), tell me which part to improve and I'll iterate.
