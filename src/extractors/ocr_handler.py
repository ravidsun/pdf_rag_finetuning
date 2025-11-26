"""
OCR Handler Module
Handles optical character recognition for scanned PDFs
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import os

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRHandler:
    """
    Handle OCR extraction for scanned PDFs
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize OCR handler
        
        Args:
            config: Dictionary with OCR settings
        """
        if not OCR_AVAILABLE:
            raise ImportError("OCR libraries not installed. Install with: pip install pytesseract pdf2image Pillow")
            
        self.config = config or {}
        
        # Set Tesseract path if provided
        tesseract_path = os.getenv('TESSERACT_PATH')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        # OCR settings
        self.dpi = self.config.get('ocr_dpi', 300)
        self.language = self.config.get('ocr_language', 'eng')
        self.timeout = self.config.get('ocr_timeout', 30)
        
    def extract_with_ocr(self, pdf_path: Path) -> Dict:
        """
        Extract text from PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Starting OCR extraction for {pdf_path.name}")
        
        result = {
            'filename': pdf_path.name,
            'filepath': str(pdf_path),
            'extraction_method': 'ocr',
            'text': '',
            'pages': [],
            'errors': []
        }
        
        try:
            # Convert PDF to images
            logger.debug(f"Converting PDF to images at {self.dpi} DPI")
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                thread_count=2,
                grayscale=True,  # Better OCR results
                fmt='png'
            )
            
            text_parts = []
            pages = []
            
            for i, image in enumerate(images):
                page_num = i + 1
                logger.debug(f"Processing page {page_num}/{len(images)}")
                
                # Preprocess image
                processed_image = self._preprocess_image(image)
                
                # Extract text with OCR
                try:
                    page_text = pytesseract.image_to_string(
                        processed_image,
                        lang=self.language,
                        timeout=self.timeout,
                        config='--oem 3 --psm 6'  # Best accuracy mode
                    )
                    
                    text_parts.append(page_text)
                    pages.append({
                        'page_num': page_num,
                        'text': page_text,
                        'char_count': len(page_text),
                        'word_count': len(page_text.split())
                    })
                    
                except pytesseract.TesseractError as e:
                    error_msg = f"OCR failed for page {page_num}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
                    pages.append({
                        'page_num': page_num,
                        'text': '',
                        'error': str(e)
                    })
                    
            result['text'] = '\n'.join(text_parts)
            result['pages'] = pages
            
            logger.info(f"OCR extraction completed: {len(result['text'])} characters extracted")
            
        except Exception as e:
            error_msg = f"OCR extraction failed: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            result['extraction_failed'] = True
            
        return result
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Processed PIL Image
        """
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
            
        # Apply threshold to get binary image
        threshold = 128
        image = image.point(lambda x: 0 if x < threshold else 255, '1')
        
        # Additional preprocessing based on config
        if self.config.get('enhance_contrast', True):
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
        if self.config.get('denoise', False):
            # Simple denoising (requires additional libraries for advanced methods)
            pass
            
        return image
    
    def extract_with_confidence(self, pdf_path: Path) -> Dict:
        """
        Extract text with confidence scores
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and confidence scores
        """
        result = self.extract_with_ocr(pdf_path)
        
        if not result.get('extraction_failed'):
            # Get detailed OCR data with confidence scores
            try:
                images = convert_from_path(pdf_path, dpi=self.dpi)
                
                confidence_scores = []
                for image in images:
                    data = pytesseract.image_to_data(
                        image,
                        lang=self.language,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Calculate average confidence for non-empty text
                    confidences = [
                        int(conf) for conf, text in zip(data['conf'], data['text'])
                        if int(conf) > 0 and text.strip()
                    ]
                    
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        confidence_scores.append(avg_confidence)
                        
                if confidence_scores:
                    result['avg_confidence'] = sum(confidence_scores) / len(confidence_scores)
                    result['min_confidence'] = min(confidence_scores)
                    result['max_confidence'] = max(confidence_scores)
                    
            except Exception as e:
                logger.warning(f"Could not calculate confidence scores: {e}")
                
        return result
    
    def check_if_scanned(self, pdf_path: Path) -> bool:
        """
        Check if PDF is scanned (image-based)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF appears to be scanned
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            
            # Check first few pages
            pages_to_check = min(3, len(doc))
            text_length = 0
            
            for i in range(pages_to_check):
                page = doc[i]
                text = page.get_text()
                text_length += len(text.strip())
                
            doc.close()
            
            # If very little text extracted, likely scanned
            avg_text_per_page = text_length / pages_to_check if pages_to_check > 0 else 0
            
            # Threshold for determining if scanned
            is_scanned = avg_text_per_page < 100
            
            return is_scanned
            
        except Exception as e:
            logger.error(f"Error checking if PDF is scanned: {e}")
            return False
    
    def get_ocr_languages(self) -> List[str]:
        """
        Get list of available OCR languages
        
        Returns:
            List of language codes
        """
        try:
            languages = pytesseract.get_languages()
            return languages
        except Exception as e:
            logger.error(f"Could not get OCR languages: {e}")
            return ['eng']  # Default to English
    
    def validate_ocr_setup(self) -> Dict:
        """
        Validate OCR setup and dependencies
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'ocr_available': OCR_AVAILABLE,
            'tesseract_installed': False,
            'tesseract_version': None,
            'languages': [],
            'errors': []
        }
        
        if not OCR_AVAILABLE:
            validation['errors'].append("OCR libraries not installed")
            return validation
            
        try:
            # Check Tesseract installation
            version = pytesseract.get_tesseract_version()
            validation['tesseract_installed'] = True
            validation['tesseract_version'] = str(version)
            
            # Get available languages
            validation['languages'] = self.get_ocr_languages()
            
        except Exception as e:
            validation['errors'].append(f"Tesseract not properly installed: {e}")
            
        return validation


# Utility function for quick OCR checks
def is_ocr_available() -> bool:
    """Check if OCR functionality is available"""
    return OCR_AVAILABLE


def quick_ocr_extract(pdf_path: str, pages: Optional[List[int]] = None) -> str:
    """
    Quick OCR extraction for specific pages
    
    Args:
        pdf_path: Path to PDF file
        pages: List of page numbers to extract (1-indexed)
        
    Returns:
        Extracted text
    """
    if not OCR_AVAILABLE:
        raise ImportError("OCR not available")
        
    handler = OCRHandler()
    
    if pages:
        # Extract specific pages only
        images = convert_from_path(pdf_path, dpi=200, first_page=min(pages), last_page=max(pages))
        text_parts = []
        
        for i, page_num in enumerate(pages):
            if i < len(images):
                text = pytesseract.image_to_string(images[i])
                text_parts.append(f"Page {page_num}:\n{text}")
                
        return '\n\n'.join(text_parts)
    else:
        # Extract all pages
        result = handler.extract_with_ocr(Path(pdf_path))
        return result.get('text', '')