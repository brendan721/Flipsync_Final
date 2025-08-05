"""
Enhanced Scalable Vision Service for FlipSync
============================================

Integrates enhanced accuracy tuning and performance optimizations into the
existing ScalableVisionPipeline while maintaining backward compatibility.

Features:
- Enhanced ML-based confidence scoring
- Product-specific analysis templates
- Image quality assessment and adaptive preprocessing
- Intelligent caching system
- Batch processing capabilities
- Memory management optimizations
- Maintains zero LLM dependencies and autonomous architecture
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Union, Any

# Import base components
from fs_agt_clean.core.ai.scalable_vision_service import (
    ScalableVisionPipeline,
    ImageAnalysisResult,
    VisionServiceType
)

# Import enhanced components
from fs_agt_clean.core.ai.enhanced_vision_processor import EnhancedVisionProcessor
from fs_agt_clean.core.ai.performance_optimized_vision import (
    PerformanceOptimizedVisionSystem,
    BatchProcessingResult
)

logger = logging.getLogger(__name__)

class EnhancedScalableVisionPipeline(ScalableVisionPipeline):
    """
    Enhanced version of ScalableVisionPipeline with ML-based accuracy improvements
    and performance optimizations.
    
    Maintains full backward compatibility while providing enhanced capabilities.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize enhanced scalable vision pipeline."""
        super().__init__(config)
        
        # Initialize enhanced components
        self.enhanced_processor = EnhancedVisionProcessor(config)
        self.performance_system = PerformanceOptimizedVisionSystem(config)
        
        # Configuration flags
        self.use_enhanced_processing = config.get("use_enhanced_processing", True) if config else True
        self.use_performance_optimization = config.get("use_performance_optimization", True) if config else True
        self.use_intelligent_caching = config.get("use_intelligent_caching", True) if config else True
        
        # Enhanced statistics
        self.enhanced_stats = {
            "enhanced_analyses": 0,
            "performance_optimized_analyses": 0,
            "confidence_improvements": 0,
            "cache_utilization": 0.0,
            "average_confidence_boost": 0.0,
            "batch_processes": 0
        }
        
        logger.info(f"Enhanced Scalable Vision Pipeline initialized: "
                   f"enhanced_processing={self.use_enhanced_processing}, "
                   f"performance_optimization={self.use_performance_optimization}, "
                   f"intelligent_caching={self.use_intelligent_caching}")
    
    async def analyze_image(
        self,
        image_data: Union[bytes, str],
        analysis_type: str = "product_identification",
        marketplace: str = "ebay",
        additional_context: str = "",
        use_enhanced: bool = None,
        use_cache: bool = None
    ) -> ImageAnalysisResult:
        """
        Enhanced image analysis with backward compatibility.
        
        Args:
            image_data: Image data as bytes or base64 string
            analysis_type: Type of analysis to perform
            marketplace: Target marketplace
            additional_context: Additional context for analysis
            use_enhanced: Override enhanced processing setting
            use_cache: Override caching setting
            
        Returns:
            Enhanced ImageAnalysisResult with improved confidence scores
        """
        start_time = time.perf_counter()
        
        try:
            # Determine processing mode
            enhanced_mode = use_enhanced if use_enhanced is not None else self.use_enhanced_processing
            cache_mode = use_cache if use_cache is not None else self.use_intelligent_caching
            
            if enhanced_mode and self.use_performance_optimization:
                # Use performance optimized system (includes enhanced processing)
                result = await self.performance_system.analyze_image_optimized(
                    image_data=image_data,
                    analysis_type=analysis_type,
                    marketplace=marketplace,
                    use_cache=cache_mode
                )
                
                self.enhanced_stats["performance_optimized_analyses"] += 1
                
                # Track confidence improvements
                if result.confidence > 0.5:  # Baseline was 0.5
                    self.enhanced_stats["confidence_improvements"] += 1
                    confidence_boost = result.confidence - 0.5
                    current_avg = self.enhanced_stats["average_confidence_boost"]
                    count = self.enhanced_stats["confidence_improvements"]
                    self.enhanced_stats["average_confidence_boost"] = (
                        (current_avg * (count - 1) + confidence_boost) / count
                    )
                
            elif enhanced_mode:
                # Use enhanced processing only
                result = await self.enhanced_processor.analyze_image_enhanced(
                    image_data=image_data,
                    analysis_type=analysis_type,
                    marketplace=marketplace
                )
                
                self.enhanced_stats["enhanced_analyses"] += 1
                
            else:
                # Fall back to original processing
                result = await super().analyze_image(
                    image_data=image_data,
                    analysis_type=analysis_type,
                    marketplace=marketplace,
                    additional_context=additional_context
                )
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            # Update result with processing metadata
            if hasattr(result, 'product_details') and result.product_details:
                result.product_details.update({
                    "enhanced_processing_used": enhanced_mode,
                    "performance_optimization_used": self.use_performance_optimization,
                    "caching_used": cache_mode,
                    "total_processing_time_ms": processing_time
                })
            
            logger.info(f"Enhanced analysis completed: confidence={result.confidence:.2f}, "
                       f"processing_time={processing_time:.1f}ms, enhanced={enhanced_mode}")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced vision analysis failed: {e}")
            # Fall back to original implementation
            return await super().analyze_image(
                image_data=image_data,
                analysis_type=analysis_type,
                marketplace=marketplace,
                additional_context=additional_context
            )
    
    async def analyze_batch(
        self,
        image_data_list: List[Union[bytes, str]],
        analysis_type: str = "product_identification",
        marketplace: str = "ebay",
        max_concurrent: int = 4,
        use_cache: bool = None
    ) -> BatchProcessingResult:
        """
        Batch process multiple images with enhanced optimization.
        
        Args:
            image_data_list: List of image data (bytes or base64)
            analysis_type: Type of analysis to perform
            marketplace: Target marketplace
            max_concurrent: Maximum concurrent processing
            use_cache: Whether to use caching
            
        Returns:
            BatchProcessingResult with all analysis results
        """
        start_time = time.perf_counter()
        self.enhanced_stats["batch_processes"] += 1
        
        try:
            cache_mode = use_cache if use_cache is not None else self.use_intelligent_caching
            
            if self.use_performance_optimization:
                # Use performance optimized batch processing
                result = await self.performance_system.analyze_batch_optimized(
                    image_data_list=image_data_list,
                    analysis_type=analysis_type,
                    marketplace=marketplace,
                    use_cache=cache_mode,
                    max_concurrent=max_concurrent
                )
                
                logger.info(f"Enhanced batch processing completed: {len(image_data_list)} images, "
                           f"avg_time={result.average_processing_time:.1f}ms, "
                           f"cache_hits={result.cache_hits}, memory={result.memory_usage_mb:.1f}MB")
                
                return result
                
            else:
                # Fall back to sequential processing
                results = []
                for i, image_data in enumerate(image_data_list):
                    try:
                        result = await self.analyze_image(
                            image_data=image_data,
                            analysis_type=analysis_type,
                            marketplace=marketplace,
                            use_cache=cache_mode
                        )
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Batch item {i} failed: {e}")
                        results.append(ImageAnalysisResult(
                            analysis=f"Batch processing failed: {str(e)}",
                            confidence=0.0,
                            product_details={"error": str(e), "batch_index": i},
                            processing_method="batch_fallback",
                            cost_estimate=0.0
                        ))
                
                total_time = (time.perf_counter() - start_time) * 1000
                avg_time = total_time / len(image_data_list) if image_data_list else 0
                
                return BatchProcessingResult(
                    results=results,
                    total_processing_time=total_time,
                    average_processing_time=avg_time,
                    cache_hits=0,
                    cache_misses=len(image_data_list),
                    memory_usage_mb=0.0
                )
                
        except Exception as e:
            logger.error(f"Enhanced batch processing failed: {e}")
            # Return error results
            error_results = [
                ImageAnalysisResult(
                    analysis=f"Batch processing failed: {str(e)}",
                    confidence=0.0,
                    product_details={"error": str(e), "batch_index": i},
                    processing_method="batch_error_fallback",
                    cost_estimate=0.0
                )
                for i in range(len(image_data_list))
            ]
            
            return BatchProcessingResult(
                results=error_results,
                total_processing_time=0.0,
                average_processing_time=0.0,
                cache_hits=0,
                cache_misses=0,
                memory_usage_mb=0.0
            )
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize system performance by cleaning up resources."""
        try:
            optimization_results = {}
            
            if self.use_performance_optimization:
                # Optimize memory usage
                memory_result = self.performance_system.optimize_memory_usage()
                optimization_results["memory_optimization"] = memory_result
                
                # Update cache utilization stats
                cache_stats = self.performance_system.cache.get_stats()
                self.enhanced_stats["cache_utilization"] = cache_stats.get("hit_rate", 0.0)
            
            optimization_results["enhanced_stats"] = self.enhanced_stats.copy()
            
            logger.info("Performance optimization completed")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            return {"error": str(e)}
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive enhanced statistics."""
        try:
            stats = {
                "enhanced_pipeline_stats": self.enhanced_stats.copy(),
                "base_pipeline_available": True
            }
            
            if self.use_enhanced_processing:
                stats["enhanced_processor_stats"] = self.enhanced_processor.get_stats()
            
            if self.use_performance_optimization:
                stats["performance_system_stats"] = self.performance_system.get_comprehensive_stats()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get enhanced stats: {e}")
            return {"error": str(e)}
    
    def configure_enhancement(
        self,
        use_enhanced_processing: bool = None,
        use_performance_optimization: bool = None,
        use_intelligent_caching: bool = None,
        cache_size_mb: int = None,
        cache_ttl_seconds: int = None
    ) -> Dict[str, Any]:
        """
        Configure enhancement settings at runtime.
        
        Args:
            use_enhanced_processing: Enable/disable enhanced processing
            use_performance_optimization: Enable/disable performance optimization
            use_intelligent_caching: Enable/disable intelligent caching
            cache_size_mb: Cache size in MB
            cache_ttl_seconds: Cache TTL in seconds
            
        Returns:
            Configuration status
        """
        try:
            config_changes = {}
            
            if use_enhanced_processing is not None:
                self.use_enhanced_processing = use_enhanced_processing
                config_changes["enhanced_processing"] = use_enhanced_processing
            
            if use_performance_optimization is not None:
                self.use_performance_optimization = use_performance_optimization
                config_changes["performance_optimization"] = use_performance_optimization
            
            if use_intelligent_caching is not None:
                self.use_intelligent_caching = use_intelligent_caching
                config_changes["intelligent_caching"] = use_intelligent_caching
            
            # Update cache configuration if needed
            if cache_size_mb is not None or cache_ttl_seconds is not None:
                if self.use_performance_optimization:
                    if cache_size_mb is not None:
                        self.performance_system.cache.max_size_mb = cache_size_mb
                        config_changes["cache_size_mb"] = cache_size_mb
                    
                    if cache_ttl_seconds is not None:
                        self.performance_system.cache.ttl_seconds = cache_ttl_seconds
                        config_changes["cache_ttl_seconds"] = cache_ttl_seconds
            
            logger.info(f"Enhanced configuration updated: {config_changes}")
            
            return {
                "success": True,
                "changes": config_changes,
                "current_config": {
                    "enhanced_processing": self.use_enhanced_processing,
                    "performance_optimization": self.use_performance_optimization,
                    "intelligent_caching": self.use_intelligent_caching
                }
            }
            
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            return {"success": False, "error": str(e)}

# Create enhanced global instance
enhanced_vision_service = EnhancedScalableVisionPipeline()

# Backward compatibility aliases
EnhancedVisionAnalysisService = EnhancedScalableVisionPipeline

# Export main components
__all__ = [
    "EnhancedScalableVisionPipeline",
    "enhanced_vision_service",
    "EnhancedVisionAnalysisService"
]
