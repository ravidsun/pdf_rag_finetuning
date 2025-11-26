"""
PDF Extractor Module
Handles PDF text extraction using multiple methods with fallback options
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib
from datetime import datetime

# PDF processing libraries
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from pdfminer.layout import LAParams

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Comprehensive PDF text extraction with multiple fallback methods
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize PDF extractor with configuration
        
        Args:
            config: Dictionary with extraction settings
        """
        self.config = config or {}
        self.extraction_methods = [
            ('pymupdf', self._extract_with_pymupdf),
            ('pdfplumber', self._extract_with_pdfplumber),
            ('pdfminer', self._extract_with_pdfminer),
            ('pypdf2', self._extract_with_pypdf2),
        ]
        
        # OCR handler will be imported if needed
        self.ocr_handler = None
        
    def extract_text(self, pdf_path: str, method: str = 'auto') -> Dict:
        """
        Extract text from PDF with metadata
        
        Args:
            pdf_path: Path to PDF file
            method: Extraction method or 'auto' for automatic selection
            
        Returns:
            Dictionary with extracted text and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        result = {
            'filename': pdf_path.name,
            'filepath': str(pdf_path),
            'file_size': pdf_path.stat().st_size,
            'extraction_date': datetime.now().isoformat(),
            'file_hash': self._calculate_file_hash(pdf_path),
            'text': '',
            'pages': [],
            'metadata': {},
            'extraction_method': None,
            'extraction_quality': 'unknown',
            'errors': []
        }
        
        # Extract metadata first
        try:
            result['metadata'] = self._extract_metadata(pdf_path)
            result['num_pages'] = result['metadata'].get('num_pages', 0)
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {pdf_path}: {e}")
            result['errors'].append(f"Metadata extraction failed: {str(e)}")
        
        # Try extraction methods
        if method == 'auto':
            text, pages, method_used = self._auto_extract(pdf_path)
        else:
            text, pages, method_used = self._extract_with_method(pdf_path, method)
            
        result['text'] = text
        result['pages'] = pages
        result['extraction_method'] = method_used
        
        # Assess extraction quality
        result['extraction_quality'] = self._assess_quality(text, pages)
        
        # If quality is poor and OCR is available, try OCR
        if result['extraction_quality'] == 'poor' and self.config.get('use_ocr', False):
            logger.info(f"Text extraction quality poor, attempting OCR for {pdf_path}")
            try:
                from .ocr_handler import OCRHandler
                self.ocr_handler = OCRHandler()
                ocr_result = self.ocr_handler.extract_with_ocr(pdf_path)
                if ocr_result and len(ocr_result['text']) > len(result['text']):
                    result.update(ocr_result)
                    result['extraction_method'] = 'ocr'
            except ImportError:
                logger.warning("OCR handler not available")
                result['errors'].append("OCR fallback not available")
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
                result['errors'].append(f"OCR failed: {str(e)}")
                
        return result
    
    def _auto_extract(self, pdf_path: Path) -> Tuple[str, List[Dict], str]:
        """
        Automatically try extraction methods until one succeeds
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (text, pages, method_used)
        """
        for method_name, method_func in self.extraction_methods:
            try:
                logger.debug(f"Trying {method_name} for {pdf_path.name}")
                text, pages = method_func(pdf_path)
                
                # Check if extraction produced meaningful text
                if text and len(text.strip()) > 100:
                    logger.info(f"Successfully extracted {pdf_path.name} using {method_name}")
                    return text, pages, method_name
                    
            except Exception as e:
                logger.debug(f"{method_name} failed for {pdf_path.name}: {e}")
                continue
                
        # If all methods fail, return empty result
        logger.error(f"All extraction methods failed for {pdf_path.name}")
        return "", [], "failed"
    
    def _extract_with_method(self, pdf_path: Path, method: str) -> Tuple[str, List[Dict], str]:
        """
        Extract using a specific method
        
        Args:
            pdf_path: Path to PDF file
            method: Method name
            
        Returns:
            Tuple of (text, pages, method_used)
        """
        method_map = {name: func for name, func in self.extraction_methods}
        
        if method not in method_map:
            raise ValueError(f"Unknown extraction method: {method}")
            
        try:
            text, pages = method_map[method](pdf_path)
            return text, pages, method
        except Exception as e:
            logger.error(f"{method} extraction failed: {e}")
            return "", [], f"{method}_failed"
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
        """Extract text using PyMuPDF"""
        doc = fitz.open(pdf_path)
        text_parts = []
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            text_parts.append(page_text)
            
            pages.append({
                'page_num': page_num + 1,
                'text': page_text,
                'char_count': len(page_text),
                'word_count': len(page_text.split())
            })
            
        doc.close()
        return '\n'.join(text_parts), pages
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
        """Extract text using pdfplumber"""
        text_parts = []
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
                
                # Extract tables if present
                tables = page.extract_tables()
                table_text = ""
                if tables:
                    for table in tables:
                        if table:
                            table_text += self._format_table(table)
                
                full_page_text = page_text + "\n" + table_text if table_text else page_text
                
                pages.append({
                    'page_num': i + 1,
                    'text': full_page_text,
                    'char_count': len(full_page_text),
                    'word_count': len(full_page_text.split()),
                    'has_tables': bool(tables)
                })
                
        return '\n'.join(text_parts), pages
    
    def _extract_with_pdfminer(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
        """Extract text using pdfminer"""
        laparams = LAParams(
            line_overlap=0.5,
            char_margin=2.0,
            word_margin=0.1,
            boxes_flow=0.5,
            detect_vertical=True
        )
        
        text = pdfminer_extract(str(pdf_path), laparams=laparams)
        
        # Simple page splitting based on form feeds
        page_texts = text.split('\f')
        pages = []
        
        for i, page_text in enumerate(page_texts):
            if page_text.strip():
                pages.append({
                    'page_num': i + 1,
                    'text': page_text,
                    'char_count': len(page_text),
                    'word_count': len(page_text.split())
                })
                
        return text, pages
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> Tuple[str, List[Dict]]:
        """Extract text using PyPDF2 (legacy fallback)"""
        text_parts = []
        pages = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text_parts.append(page_text)
                
                pages.append({
                    'page_num': i + 1,
                    'text': page_text,
                    'char_count': len(page_text),
                    'word_count': len(page_text.split())
                })
                
        return '\n'.join(text_parts), pages
    
    def _extract_metadata(self, pdf_path: Path) -> Dict:
        """Extract PDF metadata"""
        metadata = {}
        
        try:
            doc = fitz.open(pdf_path)
            metadata['num_pages'] = len(doc)
            
            # Get document metadata
            pdf_metadata = doc.metadata
            if pdf_metadata:
                metadata.update({
                    'title': pdf_metadata.get('title', ''),
                    'author': pdf_metadata.get('author', ''),
                    'subject': pdf_metadata.get('subject', ''),
                    'keywords': pdf_metadata.get('keywords', ''),
                    'creator': pdf_metadata.get('creator', ''),
                    'producer': pdf_metadata.get('producer', ''),
                    'creation_date': str(pdf_metadata.get('creationDate', '')),
                    'modification_date': str(pdf_metadata.get('modDate', ''))
                })
                
            doc.close()
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            
        return metadata
    
    def _format_table(self, table: List[List]) -> str:
        """Format table data as text"""
        if not table:
            return ""
            
        formatted_rows = []
        for row in table:
            # Filter out None values and convert to strings
            row_values = [str(cell) if cell is not None else "" for cell in row]
            formatted_rows.append(" | ".join(row_values))
            
        return "\n".join(formatted_rows)
    
    def _assess_quality(self, text: str, pages: List[Dict]) -> str:
        """
        Assess extraction quality based on text characteristics
        
        Returns:
            Quality level: 'high', 'medium', 'poor'
        """
        if not text:
            return 'poor'
            
        # Calculate quality metrics
        total_chars = len(text)
        words = text.split()
        total_words = len(words)
        
        if total_words < 50:
            return 'poor'
            
        # Check for common extraction issues
        garbage_chars = re.findall(r'[^\w\s\.\,\!\?\:\;\-\(\)\[\]\{\}\"\'\/]', text)
        garbage_ratio = len(garbage_chars) / total_chars if total_chars > 0 else 1
        
        # Check for reasonable word lengths
        avg_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0
        
        # Determine quality
        if garbage_ratio < 0.05 and 3 <= avg_word_length <= 10 and total_words > 500:
            return 'high'
        elif garbage_ratio < 0.15 and 2 <= avg_word_length <= 15 and total_words > 100:
            return 'medium'
        else:
            return 'poor'
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def batch_extract(self, pdf_paths: List[str], batch_size: int = 5) -> List[Dict]:
        """
        Extract text from multiple PDFs in batches
        
        Args:
            pdf_paths: List of PDF file paths
            batch_size: Number of PDFs to process at once
            
        Returns:
            List of extraction results
        """
        results = []
        total = len(pdf_paths)
        
        for i in range(0, total, batch_size):
            batch = pdf_paths[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} PDFs)")
            
            for pdf_path in batch:
                try:
                    result = self.extract_text(pdf_path)
                    results.append(result)
                    logger.info(f"Extracted: {Path(pdf_path).name} "
                              f"({result['extraction_quality']} quality, "
                              f"{len(result['text'])} chars)")
                except Exception as e:
                    logger.error(f"Failed to extract {pdf_path}: {e}")
                    results.append({
                        'filename': Path(pdf_path).name,
                        'filepath': pdf_path,
                        'error': str(e),
                        'extraction_failed': True
                    })
                    
        return results