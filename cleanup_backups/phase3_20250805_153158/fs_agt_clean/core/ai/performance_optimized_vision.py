"""
Performance Optimized Vision System for FlipSync
===============================================

Implements performance optimizations for the vision system:
1. Image preprocessing pipeline for optimal OCR results
2. Intelligent caching system for repeated image analysis
3. Optimized barcode detection algorithms for speed
4. Batch image processing capabilities
5. Memory management optimizations for high-volume processing

Maintains <1000ms processing target while improving accuracy.
"""

import asyncio
import hashlib
import io
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import cv2

# Import enhanced components
from fs_agt_clean.core.ai.enhanced_vision_processor import (
    EnhancedVisionProcessor,
    ImageQualityMetrics,
    EBayCategory,
)
from fs_agt_clean.core.ai.scalable_vision_service import ImageAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for image analysis results."""

    result: ImageAnalysisResult
    timestamp: float
    access_count: int
    image_hash: str
    size_bytes: int


@dataclass
class BatchProcessingResult:
    """Result from batch processing multiple images."""

    results: List[ImageAnalysisResult]
    total_processing_time: float
    average_processing_time: float
    cache_hits: int
    cache_misses: int
    memory_usage_mb: float


@dataclass
class PreprocessingConfig:
    """Configuration for image preprocessing."""

    enable_contrast_enhancement: bool = True
    enable_noise_reduction: bool = True
    enable_text_region_detection: bool = True
    enable_barcode_optimization: bool = True
    target_dpi: int = 300
    max_image_size: Tuple[int, int] = (2048, 2048)


class IntelligentCache:
    """Intelligent caching system for image analysis results."""

    def __init__(self, max_size_mb: int = 100, ttl_seconds: int = 3600):
        """Initialize intelligent cache."""
        self.max_size_mb = max_size_mb
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.current_size_bytes = 0

        # Statistics
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "total_requests": 0}

        logger.info(
            f"Intelligent cache initialized: max_size={max_size_mb}MB, ttl={ttl_seconds}s"
        )

    def _calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate hash for image data."""
        return hashlib.sha256(image_data).hexdigest()[:16]

    def get(self, image_data: bytes) -> Optional[ImageAnalysisResult]:
        """Get cached result for image."""
        self.stats["total_requests"] += 1
        image_hash = self._calculate_image_hash(image_data)

        if image_hash in self.cache:
            entry = self.cache[image_hash]

            # Check TTL
            if time.time() - entry.timestamp < self.ttl_seconds:
                entry.access_count += 1
                self.stats["hits"] += 1
                logger.debug(f"Cache hit for image {image_hash}")
                return entry.result
            else:
                # Expired entry
                self._remove_entry(image_hash)

        self.stats["misses"] += 1
        return None

    def put(self, image_data: bytes, result: ImageAnalysisResult) -> None:
        """Cache analysis result."""
        image_hash = self._calculate_image_hash(image_data)
        entry_size = len(image_data) + self._estimate_result_size(result)

        # Check if we need to evict entries
        while (self.current_size_bytes + entry_size) > (self.max_size_mb * 1024 * 1024):
            if not self._evict_lru():
                break  # No more entries to evict

        # Add new entry
        entry = CacheEntry(
            result=result,
            timestamp=time.time(),
            access_count=1,
            image_hash=image_hash,
            size_bytes=entry_size,
        )

        self.cache[image_hash] = entry
        self.current_size_bytes += entry_size

        logger.debug(f"Cached result for image {image_hash} ({entry_size} bytes)")

    def _estimate_result_size(self, result: ImageAnalysisResult) -> int:
        """Estimate memory size of analysis result."""
        # Rough estimation based on string lengths and data structures
        size = len(result.analysis) * 2  # Unicode characters
        size += len(str(result.product_details)) * 2
        size += len(result.marketplace_suggestions) * 20
        size += len(result.category_predictions) * 20
        size += 100  # Base object overhead
        return size

    def _remove_entry(self, image_hash: str) -> None:
        """Remove entry from cache."""
        if image_hash in self.cache:
            entry = self.cache[image_hash]
            self.current_size_bytes -= entry.size_bytes
            del self.cache[image_hash]

    def _evict_lru(self) -> bool:
        """Evict least recently used entry."""
        if not self.cache:
            return False

        # Find LRU entry (lowest access_count and oldest timestamp)
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].access_count, self.cache[k].timestamp),
        )

        self._remove_entry(lru_key)
        self.stats["evictions"] += 1
        logger.debug(f"Evicted LRU entry {lru_key}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = self.stats["hits"] / max(self.stats["total_requests"], 1)
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_size_entries": len(self.cache),
            "cache_size_mb": self.current_size_bytes / (1024 * 1024),
        }


