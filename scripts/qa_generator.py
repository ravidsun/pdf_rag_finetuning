#!/usr/bin/env python3
"""
Jyotish PDF QA Dataset Generator - FREE Ollama Version
======================================================
Generate high-quality QA pairs from Jyotish PDFs using FREE local LLMs via Ollama.
NO API KEY REQUIRED - runs completely offline!

Author: Modified for Ravi's Jyotish Fine-Tuning Project
Version: 2.0.0 (Ollama Edition)

Prerequisites:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: ollama pull llama3.1:8b
    3. Run: python qa_generator_ollama.py <pdf_folder> -o <output_folder>

Usage:
    python qa_generator_ollama.py "C:\LLM\tools\pdf_rag_in_out\input" -o ./output
    python qa_generator_ollama.py --help
"""

import os
import sys
import json
import re
import time
import uuid
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# PDF Processing
try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    os.system("pip install pdfplumber --quiet")
    import pdfplumber

try:
    from pypdf import PdfReader
except ImportError:
    print("Installing pypdf...")
    os.system("pip install pypdf --quiet")
    from pypdf import PdfReader

# LangChain with Ollama
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("Installing langchain-ollama...")
    os.system("pip install langchain-ollama --quiet")
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('qa_generation_ollama.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class QAPair:
    """Represents a single QA pair with metadata"""
    id: str
    source: Dict[str, Any]
    question: str
    answer: str
    qa_type: str
    difficulty: str
    tags: List[str]
    evidence: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

@dataclass
class ProcessingStats:
    """Track processing statistics"""
    total_pages: int = 0
    total_chunks: int = 0
    total_qa_pairs: int = 0
    api_calls: int = 0
    api_errors: int = 0
    start_time: Optional[datetime] = None

    def elapsed_time(self) -> str:
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            return str(elapsed).split('.')[0]
        return "0:00:00"

@dataclass
class Checkpoint:
    """Checkpoint for resumable processing"""
    pdf_name: str
    total_pages: int
    pages_processed: int
    qa_pairs_count: int
    last_page_range: Tuple[int, int]
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Checkpoint':
        return cls(**data)

# ============================================================================
# CONFIGURATION
# ============================================================================

SYSTEM_PROMPT = """You are an expert in Jyotish (Vedic Astrology) creating high-quality training data for fine-tuning language models. Your task is to generate diverse, educational question-answer pairs from the provided Jyotish text.

CRITICAL REQUIREMENTS:
1. Preserve ALL Sanskrit terms with their exact diacritical marks (ā, ī, ū, ṛ, ṣ, ś, ñ, etc.)
2. Include proper technical Jyotish terminology
3. Create self-contained, educational answers (2-4 sentences)
4. Extract actual evidence quotes from the source text
5. Mix difficulty levels and question types
6. Questions should be specific and educational, not generic

QA TYPES TO USE:
- definition: Define terms, concepts, or entities
- concept: Explain abstract principles or relationships
- rule: Describe Jyotish rules, yogas, or combinations
- procedure: Step-by-step methods or calculations
- comparison: Compare/contrast elements (Grahas, Rāśis, etc.)
- example: Practical applications or case studies
- interpretation: How to interpret placements or combinations
- checklist: Multiple factors to consider for analysis
- common_mistake: Errors to avoid in Jyotish practice

OUTPUT FORMAT - Return ONLY a valid JSON array (no markdown, no code blocks):
[
  {
    "question": "Clear, specific question about the content",
    "answer": "Comprehensive, accurate answer with technical details (2-4 sentences)",
    "qa_type": "one of the types listed above",
    "difficulty": "easy|medium|hard",
    "tags": ["relevant", "topic", "tags"],
    "evidence": ["Exact quote from source supporting this QA"]
  }
]

DIFFICULTY GUIDELINES:
- easy: Basic definitions, simple classifications, fundamental terms
- medium: Relationships between concepts, significations, characteristics
- hard: Complex yogas, multi-factor analysis, advanced calculations

Generate 3-6 high-quality QA pairs from the provided text. Focus on educational value and accuracy."""

VALID_QA_TYPES = [
    'definition', 'concept', 'rule', 'procedure',
    'comparison', 'example', 'interpretation',
    'checklist', 'common_mistake'
]

VALID_DIFFICULTIES = ['easy', 'medium', 'hard']

# ============================================================================
# PDF EXTRACTION
# ============================================================================

class PDFExtractor:
    """Extract text from PDF files with fallback methods"""

    @staticmethod
    def extract_with_pdfplumber(pdf_path: str, start_page: int = 0, end_page: int = None) -> str:
        """Primary extraction using pdfplumber (better for complex layouts)"""
        text_parts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                end_page = min(end_page or total_pages, total_pages)

                for i in range(start_page, end_page):
                    page = pdf.pages[i]
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"[Page {i + 1}]\n{page_text}")

        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")

        return "\n\n".join(text_parts)

    @staticmethod
    def extract_with_pypdf(pdf_path: str, start_page: int = 0, end_page: int = None) -> str:
        """Fallback extraction using pypdf"""
        text_parts = []
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            end_page = min(end_page or total_pages, total_pages)

            for i in range(start_page, end_page):
                page_text = reader.pages[i].extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"[Page {i + 1}]\n{page_text}")

        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")

        return "\n\n".join(text_parts)

    @classmethod
    def extract(cls, pdf_path: str, start_page: int = 0, end_page: int = None) -> str:
        """Extract text with automatic fallback"""
        # Try pdfplumber first
        text = cls.extract_with_pdfplumber(pdf_path, start_page, end_page)

        # Fallback to pypdf if needed
        if not text or len(text) < 100:
            logger.info("Falling back to pypdf extraction...")
            text = cls.extract_with_pypdf(pdf_path, start_page, end_page)

        return text

    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """Get total page count of PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except:
            try:
                reader = PdfReader(pdf_path)
                return len(reader.pages)
            except:
                return 0

# ============================================================================
# TEXT CHUNKING
# ============================================================================

class TextChunker:
    """Smart text chunking with section detection"""

    # Section header patterns for Jyotish texts
    SECTION_PATTERNS = [
        r'^\d+\.\d+\.\d+\s+\w+',  # 2.1.1 Section
        r'^Chapter\s+\d+',
        r'^CHAPTER\s+\d+',
        r'^\d+\s+[A-Z][A-Z\s]+$',  # Numbered uppercase titles
        r'^[A-Z][a-zA-Zāīūṛṣśñ]+\s+[A-Z][a-zA-Zāīūṛṣśñ]+$',  # Title Case Headers
    ]

    def __init__(self, chunk_size: int = 4000, overlap: int = 400):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.section_regex = [re.compile(p, re.MULTILINE) for p in self.SECTION_PATTERNS]

    def detect_section_title(self, text: str) -> Optional[str]:
        """Try to detect section title from text"""
        lines = text.strip().split('\n')[:5]
        for line in lines:
            line = line.strip()
            for pattern in self.section_regex:
                if pattern.match(line):
                    return line[:100]
        return None

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks with metadata"""
        if not text:
            return []

        chunks = []
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at paragraph boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start + self.chunk_size // 2, end)
                if para_break > start:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = text.rfind('. ', start + self.chunk_size // 2, end)
                    if sent_break > start:
                        end = sent_break + 1

            chunk_text = text[start:end].strip()

            if len(chunk_text) > 200:  # Only include substantial chunks
                section_title = self.detect_section_title(chunk_text)

                # Extract page numbers from chunk
                page_matches = re.findall(r'\[Page (\d+)\]', chunk_text)
                pages = [int(p) for p in page_matches] if page_matches else []

                chunks.append({
                    'index': chunk_idx,
                    'text': chunk_text,
                    'section_title': section_title,
                    'pages': pages,
                    'char_start': start,
                    'char_end': end
                })
                chunk_idx += 1

            start = end - self.overlap

        return chunks

# ============================================================================
# QA GENERATION WITH OLLAMA
# ============================================================================

class QAGenerator:
    """Generate QA pairs using Ollama (FREE local LLM)"""

    def __init__(self, model: str = "qwen2.5:14b", base_url: str = "http://localhost:11434"):
        """
        Initialize QA generator with Ollama

        Args:
            model: Ollama model name (default: qwen2.5:14b)
                   Other options: llama3.1:8b, mistral, phi3, gemma2, etc.
            base_url: Ollama server URL
        """
        try:
            self.llm = ChatOllama(
                model=model,
                base_url=base_url,
                temperature=0.3,
                num_predict=4096
            )
            logger.info(f"Initialized Ollama with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            logger.error("Make sure Ollama is installed and running:")
            logger.error("  1. Install: https://ollama.ai")
            logger.error(f"  2. Pull model: ollama pull {model}")
            logger.error("  3. Start: ollama serve")
            raise

        self.stats = ProcessingStats()

    def generate_from_chunk(
        self,
        chunk: Dict[str, Any],
        pdf_name: str,
        retry_count: int = 3
    ) -> List[QAPair]:
        """Generate QA pairs from a single chunk"""

        prompt = f"""Source: {pdf_name}
{f"Section: {chunk['section_title']}" if chunk.get('section_title') else ""}
{f"Pages: {min(chunk['pages'])}-{max(chunk['pages'])}" if chunk.get('pages') else ""}

TEXT TO ANALYZE:
{chunk['text']}

Generate 3-6 high-quality QA pairs from this Jyotish text.
Return ONLY a valid JSON array with no additional text or markdown."""

        for attempt in range(retry_count):
            try:
                self.stats.api_calls += 1

                response = self.llm.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ])

                # Parse response
                content = response.content

                # Clean markdown code blocks
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                content = content.strip()

                # Parse JSON
                qa_list = json.loads(content)

                if not isinstance(qa_list, list):
                    raise ValueError("Response is not a list")

                # Convert to QAPair objects with validation
                qa_pairs = []
                for i, qa in enumerate(qa_list):
                    if not isinstance(qa, dict):
                        continue
                    if not qa.get('question') or not qa.get('answer'):
                        continue

                    # Validate and fix qa_type
                    qa_type = qa.get('qa_type', 'concept')
                    if qa_type not in VALID_QA_TYPES:
                        qa_type = 'concept'

                    # Validate and fix difficulty
                    difficulty = qa.get('difficulty', 'medium')
                    if difficulty not in VALID_DIFFICULTIES:
                        difficulty = 'medium'

                    # Create unique ID
                    pdf_short = pdf_name[:30].replace('.pdf', '').replace('_nodrm', '')
                    qa_id = f"{pdf_short}_p{min(chunk['pages']) if chunk.get('pages') else 0}_{i}_{uuid.uuid4().hex[:6]}"

                    qa_pair = QAPair(
                        id=qa_id,
                        source={
                            'pdf_name': pdf_name,
                            'page_start': min(chunk['pages']) if chunk.get('pages') else 0,
                            'page_end': max(chunk['pages']) if chunk.get('pages') else 0,
                            'section_title': chunk.get('section_title', '')
                        },
                        question=qa['question'],
                        answer=qa['answer'],
                        qa_type=qa_type,
                        difficulty=difficulty,
                        tags=qa.get('tags', []),
                        evidence=qa.get('evidence', [])
                    )
                    qa_pairs.append(qa_pair)

                return qa_pairs

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                logger.warning(f"Response was: {content[:200]}...")
                self.stats.api_errors += 1

            except Exception as e:
                logger.warning(f"Generation error (attempt {attempt + 1}): {e}")
                self.stats.api_errors += 1

            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        return []

