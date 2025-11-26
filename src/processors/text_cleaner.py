"""
Text Cleaning Module
Handles text preprocessing and cleaning for domain-specific content
"""

import re
import string
import unicodedata
from typing import List, Dict, Optional, Set
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Advanced text cleaning for domain-specific PDF content
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize text cleaner with configuration
        
        Args:
            config: Dictionary with cleaning settings
        """
        self.config = config or {}
        
        # Domain-specific terms to preserve (loaded from config)
        self.preserve_terms = set(self.config.get('preserve_terms', []))
        
        # Common artifacts from PDF extraction
        self.pdf_artifacts = [
            r'\s+', # Multiple spaces
            r'\n{3,}', # Multiple newlines
            r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', # Control characters
            r'^\s*Page\s+\d+\s*$', # Page numbers
            r'^\s*\d+\s*$', # Standalone numbers (often page numbers)
        ]
        
        # Academic/technical patterns to preserve
        self.preserve_patterns = [
            r'\b\d+\.\d+\b', # Decimal numbers
            r'\b\d{4}\b', # Years
            r'\b[A-Z]{2,}\b', # Acronyms
            r'\$[\d,]+\.?\d*', # Currency
            r'\d+%', # Percentages
            r'\b\w+@\w+\.\w+\b', # Emails
            r'https?://[^\s]+', # URLs
            r'\b\d+[a-zA-Z]+\b', # Measurements (e.g., 10kg)
            r'[A-Za-z]+\d+', # Alphanumeric codes
        ]
    
    def clean_text(self, text: str, preserve_structure: bool = True) -> str:
        """
        Clean extracted text while preserving domain-specific content
        
        Args:
            text: Raw extracted text
            preserve_structure: Whether to preserve paragraph structure
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        original_length = len(text)
        
        # Step 1: Normalize unicode and encoding
        text = self._normalize_unicode(text)
        
        # Step 2: Remove PDF-specific artifacts
        text = self._remove_pdf_artifacts(text)
        
        # Step 3: Fix common OCR errors (if applicable)
        text = self._fix_ocr_errors(text)
        
        # Step 4: Handle hyphenation
        text = self._fix_hyphenation(text)
        
        # Step 5: Clean whitespace
        text = self._clean_whitespace(text, preserve_structure)
        
        # Step 6: Remove headers/footers
        text = self._remove_headers_footers(text)
        
        # Step 7: Normalize punctuation
        text = self._normalize_punctuation(text)
        
        # Step 8: Domain-specific cleaning
        text = self._domain_specific_cleaning(text)
        
        # Step 9: Final validation
        text = self._validate_cleaned_text(text)
        
        # Log cleaning statistics
        final_length = len(text)
        reduction_pct = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
        logger.debug(f"Text cleaned: {original_length} -> {final_length} chars ({reduction_pct:.1f}% reduction)")
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        # Normalize to NFKD form
        text = unicodedata.normalize('NFKD', text)
        
        # Replace common unicode issues
        replacements = {
            '\u2018': "'", '\u2019': "'", # Smart quotes
            '\u201c': '"', '\u201d': '"',
            '\u2013': '-', '\u2014': '--', # Dashes
            '\u2026': '...', # Ellipsis
            '\xa0': ' ', # Non-breaking space
            '\u200b': '', # Zero-width space
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text
    
    def _remove_pdf_artifacts(self, text: str) -> str:
        """Remove common PDF extraction artifacts"""
        for pattern in self.pdf_artifacts:
            if pattern == r'\s+':
                # Special handling for multiple spaces
                text = re.sub(pattern, ' ', text)
            elif pattern == r'\n{3,}':
                # Preserve paragraph breaks but remove excessive newlines
                text = re.sub(pattern, '\n\n', text)
            else:
                text = re.sub(pattern, '', text, flags=re.MULTILINE)
                
        return text
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR recognition errors"""
        # Common OCR substitutions
        ocr_fixes = {
            r'\bl\b': 'I', # Lowercase L mistaken for uppercase I
            r'0(?=[a-zA-Z])': 'O', # Zero before letters
            r'(?<=[a-zA-Z])0': 'O', # Zero after letters
            r'\brn\b': 'm', # rn mistaken for m
            r'\bcl\b': 'd', # cl mistaken for d
        }
        
        # Apply fixes carefully to avoid over-correction
        for pattern, replacement in ocr_fixes.items():
            # Only apply if confidence is high (context-dependent)
            if self.config.get('aggressive_ocr_fixing', False):
                text = re.sub(pattern, replacement, text)
                
        return text
    
    def _fix_hyphenation(self, text: str) -> str:
        """Fix word hyphenation at line breaks"""
        # Pattern: word-\n continuation
        hyphen_pattern = r'(\w+)-\n(\w+)'
        
        def hyphen_replacer(match):
            part1, part2 = match.groups()
            combined = part1 + part2
            
            # Check if the unhyphenated word looks valid
            # (You could use a dictionary check here)
            if len(combined) < 20:  # Reasonable word length
                return combined
            else:
                return match.group(0)  # Keep original
                
        text = re.sub(hyphen_pattern, hyphen_replacer, text)
        return text
    
    def _clean_whitespace(self, text: str, preserve_structure: bool) -> str:
        """Clean and normalize whitespace"""
        if preserve_structure:
            # Preserve paragraph structure
            paragraphs = text.split('\n\n')
            cleaned_paragraphs = []
            
            for para in paragraphs:
                # Clean whitespace within paragraph
                para = ' '.join(para.split())
                if para:  # Only keep non-empty paragraphs
                    cleaned_paragraphs.append(para)
                    
            text = '\n\n'.join(cleaned_paragraphs)
        else:
            # Aggressive whitespace cleaning
            text = ' '.join(text.split())
            
        return text
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove repeated headers and footers"""
        lines = text.split('\n')
        
        if len(lines) < 10:
            return text
            
        # Detect repeated lines (likely headers/footers)
        line_counts = Counter(lines)
        repeated_lines = {line for line, count in line_counts.items() 
                         if count > 3 and len(line) < 100}
        
        # Filter out repeated lines
        filtered_lines = []
        for line in lines:
            if line not in repeated_lines or not line.strip():
                filtered_lines.append(line)
                
        return '\n'.join(filtered_lines)
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation spacing"""
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Remove space before
        text = re.sub(r'([.,!?;:])(?=[a-zA-Z])', r'\1 ', text)  # Add space after
        
        # Fix multiple punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        return text
    
    def _domain_specific_cleaning(self, text: str) -> str:
        """Apply domain-specific cleaning rules"""
        # Preserve important patterns
        preserved_segments = []
        
        for pattern in self.preserve_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                preserved_segments.append((match.start(), match.end(), match.group()))
        
        # Sort by position
        preserved_segments.sort(key=lambda x: x[0])
        
        # Additional domain-specific rules from config
        if self.config.get('remove_citations', False):
            # Remove citation brackets [1], [2,3], etc.
            text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
            
        if self.config.get('remove_equations', False):
            # Remove LaTeX equations
            text = re.sub(r'\$[^$]+\$', '[EQUATION]', text)
            text = re.sub(r'\\\[[^\]]+\\\]', '[EQUATION]', text)
            
        return text
    
    def _validate_cleaned_text(self, text: str) -> str:
        """Final validation and quality checks"""
        # Remove any remaining control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        
        # Check minimum length
        min_length = self.config.get('min_text_length', 50)
        if len(text) < min_length:
            logger.warning(f"Cleaned text below minimum length: {len(text)} < {min_length}")
            
        return text
    
    def clean_for_training(self, text: str, max_length: int = 2048) -> List[str]:
        """
        Clean and prepare text specifically for training
        
        Args:
            text: Cleaned text
            max_length: Maximum chunk length for training
            
        Returns:
            List of text chunks ready for training
        """
        # First apply general cleaning
        text = self.clean_text(text)
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Group into chunks
        chunks = self._create_chunks(sentences, max_length)
        
        # Filter chunks
        valid_chunks = []
        for chunk in chunks:
            if self._is_valid_training_chunk(chunk):
                valid_chunks.append(chunk)
                
        return valid_chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter (can be improved with NLTK or spaCy)
        sentence_endings = re.compile(r'[.!?]+[\s\n]+')
        sentences = sentence_endings.split(text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _create_chunks(self, sentences: List[str], max_length: int) -> List[str]:
        """Create training chunks from sentences"""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > max_length and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
                
        # Add last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
    
    def _is_valid_training_chunk(self, chunk: str) -> bool:
        """Validate if chunk is suitable for training"""
        # Check minimum length
        if len(chunk) < self.config.get('min_chunk_length', 100):
            return False
            
        # Check word count
        word_count = len(chunk.split())
        if word_count < self.config.get('min_word_count', 20):
            return False
            
        # Check for meaningful content (not just numbers or symbols)
        alpha_ratio = sum(1 for c in chunk if c.isalpha()) / len(chunk)
        if alpha_ratio < 0.5:
            return False
            
        return True
    
    def get_statistics(self, text: str) -> Dict:
        """Get text statistics for quality assessment"""
        words = text.split()
        sentences = self._split_sentences(text)
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(words)),
            'vocabulary_diversity': len(set(words)) / len(words) if words else 0,
        }