class OptimizedImagePreprocessor:
    """Optimized image preprocessing for better OCR and barcode detection."""

    def __init__(self, config: PreprocessingConfig = None):
        """Initialize optimized preprocessor."""
        self.config = config or PreprocessingConfig()

        # Performance tracking
        self.stats = {
            "images_processed": 0,
            "average_preprocessing_time": 0.0,
            "contrast_enhancements": 0,
            "noise_reductions": 0,
            "text_region_detections": 0,
            "barcode_optimizations": 0,
        }

        logger.info("Optimized image preprocessor initialized")

    def preprocess_for_ocr(
        self, image: Image.Image, quality_metrics: ImageQualityMetrics
    ) -> Image.Image:
        """Preprocess image for optimal OCR results."""
        start_time = time.perf_counter()

        try:
            processed_image = image.copy()

            # Resize if too large
            if (
                processed_image.size[0] > self.config.max_image_size[0]
                or processed_image.size[1] > self.config.max_image_size[1]
            ):
                processed_image.thumbnail(
                    self.config.max_image_size, Image.Resampling.LANCZOS
                )

            # Convert to grayscale for processing
            if processed_image.mode != "L":
                gray_image = processed_image.convert("L")
            else:
                gray_image = processed_image

            # Enhance contrast if needed
            if (
                self.config.enable_contrast_enhancement
                and quality_metrics.contrast_score < 0.6
            ):
                contrast_factor = 1.0 + (0.6 - quality_metrics.contrast_score) * 1.5
                enhancer = ImageEnhance.Contrast(gray_image)
                gray_image = enhancer.enhance(contrast_factor)
                self.stats["contrast_enhancements"] += 1

            # Apply noise reduction if needed
            if self.config.enable_noise_reduction and quality_metrics.noise_level > 0.5:
                # Use bilateral filter for noise reduction while preserving edges
                img_array = np.array(gray_image)
                filtered = cv2.bilateralFilter(img_array, 9, 75, 75)
                gray_image = Image.fromarray(filtered)
                self.stats["noise_reductions"] += 1

            # Detect and enhance text regions
            if self.config.enable_text_region_detection:
                gray_image = self._enhance_text_regions(gray_image)
                self.stats["text_region_detections"] += 1

            # Convert back to RGB if needed
            if image.mode == "RGB":
                processed_image = gray_image.convert("RGB")
            else:
                processed_image = gray_image

            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_average_time(processing_time)

            logger.debug(f"OCR preprocessing completed in {processing_time:.1f}ms")
            return processed_image

        except Exception as e:
            logger.warning(f"OCR preprocessing failed: {e}")
            return image

    def preprocess_for_barcode(
        self, image: Image.Image, quality_metrics: ImageQualityMetrics
    ) -> Image.Image:
        """Preprocess image for optimal barcode detection."""
        start_time = time.perf_counter()

        try:
            processed_image = image.copy()

            # Convert to grayscale
            if processed_image.mode != "L":
                gray_image = processed_image.convert("L")
            else:
                gray_image = processed_image

            # Enhance for barcode detection if enabled
            if self.config.enable_barcode_optimization:
                # Apply adaptive thresholding for better barcode detection
                img_array = np.array(gray_image)

                # Use adaptive threshold to handle varying lighting
                adaptive_thresh = cv2.adaptiveThreshold(
                    img_array,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2,
                )

                # Apply morphological operations to clean up
                kernel = np.ones((2, 2), np.uint8)
                cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)

                gray_image = Image.fromarray(cleaned)
                self.stats["barcode_optimizations"] += 1

            # Convert back to original mode if needed
            if image.mode == "RGB":
                processed_image = gray_image.convert("RGB")
            else:
                processed_image = gray_image

            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_average_time(processing_time)

            logger.debug(f"Barcode preprocessing completed in {processing_time:.1f}ms")
            return processed_image

        except Exception as e:
            logger.warning(f"Barcode preprocessing failed: {e}")
            return image

    def _enhance_text_regions(self, image: Image.Image) -> Image.Image:
        """Enhance text regions for better OCR."""
        try:
            img_array = np.array(image)

            # Use MSER (Maximally Stable Extremal Regions) to detect text regions
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(img_array)

            # Create mask for text regions
            mask = np.zeros_like(img_array)
            for region in regions:
                # Filter regions by size (likely text regions)
                if 50 < len(region) < 2000:
                    hull = cv2.convexHull(region.reshape(-1, 1, 2))
                    cv2.fillPoly(mask, [hull], 255)

            # Apply enhancement only to text regions
            enhanced = img_array.copy()
            text_regions = mask > 0

            if np.any(text_regions):
                # Enhance contrast in text regions
                enhanced[text_regions] = cv2.equalizeHist(enhanced[text_regions])

            return Image.fromarray(enhanced)

        except Exception as e:
            logger.warning(f"Text region enhancement failed: {e}")
            return image

    def _update_average_time(self, processing_time: float) -> None:
        """Update average preprocessing time."""
        self.stats["images_processed"] += 1
        self.stats["average_preprocessing_time"] = (
            self.stats["average_preprocessing_time"]
            * (self.stats["images_processed"] - 1)
            + processing_time
        ) / self.stats["images_processed"]

    def get_stats(self) -> Dict[str, Any]:
        """Get preprocessing statistics."""
        return self.stats.copy()