# ============================================================================
# MAIN PROCESSOR
# ============================================================================

class JyotishQAProcessor:
    """Main processor for generating QA datasets from Jyotish PDFs"""

    def __init__(
        self,
        output_dir: str = "./output",
        chunk_size: int = 4000,
        chunk_overlap: int = 400,
        rate_limit_delay: float = 0.5,
        model: str = "qwen2.5:14b"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Checkpoint file
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        self.progress_file = self.output_dir / "progress.json"

        self.extractor = PDFExtractor()
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.generator = QAGenerator(model=model)
        self.rate_limit_delay = rate_limit_delay

        self.stats = ProcessingStats()

    def save_checkpoint(self, pdf_name: str, total_pages: int, pages_processed: int,
                       qa_pairs_count: int, last_page_range: Tuple[int, int]):
        """Save checkpoint for resuming later"""
        checkpoint = Checkpoint(
            pdf_name=pdf_name,
            total_pages=total_pages,
            pages_processed=pages_processed,
            qa_pairs_count=qa_pairs_count,
            last_page_range=last_page_range,
            timestamp=datetime.now().isoformat()
        )
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)
        logger.info(f"💾 Checkpoint saved: {pdf_name} ({pages_processed}/{total_pages} pages, {qa_pairs_count} QA pairs)")

    def load_checkpoint(self) -> Optional[Checkpoint]:
        """Load checkpoint if exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Checkpoint.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return None

    def clear_checkpoint(self):
        """Clear checkpoint after completing a PDF"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info("✓ Checkpoint cleared")

    def save_progress(self, completed_pdfs: List[str], total_pdfs: int):
        """Save overall progress"""
        progress = {
            'completed_pdfs': completed_pdfs,
            'total_pdfs': total_pdfs,
            'completion_percentage': (len(completed_pdfs) / total_pdfs * 100) if total_pdfs > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)

    def load_progress(self) -> Dict[str, Any]:
        """Load overall progress"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load progress: {e}")
        return {'completed_pdfs': [], 'total_pdfs': 0, 'completion_percentage': 0}

    def process_pdf(
        self,
        pdf_path: str,
        page_ranges: Optional[List[Tuple[int, int]]] = None,
        target_qa_count: Optional[int] = None,
        qa_multiplier: float = 2.0,
        resume: bool = True
    ) -> List[QAPair]:
        """Process a single PDF and generate QA pairs

        Args:
            pdf_path: Path to PDF file
            page_ranges: Optional specific page ranges to process
            target_qa_count: Optional fixed target QA count (overrides qa_multiplier)
            qa_multiplier: Generate this many QA pairs per page (default: 2.0)
            resume: Whether to resume from checkpoint if available
        """

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return []

        pdf_name = pdf_path.name
        total_pages = self.extractor.get_page_count(str(pdf_path))

        # Calculate target based on page count if not explicitly set
        if target_qa_count is None:
            target_qa_count = int(total_pages * qa_multiplier)

        # Check for checkpoint
        checkpoint = None
        all_qa_pairs = []
        start_range_idx = 0

        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint and checkpoint.pdf_name == pdf_name:
                logger.info(f"📂 Resuming from checkpoint...")
                logger.info(f"   Previously processed: {checkpoint.pages_processed}/{total_pages} pages")
                logger.info(f"   QA pairs so far: {checkpoint.qa_pairs_count}")

                # Load existing QA pairs
                output_file = self.output_dir / f"{pdf_path.stem}_qa.jsonl"
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            qa_data = json.loads(line.strip())
                            all_qa_pairs.append(QAPair(**qa_data))

                # Calculate which range to resume from
                start_range_idx = checkpoint.last_page_range[1] // 50

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pdf_name}")
        logger.info(f"Total Pages: {total_pages}")
        logger.info(f"Target QA Pairs: {target_qa_count} ({qa_multiplier}x pages)")
        if checkpoint:
            logger.info(f"Resuming from page: {checkpoint.pages_processed}")
        logger.info(f"{'='*60}")

        # Determine page ranges to process
        if page_ranges:
            ranges_to_process = page_ranges
        else:
            # Default: process in chunks of 50 pages
            ranges_to_process = [(i, min(i + 50, total_pages))
                                for i in range(0, total_pages, 50)]

        # Start from the resume point
        ranges_to_process = ranges_to_process[start_range_idx:]

        for range_idx, (start, end) in enumerate(ranges_to_process, start=start_range_idx):
            logger.info(f"\nExtracting pages {start}-{end}...")

            # Extract text
            text = self.extractor.extract(str(pdf_path), start - 1, end)
            if not text:
                logger.warning(f"No text extracted from pages {start}-{end}")
                continue

            # Chunk text
            chunks = self.chunker.chunk(text)
            logger.info(f"Created {len(chunks)} chunks")
            self.stats.total_chunks += len(chunks)

            # Generate QA pairs from each chunk
            for chunk in chunks:
                logger.info(f"  Processing chunk {chunk['index'] + 1}/{len(chunks)}...")

                qa_pairs = self.generator.generate_from_chunk(
                    chunk,
                    pdf_name=pdf_name
                )

                all_qa_pairs.extend(qa_pairs)
                logger.info(f"  Generated {len(qa_pairs)} QA pairs (Total: {len(all_qa_pairs)})")

                # Save progress incrementally
                book_name = pdf_path.stem
                output_file = self.output_dir / f"{book_name}_qa.jsonl"
                self.save_qa_pairs(all_qa_pairs, output_file)

                # Rate limiting
                time.sleep(self.rate_limit_delay)

                # Check if we've reached target
                if len(all_qa_pairs) >= target_qa_count:
                    logger.info(f"Reached target QA count: {target_qa_count}")
                    break

            # Save checkpoint after each page range
            self.save_checkpoint(
                pdf_name=pdf_name,
                total_pages=total_pages,
                pages_processed=end,
                qa_pairs_count=len(all_qa_pairs),
                last_page_range=(start, end)
            )

            if len(all_qa_pairs) >= target_qa_count:
                break

        self.stats.total_qa_pairs += len(all_qa_pairs)

        # Clear checkpoint when PDF is complete
        if len(all_qa_pairs) >= target_qa_count or end >= total_pages:
            self.clear_checkpoint()

        return all_qa_pairs

    def process_folder(
        self,
        pdf_folder: str,
        target_qa_per_book: Optional[int] = None,
        qa_multiplier: float = 2.0,
        resume: bool = True
    ) -> Dict[str, List[QAPair]]:
        """Process all PDFs in a folder with resume capability

        Args:
            pdf_folder: Path to folder containing PDFs
            target_qa_per_book: Optional fixed target QA count per book (overrides qa_multiplier)
            qa_multiplier: Generate this many QA pairs per page (default: 2.0)
            resume: Whether to resume from previous progress
        """

        pdf_folder = Path(pdf_folder)
        pdf_files = sorted(pdf_folder.glob("*.pdf"))

        if not pdf_files:
            logger.error(f"No PDF files found in {pdf_folder}")
            return {}

        # Load progress
        progress = self.load_progress() if resume else {'completed_pdfs': [], 'total_pdfs': 0}
        completed_pdfs = set(progress.get('completed_pdfs', []))

        # Filter out already completed PDFs
        remaining_pdfs = [pdf for pdf in pdf_files if pdf.stem not in completed_pdfs]

        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH PROCESSING STATUS")
        logger.info(f"{'='*60}")
        logger.info(f"Total PDFs: {len(pdf_files)}")
        logger.info(f"Completed: {len(completed_pdfs)}")
        logger.info(f"Remaining: {len(remaining_pdfs)}")
        logger.info(f"QA Generation Mode: {target_qa_per_book if target_qa_per_book else f'{qa_multiplier}x page count'}")
        logger.info(f"{'='*60}\n")

        if not remaining_pdfs:
            logger.info("✅ All PDFs already processed!")
            return {}

        self.stats.start_time = datetime.now()
        results = {}

        for idx, pdf_file in enumerate(remaining_pdfs, 1):
            try:
                logger.info(f"\n📄 [{idx}/{len(remaining_pdfs)}] Processing: {pdf_file.name}")

                qa_pairs = self.process_pdf(
                    str(pdf_file),
                    target_qa_count=target_qa_per_book,
                    qa_multiplier=qa_multiplier,
                    resume=resume
                )

                if qa_pairs:
                    book_name = pdf_file.stem

                    # Save to individual file
                    output_file = self.output_dir / f"{book_name}_qa.jsonl"
                    self.save_qa_pairs(qa_pairs, output_file)

                    results[book_name] = qa_pairs

                    # Mark as completed
                    completed_pdfs.add(book_name)
                    self.save_progress(list(completed_pdfs), len(pdf_files))

                    logger.info(f"✅ Completed: {book_name} ({len(qa_pairs)} QA pairs)")
                    logger.info(f"📊 Overall Progress: {len(completed_pdfs)}/{len(pdf_files)} PDFs ({len(completed_pdfs)/len(pdf_files)*100:.1f}%)")

            except KeyboardInterrupt:
                logger.warning(f"\n⚠️  Process interrupted by user!")
                logger.info(f"Progress saved. Resume by running the same command.")
                logger.info(f"Completed: {len(completed_pdfs)}/{len(pdf_files)} PDFs")
                raise

            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                logger.info(f"Skipping to next PDF...")
                continue

        # Save combined file
        if results:
            all_pairs = []
            for pairs in results.values():
                all_pairs.extend(pairs)
            combined_file = self.output_dir / "all_books_combined_qa.jsonl"
            self.save_qa_pairs(all_pairs, combined_file)

        # Print summary
        self.print_summary(results)

        return results

    def save_qa_pairs(self, qa_pairs: List[QAPair], output_file: Path):
        """Save QA pairs to JSONL file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for qa in qa_pairs:
                f.write(json.dumps(qa.to_dict(), ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(qa_pairs)} QA pairs to {output_file}")

    def print_summary(self, results: Dict[str, List[QAPair]]):
        """Print processing summary"""
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Time: {self.stats.elapsed_time()}")
        print(f"Total Chunks Processed: {self.stats.total_chunks}")
        print(f"Total LLM Calls: {self.generator.stats.api_calls}")
        print(f"LLM Errors: {self.generator.stats.api_errors}")
        print(f"\nQA Pairs Generated:")

        total = 0
        for book_name, pairs in results.items():
            print(f"  {book_name}: {len(pairs)} pairs")
            total += len(pairs)

        print(f"\nTOTAL: {total} QA pairs")
        print(f"Output Directory: {self.output_dir}")
        print(f"{'='*60}\n")

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate QA training data from Jyotish PDFs using FREE Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process folder with auto-resume (default)
  python qa_generator_ollama.py "C:\\LLM\\tools\\pdf_rag_in_out\\input" -o ./output

  # Process single PDF with 2x QA pairs per page
  python qa_generator_ollama.py /path/to/book.pdf -o ./output

  # Generate 3x QA pairs per page
  python qa_generator_ollama.py /path/to/pdfs/ -o ./output --qa-multiplier 3.0

  # Start fresh without resuming
  python qa_generator_ollama.py /path/to/pdfs/ -o ./output --no-resume

  # Check progress status
  python qa_generator_ollama.py --status -o ./output

Features:
  - Auto-saves progress after each page batch
  - Resume from checkpoint if interrupted (Ctrl+C)
  - Tracks completed PDFs across sessions
  - Incremental JSONL file updates
        """
    )

    parser.add_argument(
        "input_path",
        nargs='?',
        help="Path to PDF file or folder containing PDFs"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current progress status and exit"
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh, ignoring any existing checkpoints"
    )

    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Output directory for JSONL files (default: ./output)"
    )

    parser.add_argument(
        "--target-qa",
        type=int,
        default=None,
        help="Fixed target number of QA pairs per book (overrides --qa-multiplier)"
    )

    parser.add_argument(
        "--qa-multiplier",
        type=float,
        default=2.0,
        help="Generate this many QA pairs per page (default: 2.0). Ignored if --target-qa is set."
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4000,
        help="Text chunk size in characters (default: 4000)"
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.5,
        help="Delay between LLM calls in seconds (default: 0.5)"
    )

    parser.add_argument(
        "--model",
        default="qwen2.5:14b",
        help="Ollama model to use (default: qwen2.5:14b). Other options: llama3.1:8b, mistral, phi3, gemma2"
    )

    args = parser.parse_args()

    # Initialize processor
    processor = JyotishQAProcessor(
        output_dir=args.output,
        chunk_size=args.chunk_size,
        rate_limit_delay=args.rate_limit,
        model=args.model
    )

    # Handle status check
    if args.status:
        progress = processor.load_progress()
        checkpoint = processor.load_checkpoint()

        print(f"\n{'='*60}")
        print("CURRENT PROGRESS STATUS")
        print(f"{'='*60}")
        print(f"Output Directory: {processor.output_dir}")
        print(f"\nBatch Progress:")
        print(f"  Total PDFs: {progress.get('total_pdfs', 0)}")
        print(f"  Completed: {len(progress.get('completed_pdfs', []))}")
        print(f"  Remaining: {progress.get('total_pdfs', 0) - len(progress.get('completed_pdfs', []))}")
        print(f"  Completion: {progress.get('completion_percentage', 0):.1f}%")

        if checkpoint:
            print(f"\nActive Checkpoint:")
            print(f"  PDF: {checkpoint.pdf_name}")
            print(f"  Pages Processed: {checkpoint.pages_processed}/{checkpoint.total_pages}")
            print(f"  QA Pairs: {checkpoint.qa_pairs_count}")
            print(f"  Last Updated: {checkpoint.timestamp}")
        else:
            print(f"\nNo active checkpoint")

        if progress.get('completed_pdfs'):
            print(f"\nCompleted PDFs:")
            for pdf in progress['completed_pdfs'][:10]:
                print(f"  ✓ {pdf}")
            if len(progress['completed_pdfs']) > 10:
                print(f"  ... and {len(progress['completed_pdfs']) - 10} more")

        print(f"{'='*60}\n")
        sys.exit(0)

    # Validate input path
    if not args.input_path:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input_path)
    resume = not args.no_resume

    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        # Process single PDF
        qa_pairs = processor.process_pdf(
            str(input_path),
            target_qa_count=args.target_qa,
            qa_multiplier=args.qa_multiplier,
            resume=resume
        )

        if qa_pairs:
            book_name = input_path.stem
            output_file = processor.output_dir / f"{book_name}_qa.jsonl"
            processor.save_qa_pairs(qa_pairs, output_file)
            processor.print_summary({book_name: qa_pairs})

    elif input_path.is_dir():
        # Process folder
        processor.process_folder(
            str(input_path),
            target_qa_per_book=args.target_qa,
            qa_multiplier=args.qa_multiplier,
            resume=resume
        )
    else:
        print(f"ERROR: Invalid input path: {input_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
