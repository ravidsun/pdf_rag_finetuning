#!/usr/bin/env python3
"""
Main PDF Processing Script
Processes PDFs in batches and prepares them for Llama 3.1 fine-tuning
"""

import argparse
import sys
import os
from pathlib import Path
import logging
import yaml
from typing import List, Dict, Optional, Union
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Shared input/output directories
IO_BASE_DIR = Path(r"C:\LLM\tools\pdf_rag_in_out")
DEFAULT_INPUT_DIR = IO_BASE_DIR / "input"
DEFAULT_OUTPUT_DIR = IO_BASE_DIR / "output"
for directory in (DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

from src.extractors.pdf_extractor import PDFExtractor
from src.processors.text_cleaner import TextCleaner
from src.processors.data_formatter import DataFormatter
from src.database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Main PDF processing pipeline"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize PDF processor
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.extractor = PDFExtractor(self.config.get('extraction', {}))
        self.cleaner = TextCleaner(self.config.get('cleaning', {}))
        self.formatter = DataFormatter(self.config.get('formatting', {}))
        
        # Initialize database
        db_path = os.getenv('DATABASE_PATH') or self.config.get('database', {}).get('path')
        self.db = DatabaseManager(db_path)
        
        logger.info("PDF Processor initialized")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from file"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # Default configuration
            config = {
                'extraction': {
                    'use_ocr': False,
                    'batch_size': 5
                },
                'cleaning': {
                    'preserve_terms': [],
                    'min_chunk_length': 100,
                    'min_word_count': 20,
                    'remove_citations': False,
                    'remove_equations': False,
                    'normalize_special_chars': True,
                    'romanize_sanskrit': True,
                    'romanization_scheme': 'ascii'
                },
                'formatting': {
                    'max_length': 2048,
                    'chunk_size': 1024,
                    'chunk_overlap': 128,
                    'shuffle': True,
                    'augment_data': False,
                    'include_metadata': False,
                    'include_continuation': False,
                    'max_output_similarity': 0.75,
                    'max_summary_ratio': 0.35,
                    'max_summary_length': 200,
                    'min_keyword_count': 4,
                    'max_keyword_count': 8,
                    'output_format': 'alpaca'
                },
                'database': {
                    'path': None  # Will use default
                },
                'processing': {
                    'batch_size': 5,
                    'skip_existing': True,
                    'quality_threshold': 'medium'
                }
            }
        
        return config
    
    def process_directory(
        self,
        input_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        """
        Process all PDFs in a directory
        
        Args:
            input_dir: Directory containing PDFs
            output_dir: Directory for output files
            batch_size: Number of PDFs to process at once
        """
        input_path = Path(input_dir or DEFAULT_INPUT_DIR)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_path}")

        output_root = Path(output_dir or DEFAULT_OUTPUT_DIR)
        output_root.mkdir(parents=True, exist_ok=True)
        
        # Get all PDF files
        pdf_files = list(input_path.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {input_dir}")
        
        if not pdf_files:
            logger.warning("No PDF files found")
            return
        
        # Set batch size
        if batch_size is None:
            batch_size = self.config['processing']['batch_size']
        
        # Process in batches
        processed_count = 0
        failed_count = 0
        total_examples = 0
        
        for i in range(0, len(pdf_files), batch_size):
            batch = pdf_files[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(pdf_files) + batch_size - 1) // batch_size
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing batch {batch_num}/{total_batches}")
            logger.info(f"{'='*60}")
            
            for pdf_path in batch:
                try:
                    pdf_output_dir = output_root / pdf_path.stem
                    result = self.process_single_pdf(
                        str(pdf_path), output_dir=pdf_output_dir
                    )
                    
                    if result['success']:
                        processed_count += 1
                        total_examples += len(result['training_data'])
                        logger.info(f"[OK] Successfully processed: {pdf_path.name}")
                    else:
                        failed_count += 1
                        logger.error(f"[FAIL] Failed to process: {pdf_path.name}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"[FAIL] Error processing {pdf_path.name}: {str(e)}")
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESSING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total PDFs: {len(pdf_files)}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Training examples created: {total_examples}")
        
        # Show database statistics
        stats = self.db.get_statistics()
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total documents: {stats['total_documents']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Total training examples: {stats['total_training_examples']}")
        logger.info(f"  Estimated tokens: {stats['total_tokens_estimate']:,}")
    
    def process_single_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict:
        """
        Process a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Processing result dictionary
        """
        result = {
            'success': False,
            'pdf_path': pdf_path,
            'training_data': [],
            'errors': []
        }
        
        try:
            # Step 1: Extract text
            logger.info(f"Extracting text from: {Path(pdf_path).name}")
            extraction_result = self.extractor.extract_text(pdf_path)
            
            if not extraction_result.get('text'):
                result['errors'].append("No text extracted")
                return result
            
            # Check if already processed
            if self.config['processing']['skip_existing']:
                if self.db.document_exists(extraction_result['file_hash']):
                    logger.info(f"Document already processed: {Path(pdf_path).name}")
                    result['success'] = True
                    return result
            
            # Step 2: Insert document into database
            doc_id = self.db.insert_document(extraction_result)
            
            # Step 3: Clean text
            logger.info(f"Cleaning extracted text...")
            cleaned_text = self.cleaner.clean_text(extraction_result['text'])
            
            # Get text statistics
            text_stats = self.cleaner.get_statistics(cleaned_text)
            logger.info(f"  Words: {text_stats['word_count']:,}, "
                       f"Sentences: {text_stats['sentence_count']}, "
                       f"Vocabulary: {text_stats['unique_words']:,}")
            
            # Step 4: Create training chunks
            logger.info(f"Creating training chunks...")
            training_chunks = self.cleaner.clean_for_training(
                cleaned_text,
                max_length=self.config['formatting']['chunk_size']
            )
            
            # Insert chunks into database
            chunk_ids = self.db.insert_text_chunks(doc_id, training_chunks)
            
            # Step 5: Format for training
            logger.info(f"Formatting {len(training_chunks)} chunks for training...")
            
            # Create a simplified extraction result for formatting
            simplified_result = {
                'filename': extraction_result['filename'],
                'text': cleaned_text,
                'chunks': training_chunks,
                'extraction_method': extraction_result['extraction_method'],
                'extraction_quality': extraction_result['extraction_quality']
            }
            
            output_format = self.config.get('formatting', {}).get('output_format', 'alpaca')
            training_data = self.formatter.format_for_training(
                [simplified_result],
                output_format=output_format
            )
            
            # Step 6: Insert training examples into database
            batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            inserted = self.db.insert_training_examples(
                training_data,
                doc_id=doc_id,
                batch_name=batch_name
            )
            
            logger.info(f"  Created {len(training_data)} training examples")
            
            # Update document status
            self.db.update_document_status(doc_id, 'completed')
            
            result['success'] = True
            result['training_data'] = training_data

            if output_dir:
                self._save_training_data(
                    training_data,
                    Path(output_dir),
                    pdf_name=Path(pdf_path).stem,
                )
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {str(e)}")
            result['errors'].append(str(e))
            
        return result
    
    def _save_training_data(
        self,
        training_data: List[Dict],
        output_dir: Union[str, Path],
        pdf_name: Optional[str] = None,
    ):
        """Save training data to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = pdf_name or "training"
        
        # Save as JSONL
        jsonl_path = output_path / f"{prefix}_training_data_{timestamp}.jsonl"
        self.formatter.save_to_jsonl(training_data, str(jsonl_path))
        
        # Save statistics
        stats = self.formatter.get_statistics(training_data)
        stats_path = output_path / f"{prefix}_training_stats_{timestamp}.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Saved training data to: {jsonl_path}")
        logger.info(f"Saved statistics to: {stats_path}")
    
    def export_from_database(self, output_path: str, **filters):
        """Export training data from database"""
        logger.info("Exporting training data from database...")
        self.db.export_training_data_to_jsonl(output_path, **filters)
        
        # Validate the exported file
        is_valid, errors = self.formatter.validate_jsonl(output_path)
        
        if is_valid:
            logger.info(f"[OK] Exported data is valid")
        else:
            logger.error(f"[FAIL] Validation errors found:")
            for error in errors[:5]:  # Show first 5 errors
                logger.error(f"  - {error}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Process PDFs for Llama 3.1 fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process PDFs from a directory
  python process_pdfs.py --input-dir /path/to/pdfs --output-dir ./output

  # Process with custom batch size
  python process_pdfs.py --input-dir /path/to/pdfs --batch-size 3

  # Process a single PDF
  python process_pdfs.py --single-pdf /path/to/document.pdf

  # Export from database
  python process_pdfs.py --export-db training_data.jsonl

  # Use custom configuration
  python process_pdfs.py --config config/custom_settings.yaml --input-dir /path/to/pdfs
        """
    )
    
    parser.add_argument('--input-dir', type=str, default=str(DEFAULT_INPUT_DIR),
                       help=f'Directory containing PDF files (default: {DEFAULT_INPUT_DIR})')
    parser.add_argument('--output-dir', type=str, default=str(DEFAULT_OUTPUT_DIR),
                       help=f'Directory for output files (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--single-pdf', type=str,
                       help='Process a single PDF file')
    parser.add_argument('--batch-size', type=int,
                       help='Number of PDFs to process at once')
    parser.add_argument('--config', type=str,
                       help='Path to configuration file')
    parser.add_argument('--export-db', type=str,
                       help='Export training data from database to JSONL')
    parser.add_argument('--db-stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--cleanup-duplicates', action='store_true',
                       help='Remove duplicate training examples from database')
    parser.add_argument('--backup-db', action='store_true',
                       help='Create a backup of the database')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = PDFProcessor(config_path=args.config)
    
    # Handle different operations
    if args.db_stats:
        stats = processor.db.get_statistics()
        print("\nDatabase Statistics:")
        print("=" * 40)
        for key, value in stats.items():
            print(f"{key}: {value}")
            
    elif args.cleanup_duplicates:
        removed = processor.db.cleanup_duplicates()
        print(f"Removed {removed} duplicate training examples")
        
    elif args.backup_db:
        backup_path = processor.db.backup_database()
        print(f"Database backed up to: {backup_path}")
        
    elif args.export_db:
        processor.export_from_database(args.export_db)
        
    elif args.single_pdf:
        single_output_dir = Path(args.output_dir) / Path(args.single_pdf).stem
        result = processor.process_single_pdf(args.single_pdf, single_output_dir)
        if result['success']:
            print(f"Successfully processed: {args.single_pdf}")
            print(f"Training examples created: {len(result['training_data'])}")
        else:
            print(f"Failed to process: {args.single_pdf}")
            for error in result['errors']:
                print(f"  Error: {error}")
                
    elif args.input_dir:
        processor.process_directory(
            args.input_dir,
            args.output_dir,
            args.batch_size
        )
        
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