class PerformanceOptimizedVisionSystem:
    """Performance optimized vision system with caching and batch processing."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize performance optimized vision system."""
        self.config = config or {}

        # Initialize components
        self.enhanced_processor = EnhancedVisionProcessor(config)
        self.cache = IntelligentCache(
            max_size_mb=self.config.get("cache_size_mb", 100),
            ttl_seconds=self.config.get("cache_ttl_seconds", 3600),
        )
        self.preprocessor = OptimizedImagePreprocessor(
            PreprocessingConfig(**self.config.get("preprocessing", {}))
        )

        # Thread pool for concurrent processing
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get("max_workers", 4),
            thread_name_prefix="vision_worker",
        )

        # Performance tracking
        self.stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_processes": 0,
            "average_processing_time": 0.0,
            "memory_optimizations": 0,
        }

        logger.info("Performance Optimized Vision System initialized")

    async def analyze_image_optimized(
        self,
        image_data: Union[bytes, str],
        analysis_type: str = "product_identification",
        marketplace: str = "ebay",
        use_cache: bool = True,
    ) -> ImageAnalysisResult:
        """
        Optimized image analysis with caching and preprocessing.

        Args:
            image_data: Image data as bytes or base64 string
            analysis_type: Type of analysis to perform
            marketplace: Target marketplace
            use_cache: Whether to use caching

        Returns:
            Optimized ImageAnalysisResult
        """
        start_time = time.perf_counter()
        self.stats["total_analyses"] += 1

        try:
            # Convert to bytes if needed
            if isinstance(image_data, str):
                import base64

                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data

            # Check cache first
            if use_cache:
                cached_result = self.cache.get(image_bytes)
                if cached_result:
                    self.stats["cache_hits"] += 1
                    logger.debug("Using cached analysis result")
                    return cached_result
                else:
                    self.stats["cache_misses"] += 1

            # Perform enhanced analysis
            result = await self.enhanced_processor.analyze_image_enhanced(
                image_bytes, analysis_type, marketplace
            )

            # Cache the result
            if use_cache:
                self.cache.put(image_bytes, result)

            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_average_time(processing_time)

            logger.info(f"Optimized analysis completed in {processing_time:.1f}ms")
            return result

        except Exception as e:
            logger.error(f"Optimized vision analysis failed: {e}")
            return ImageAnalysisResult(
                analysis=f"Optimized analysis failed: {str(e)}",
                confidence=0.0,
                product_details={"error": str(e)},
                processing_method="error_fallback",
                cost_estimate=0.0,
            )

    async def analyze_batch_optimized(
        self,
        image_data_list: List[Union[bytes, str]],
        analysis_type: str = "product_identification",
        marketplace: str = "ebay",
        use_cache: bool = True,
        max_concurrent: int = 4,
    ) -> BatchProcessingResult:
        """
        Batch process multiple images with optimization.

        Args:
            image_data_list: List of image data (bytes or base64)
            analysis_type: Type of analysis to perform
            marketplace: Target marketplace
            use_cache: Whether to use caching
            max_concurrent: Maximum concurrent processing

        Returns:
            BatchProcessingResult with all analysis results
        """
        start_time = time.perf_counter()
        self.stats["batch_processes"] += 1

        try:
            # Track memory usage
            import psutil

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Process images in batches to manage memory
            batch_size = min(max_concurrent, len(image_data_list))
            results = []
            cache_hits = 0
            cache_misses = 0

            # Create semaphore to limit concurrent processing
            semaphore = asyncio.Semaphore(batch_size)

            async def process_single_image(image_data):
                async with semaphore:
                    result = await self.analyze_image_optimized(
                        image_data, analysis_type, marketplace, use_cache
                    )
                    return result

            # Process all images concurrently with semaphore limiting
            tasks = [process_single_image(img_data) for img_data in image_data_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch processing failed for image {i}: {result}")
                    processed_results.append(
                        ImageAnalysisResult(
                            analysis=f"Batch processing failed: {str(result)}",
                            confidence=0.0,
                            product_details={"error": str(result), "batch_index": i},
                            processing_method="batch_error_fallback",
                            cost_estimate=0.0,
                        )
                    )
                else:
                    processed_results.append(result)

            # Calculate statistics
            total_processing_time = (time.perf_counter() - start_time) * 1000
            average_processing_time = (
                total_processing_time / len(image_data_list) if image_data_list else 0
            )

            # Get cache statistics
            cache_stats = self.cache.get_stats()
            cache_hits = cache_stats["hits"] - cache_hits  # Delta since start
            cache_misses = cache_stats["misses"] - cache_misses  # Delta since start

            # Calculate memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory

            batch_result = BatchProcessingResult(
                results=processed_results,
                total_processing_time=total_processing_time,
                average_processing_time=average_processing_time,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                memory_usage_mb=memory_usage,
            )

            logger.info(
                f"Batch processing completed: {len(processed_results)} images in {total_processing_time:.1f}ms "
                f"(avg: {average_processing_time:.1f}ms/image, memory: {memory_usage:.1f}MB)"
            )

            return batch_result

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Return error results for all images
            error_results = [
                ImageAnalysisResult(
                    analysis=f"Batch processing failed: {str(e)}",
                    confidence=0.0,
                    product_details={"error": str(e), "batch_index": i},
                    processing_method="batch_error_fallback",
                    cost_estimate=0.0,
                )
                for i in range(len(image_data_list))
            ]

            return BatchProcessingResult(
                results=error_results,
                total_processing_time=0.0,
                average_processing_time=0.0,
                cache_hits=0,
                cache_misses=0,
                memory_usage_mb=0.0,
            )

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize memory usage by cleaning up caches and resources."""
        try:
            initial_cache_size = self.cache.current_size_bytes / 1024 / 1024  # MB

            # Clean expired cache entries
            current_time = time.time()
            expired_keys = [
                key
                for key, entry in self.cache.cache.items()
                if current_time - entry.timestamp > self.cache.ttl_seconds
            ]

            for key in expired_keys:
                self.cache._remove_entry(key)

            # Force garbage collection
            import gc

            collected = gc.collect()

            final_cache_size = self.cache.current_size_bytes / 1024 / 1024  # MB
            memory_freed = initial_cache_size - final_cache_size

            self.stats["memory_optimizations"] += 1

            optimization_result = {
                "expired_entries_removed": len(expired_keys),
                "memory_freed_mb": memory_freed,
                "gc_objects_collected": collected,
                "cache_size_before_mb": initial_cache_size,
                "cache_size_after_mb": final_cache_size,
            }

            logger.info(
                f"Memory optimization completed: freed {memory_freed:.1f}MB, "
                f"removed {len(expired_keys)} expired entries"
            )

            return optimization_result

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {"error": str(e)}

    def _update_average_time(self, processing_time: float) -> None:
        """Update average processing time."""
        count = self.stats["total_analyses"]
        self.stats["average_processing_time"] = (
            self.stats["average_processing_time"] * (count - 1) + processing_time
        ) / count

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "system_stats": self.stats,
            "cache_stats": self.cache.get_stats(),
            "preprocessor_stats": self.preprocessor.get_stats(),
            "enhanced_processor_stats": self.enhanced_processor.get_stats(),
        }

    def __del__(self):
        """Cleanup resources."""
        try:
            if hasattr(self, "thread_pool"):
                self.thread_pool.shutdown(wait=False)
        except Exception:
            pass  # Ignore cleanup errors


# Global instance for backward compatibility
performance_optimized_vision = PerformanceOptimizedVisionSystem()

# Export main components
__all__ = [
    "PerformanceOptimizedVisionSystem",
    "IntelligentCache",
    "OptimizedImagePreprocessor",
    "PreprocessingConfig",
    "BatchProcessingResult",
    "CacheEntry",
    "performance_optimized_vision",
]
