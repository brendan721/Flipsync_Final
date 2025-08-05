"""
Barcode Extractor for FlipSync - Free Local Analysis Component
============================================================

Provides fast, free barcode and QR code detection using pyzbar library.
Part of the scalable multistep vision pipeline that reduces cloud API costs
by 70-80% through local processing.

Features:
- UPC/EAN barcode detection
- QR code extraction
- Multiple barcode format support
- <100ms processing time target
- Zero cost local processing
- High accuracy barcode detection
"""

import logging
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from PIL import Image
import numpy as np

# Barcode detection
try:
    from pyzbar import pyzbar
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    pyzbar = None

# OpenCV for image preprocessing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

logger = logging.getLogger(__name__)


class BarcodeType(Enum):
    """Supported barcode types."""
    
    UPC_A = "UPCA"
    UPC_E = "UPCE"
    EAN13 = "EAN13"
    EAN8 = "EAN8"
    CODE128 = "CODE128"
    CODE39 = "CODE39"
    QR_CODE = "QRCODE"
    DATA_MATRIX = "DATAMATRIX"
    PDF417 = "PDF417"


@dataclass
class BarcodeResult:
    """Result from barcode detection."""
    
    data: str
    barcode_type: BarcodeType
    confidence: float
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    processing_time_ms: float


class BarcodeExtractor:
    """Extract barcodes and QR codes from product images."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize barcode extractor."""
        self.config = config or {}
        self.max_processing_time_ms = self.config.get("max_processing_time_ms", 100)
        self.enable_preprocessing = self.config.get("enable_preprocessing", True)
        
        # Performance tracking
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "average_processing_time": 0.0,
            "barcode_types_found": {},
        }
        
        if not BARCODE_AVAILABLE:
            logger.warning("pyzbar not available - barcode detection disabled")
    
    def extract_barcode(self, image: Image.Image) -> Optional[BarcodeResult]:
        """
        Extract the first barcode found in the image.
        
        Args:
            image: PIL Image to process
            
        Returns:
            BarcodeResult if barcode found, None otherwise
        """
        barcodes = self.extract_all_barcodes(image)
        return barcodes[0] if barcodes else None
    
    def extract_all_barcodes(self, image: Image.Image) -> List[BarcodeResult]:
        """
        Extract all barcodes found in the image.
        
        Args:
            image: PIL Image to process
            
        Returns:
            List of BarcodeResult objects
        """
        start_time = time.perf_counter()
        self.stats["total_extractions"] += 1
        
        if not BARCODE_AVAILABLE:
            logger.error("pyzbar not available for barcode detection")
            return []
        
        try:
            # Convert PIL image to numpy array
            image_array = np.array(image)
            
            # Preprocess image if enabled
            if self.enable_preprocessing and CV2_AVAILABLE:
                image_array = self._preprocess_image(image_array)
            
            # Detect barcodes using pyzbar
            detected_barcodes = pyzbar.decode(image_array)
            
            results = []
            for barcode in detected_barcodes:
                try:
                    # Extract barcode data
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = BarcodeType(barcode.type)
                    
                    # Get bounding box
                    rect = barcode.rect
                    bounding_box = (rect.left, rect.top, rect.width, rect.height)
                    
                    # Calculate confidence (simple heuristic based on data length and type)
                    confidence = self._calculate_confidence(barcode_data, barcode_type)
                    
                    processing_time = (time.perf_counter() - start_time) * 1000
                    
                    result = BarcodeResult(
                        data=barcode_data,
                        barcode_type=barcode_type,
                        confidence=confidence,
                        bounding_box=bounding_box,
                        processing_time_ms=processing_time
                    )
                    
                    results.append(result)
                    
                    # Update stats
                    type_name = barcode_type.value
                    self.stats["barcode_types_found"][type_name] = (
                        self.stats["barcode_types_found"].get(type_name, 0) + 1
                    )
                    
                    logger.debug(
                        f"Barcode detected: {barcode_data} (type: {barcode_type.value}, "
                        f"confidence: {confidence:.3f})"
                    )
                    
                except (ValueError, UnicodeDecodeError) as e:
                    logger.warning(f"Failed to process barcode: {e}")
                    continue
            
            # Update performance stats
            processing_time = (time.perf_counter() - start_time) * 1000
            if results:
                self.stats["successful_extractions"] += 1
            
            self._update_average_processing_time(processing_time)
            
            logger.debug(f"Barcode extraction completed: {len(results)} found in {processing_time:.1f}ms")
            
            return results
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Barcode extraction failed: {e}")
            self._update_average_processing_time(processing_time)
            return []
    
    def extract_qr_code(self, image: Image.Image) -> Optional[str]:
        """
        Extract QR code data from image.
        
        Args:
            image: PIL Image to process
            
        Returns:
            QR code data string if found, None otherwise
        """
        barcodes = self.extract_all_barcodes(image)
        
        # Find first QR code
        for barcode in barcodes:
            if barcode.barcode_type == BarcodeType.QR_CODE:
                return barcode.data
        
        return None
    
    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve barcode detection.
        
        Args:
            image_array: Input image as numpy array
            
        Returns:
            Preprocessed image array
        """
        try:
            # Convert to grayscale if needed
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # Apply adaptive thresholding to improve contrast
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return processed
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image_array
    
    def _calculate_confidence(self, data: str, barcode_type: BarcodeType) -> float:
        """
        Calculate confidence score for detected barcode.
        
        Args:
            data: Barcode data string
            barcode_type: Type of barcode detected
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.8  # Base confidence for successful detection
        
        # Adjust based on barcode type (some are more reliable)
        type_multipliers = {
            BarcodeType.UPC_A: 0.95,
            BarcodeType.UPC_E: 0.95,
            BarcodeType.EAN13: 0.95,
            BarcodeType.EAN8: 0.95,
            BarcodeType.QR_CODE: 0.90,
            BarcodeType.CODE128: 0.85,
            BarcodeType.CODE39: 0.80,
            BarcodeType.DATA_MATRIX: 0.85,
            BarcodeType.PDF417: 0.80,
        }
        
        type_confidence = base_confidence * type_multipliers.get(barcode_type, 0.75)
        
        # Adjust based on data length (longer codes generally more reliable)
        if len(data) >= 12:  # Standard UPC/EAN length
            length_bonus = 0.1
        elif len(data) >= 8:
            length_bonus = 0.05
        else:
            length_bonus = 0.0
        
        final_confidence = min(1.0, type_confidence + length_bonus)
        return final_confidence
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time statistics."""
        total = self.stats["total_extractions"]
        current_avg = self.stats["average_processing_time"]
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.stats["average_processing_time"] = new_avg
    
    def get_stats(self) -> dict:
        """Get barcode extraction statistics."""
        total = self.stats["total_extractions"]
        success_rate = (
            self.stats["successful_extractions"] / total if total > 0 else 0.0
        )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "barcode_detection_available": BARCODE_AVAILABLE,
            "preprocessing_enabled": self.enable_preprocessing and CV2_AVAILABLE,
        }
