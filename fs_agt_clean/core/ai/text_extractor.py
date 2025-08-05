"""
Text Extractor for FlipSync - Free OCR Analysis Component
========================================================

Provides fast, free text extraction using Tesseract OCR.
Part of the scalable multistep vision pipeline that reduces cloud API costs
by 70-80% through local processing.

Features:
- Product text extraction using Tesseract OCR
- Text cleaning and normalization
- Product keyword identification
- <200ms processing time target
- Zero cost local processing
- Multi-language support
"""

import logging
import re
import time
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from PIL import Image, ImageEnhance, ImageFilter

# OCR text extraction
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None

# OpenCV for image preprocessing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

logger = logging.getLogger(__name__)


class TextConfidence(Enum):
    """Text extraction confidence levels."""
    
    HIGH = "high"      # >80% confidence
    MEDIUM = "medium"  # 50-80% confidence
    LOW = "low"        # <50% confidence


@dataclass
class ExtractedText:
    """Result from text extraction."""
    
    text: str
    confidence: float
    bounding_box: Optional[tuple] = None
    language: str = "eng"
    processing_time_ms: float = 0.0


@dataclass
class ProductKeywords:
    """Extracted product keywords with metadata."""
    
    brand_keywords: List[str]
    product_keywords: List[str]
    model_keywords: List[str]
    descriptive_keywords: List[str]
    confidence: float


class TextExtractor:
    """Extract product text using OCR."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize text extractor."""
        self.config = config or {}
        self.max_processing_time_ms = self.config.get("max_processing_time_ms", 200)
        self.enable_preprocessing = self.config.get("enable_preprocessing", True)
        self.languages = self.config.get("languages", ["eng"])
        
        # Common brand names for keyword identification
        self.brand_keywords = {
            "apple", "samsung", "sony", "lg", "microsoft", "google", "amazon",
            "nike", "adidas", "canon", "nikon", "hp", "dell", "lenovo",
            "asus", "acer", "intel", "amd", "nvidia", "logitech", "razer"
        }
        
        # Product category keywords
        self.product_categories = {
            "electronics": {"phone", "laptop", "tablet", "camera", "headphones", "speaker"},
            "clothing": {"shirt", "pants", "dress", "shoes", "jacket", "hat"},
            "books": {"book", "novel", "guide", "manual", "textbook"},
            "home": {"furniture", "decor", "kitchen", "bathroom", "storage"}
        }
        
        # Performance tracking
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "languages_detected": {},
        }
        
        if not OCR_AVAILABLE:
            logger.warning("pytesseract not available - text extraction disabled")
    
    def extract_product_text(self, image: Image.Image) -> List[str]:
        """
        Extract product names and models from image.
        
        Args:
            image: PIL Image to process
            
        Returns:
            List of extracted text strings
        """
        extracted = self.extract_text_detailed(image)
        return [item.text for item in extracted if item.confidence > 0.5]
    
    def extract_text_detailed(self, image: Image.Image) -> List[ExtractedText]:
        """
        Extract text with detailed confidence and metadata.
        
        Args:
            image: PIL Image to process
            
        Returns:
            List of ExtractedText objects
        """
        start_time = time.perf_counter()
        self.stats["total_extractions"] += 1
        
        if not OCR_AVAILABLE:
            logger.error("pytesseract not available for text extraction")
            return []
        
        try:
            # Preprocess image if enabled
            processed_image = image
            if self.enable_preprocessing:
                processed_image = self._preprocess_image(image)
            
            # Configure Tesseract
            lang_string = "+".join(self.languages)
            config = "--oem 3 --psm 6"  # Use LSTM OCR Engine with uniform text block
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(
                processed_image, 
                lang=lang_string, 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            results = []
            current_line = []
            current_confidence = []
            
            # Process OCR results
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if text and confidence > 0:
                    # Group words into lines
                    if data['line_num'][i] != data['line_num'][i-1] if i > 0 else True:
                        # Process previous line
                        if current_line:
                            line_text = " ".join(current_line)
                            avg_confidence = sum(current_confidence) / len(current_confidence)
                            
                            if self._is_product_relevant(line_text):
                                processing_time = (time.perf_counter() - start_time) * 1000
                                
                                extracted = ExtractedText(
                                    text=line_text,
                                    confidence=avg_confidence / 100.0,  # Convert to 0-1 scale
                                    bounding_box=(
                                        data['left'][i], data['top'][i],
                                        data['width'][i], data['height'][i]
                                    ),
                                    language=lang_string,
                                    processing_time_ms=processing_time
                                )
                                
                                results.append(extracted)
                        
                        # Start new line
                        current_line = [text]
                        current_confidence = [confidence]
                    else:
                        current_line.append(text)
                        current_confidence.append(confidence)
            
            # Process final line
            if current_line:
                line_text = " ".join(current_line)
                avg_confidence = sum(current_confidence) / len(current_confidence)
                
                if self._is_product_relevant(line_text):
                    processing_time = (time.perf_counter() - start_time) * 1000
                    
                    extracted = ExtractedText(
                        text=line_text,
                        confidence=avg_confidence / 100.0,
                        language=lang_string,
                        processing_time_ms=processing_time
                    )
                    
                    results.append(extracted)
            
            # Update stats
            processing_time = (time.perf_counter() - start_time) * 1000
            if results:
                self.stats["successful_extractions"] += 1
                avg_conf = sum(r.confidence for r in results) / len(results)
                self._update_average_confidence(avg_conf)
            
            self._update_average_processing_time(processing_time)
            
            logger.debug(f"Text extraction completed: {len(results)} items in {processing_time:.1f}ms")
            
            return results
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Text extraction failed: {e}")
            self._update_average_processing_time(processing_time)
            return []
    
    def extract_product_keywords(self, image: Image.Image) -> ProductKeywords:
        """
        Extract and categorize product keywords.
        
        Args:
            image: PIL Image to process
            
        Returns:
            ProductKeywords object with categorized keywords
        """
        extracted_texts = self.extract_text_detailed(image)
        
        brand_keywords = []
        product_keywords = []
        model_keywords = []
        descriptive_keywords = []
        
        for item in extracted_texts:
            words = self.clean_extracted_text(item.text).lower().split()
            
            for word in words:
                # Check for brand keywords
                if word in self.brand_keywords:
                    brand_keywords.append(word)
                
                # Check for product category keywords
                for category, keywords in self.product_categories.items():
                    if word in keywords:
                        product_keywords.append(word)
                
                # Check for model numbers (alphanumeric patterns)
                if re.match(r'^[A-Z0-9\-]{3,}$', word.upper()):
                    model_keywords.append(word)
                
                # Add other descriptive words
                if len(word) > 2 and word.isalpha():
                    descriptive_keywords.append(word)
        
        # Remove duplicates and calculate confidence
        brand_keywords = list(set(brand_keywords))
        product_keywords = list(set(product_keywords))
        model_keywords = list(set(model_keywords))
        descriptive_keywords = list(set(descriptive_keywords))
        
        # Calculate overall confidence based on keyword quality
        confidence = self._calculate_keyword_confidence(
            brand_keywords, product_keywords, model_keywords, descriptive_keywords
        )
        
        return ProductKeywords(
            brand_keywords=brand_keywords,
            product_keywords=product_keywords,
            model_keywords=model_keywords,
            descriptive_keywords=descriptive_keywords,
            confidence=confidence
        )
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text for search.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text string
        """
        # Remove special characters and extra whitespace
        cleaned = re.sub(r'[^\w\s\-]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Remove very short words (likely OCR errors)
        words = [word for word in cleaned.split() if len(word) > 1]
        
        return " ".join(words)
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: Input PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def _is_product_relevant(self, text: str) -> bool:
        """Check if extracted text is relevant for product identification."""
        if len(text.strip()) < 3:
            return False
        
        # Filter out common OCR noise
        noise_patterns = [
            r'^\d+$',  # Pure numbers
            r'^[^\w\s]+$',  # Only special characters
            r'^.{1,2}$',  # Very short strings
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text.strip()):
                return False
        
        return True
    
    def _calculate_keyword_confidence(self, brand_kw: List[str], product_kw: List[str], 
                                    model_kw: List[str], desc_kw: List[str]) -> float:
        """Calculate confidence score for extracted keywords."""
        base_confidence = 0.5
        
        # Boost confidence based on keyword types found
        if brand_kw:
            base_confidence += 0.3
        if product_kw:
            base_confidence += 0.2
        if model_kw:
            base_confidence += 0.2
        if len(desc_kw) >= 3:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time statistics."""
        total = self.stats["total_extractions"]
        current_avg = self.stats["average_processing_time"]
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.stats["average_processing_time"] = new_avg
    
    def _update_average_confidence(self, confidence: float):
        """Update average confidence statistics."""
        total = self.stats["successful_extractions"]
        current_avg = self.stats["average_confidence"]
        new_avg = ((current_avg * (total - 1)) + confidence) / total
        self.stats["average_confidence"] = new_avg
    
    def get_stats(self) -> dict:
        """Get text extraction statistics."""
        total = self.stats["total_extractions"]
        success_rate = (
            self.stats["successful_extractions"] / total if total > 0 else 0.0
        )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "ocr_available": OCR_AVAILABLE,
            "preprocessing_enabled": self.enable_preprocessing,
            "languages_configured": self.languages,
        }
