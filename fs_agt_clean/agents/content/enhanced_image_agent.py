"""
Enhanced Image Processing Agent for FlipSync
===========================================

Advanced image processing agent with multi-model AI analysis, specialized processing operations,
and marketplace-optimized image enhancement capabilities.

AGENT_CONTEXT: Enhanced image processing with AI-powered analysis and advanced optimization
AGENT_PRIORITY: Production-ready image processing with quality assurance and cost optimization
AGENT_PATTERN: Async processing with intelligent model routing and comprehensive error handling
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fs_agt_clean.agents.content.base_content_agent import BaseContentUnifiedAgent
from fs_agt_clean.core.ai.enhanced_vision_service import (
    EnhancedVisionService,
    VisionModelProvider,
    AnalysisType,
    ProcessingOperation,
    EnhancedAnalysisResult
)
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager

logger = logging.getLogger(__name__)


class EnhancedImageUnifiedAgent(BaseContentUnifiedAgent):
    """
    Enhanced Image Processing Agent with advanced AI analysis capabilities.
    
    Capabilities:
    - Multi-model AI vision analysis (OpenAI, Claude, Google, Azure)
    - Specialized analysis types (quality, brand detection, defect analysis)
    - Advanced image processing (background removal, quality enhancement)
    - Batch processing with optimized concurrency
    - Marketplace compliance verification
    - Authenticity verification and brand detection
    - Real-time processing with WebSocket support
    """
    
    def __init__(self, agent_id: str = None, config: Dict[str, Any] = None):
        """Initialize enhanced image agent."""
        super().__init__(
            agent_id=agent_id or f"enhanced_image_agent_{uuid4().hex[:8]}",
            agent_type="enhanced_image_processing",
            config=config or {}
        )
        
        # Initialize enhanced vision service
        self.vision_service = EnhancedVisionService(config=self.config)
        
        # Processing capabilities
        self.supported_formats = ["JPEG", "PNG", "WEBP", "BMP", "TIFF"]
        self.max_batch_size = self.config.get("max_batch_size", 10)
        self.quality_threshold = self.config.get("quality_threshold", 0.8)
        
        # Performance tracking
        self.processing_stats = {
            "total_processed": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_processing_time": 0.0,
            "total_cost": 0.0
        }
        
        logger.info(f"Enhanced Image Agent initialized: {self.agent_id}")
    
    async def _initialize_agent(self) -> None:
        """Initialize agent-specific components."""
        await super()._initialize_agent()
        
        # Initialize processing pipelines
        self.processing_pipelines = {
            "marketplace_optimization": [
                ProcessingOperation.QUALITY_ENHANCEMENT,
                ProcessingOperation.COLOR_CORRECTION,
                ProcessingOperation.BACKGROUND_REMOVAL
            ],
            "quality_enhancement": [
                ProcessingOperation.NOISE_REDUCTION,
                ProcessingOperation.QUALITY_ENHANCEMENT,
                ProcessingOperation.RESOLUTION_UPSCALING
            ],
            "compliance_check": [
                ProcessingOperation.BACKGROUND_REMOVAL,
                ProcessingOperation.WATERMARK_REMOVAL
            ]
        }
        
        logger.info("Enhanced image processing pipelines initialized")
    
    async def _generate_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced image analysis and processing results."""
        try:
            operation = task.get("operation", "analyze")
            image_data = task.get("image_data")
            marketplace = task.get("marketplace", "ebay")
            
            if not image_data:
                raise ValueError("No image data provided")
            
            start_time = datetime.now(timezone.utc)
            
            if operation == "analyze_enhanced":
                result = await self.analyze_image_enhanced(
                    image_data=image_data,
                    analysis_types=task.get("analysis_types", [AnalysisType.PRODUCT_IDENTIFICATION]),
                    marketplace=marketplace,
                    model_preference=task.get("model_preference"),
                    additional_context=task.get("context", "")
                )
            elif operation == "process_advanced":
                result = await self.process_image_advanced(
                    image_data=image_data,
                    operations=task.get("operations", [ProcessingOperation.QUALITY_ENHANCEMENT]),
                    quality_target=task.get("quality_target", 0.9)
                )
            elif operation == "batch_analyze":
                result = await self.batch_analyze_images(
                    image_batch=task.get("image_batch", []),
                    analysis_types=task.get("analysis_types", [AnalysisType.PRODUCT_IDENTIFICATION]),
                    marketplace=marketplace
                )
            elif operation == "marketplace_optimize":
                result = await self.optimize_for_marketplace(
                    image_data=image_data,
                    marketplace=marketplace,
                    target_quality=task.get("target_quality", 0.9)
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Update statistics
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._update_processing_stats(processing_time, True, result.get("cost_estimate", 0.0))
            
            return {
                "success": True,
                "result": result,
                "processing_time": processing_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced image processing failed: {e}")
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._update_processing_stats(processing_time, False, 0.0)
            
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "agent_id": self.agent_id
            }
    
    async def analyze_image_enhanced(
        self,
        image_data: Any,
        analysis_types: List[AnalysisType],
        marketplace: str = "ebay",
        model_preference: Optional[VisionModelProvider] = None,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Perform enhanced image analysis with multiple AI models and analysis types.
        
        Args:
            image_data: Image data (bytes, base64, or file path)
            analysis_types: List of analysis types to perform
            marketplace: Target marketplace for optimization
            model_preference: Preferred AI model
            additional_context: Additional context for analysis
            
        Returns:
            Enhanced analysis results with comprehensive insights
        """
        try:
            logger.info(f"Starting enhanced analysis with {len(analysis_types)} analysis types")
            
            # Perform enhanced analysis
            result = await self.vision_service.analyze_image_enhanced(
                image_data=image_data,
                analysis_types=analysis_types,
                marketplace=marketplace,
                model_preference=model_preference,
                additional_context=additional_context
            )
            
            # Convert to dictionary for API response
            analysis_dict = {
                "analysis_id": result.analysis_id,
                "timestamp": result.timestamp.isoformat(),
                "primary_analysis": result.primary_analysis,
                "confidence_score": result.confidence_score,
                "product_details": result.product_details,
                "category_predictions": result.category_predictions,
                "brand_detection": result.brand_detection,
                "quality_metrics": result.quality_metrics,
                "defect_analysis": result.defect_analysis,
                "marketplace_compliance": result.marketplace_compliance,
                "optimization_suggestions": result.optimization_suggestions,
                "model_used": result.model_used.value,
                "processing_time": result.processing_time,
                "cost_estimate": result.cost_estimate,
                "competitive_insights": result.competitive_insights,
                "authenticity_score": result.authenticity_score,
                "style_attributes": result.style_attributes
            }
            
            logger.info(f"Enhanced analysis completed: confidence={result.confidence_score:.2f}, cost=${result.cost_estimate:.4f}")
            return analysis_dict
            
        except Exception as e:
            logger.error(f"Enhanced image analysis failed: {e}")
            return {
                "error": str(e),
                "analysis_id": f"failed_{int(datetime.now().timestamp())}",
                "confidence_score": 0.0
            }
    
    async def process_image_advanced(
        self,
        image_data: Any,
        operations: List[ProcessingOperation],
        quality_target: float = 0.9
    ) -> Dict[str, Any]:
        """
        Perform advanced image processing operations.
        
        Args:
            image_data: Input image data
            operations: List of processing operations
            quality_target: Target quality score
            
        Returns:
            Processing results with enhanced image
        """
        try:
            logger.info(f"Starting advanced processing with {len(operations)} operations")
            
            result = await self.vision_service.process_image_advanced(
                image_data=image_data,
                operations=operations,
                quality_target=quality_target
            )
            
            logger.info(f"Advanced processing completed: quality={result.get('quality_score', 0):.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Advanced image processing failed: {e}")
            return {
                "error": str(e),
                "processed_image_data": None,
                "quality_score": 0.0
            }
    
    async def batch_analyze_images(
        self,
        image_batch: List[Dict[str, Any]],
        analysis_types: List[AnalysisType],
        marketplace: str = "ebay"
    ) -> Dict[str, Any]:
        """
        Perform batch analysis of multiple images.
        
        Args:
            image_batch: List of image data dictionaries
            analysis_types: Analysis types to perform
            marketplace: Target marketplace
            
        Returns:
            Batch analysis results
        """
        try:
            logger.info(f"Starting batch analysis of {len(image_batch)} images")
            
            # Limit batch size
            if len(image_batch) > self.max_batch_size:
                logger.warning(f"Batch size {len(image_batch)} exceeds limit {self.max_batch_size}, truncating")
                image_batch = image_batch[:self.max_batch_size]
            
            results = await self.vision_service.batch_analyze_images(
                image_batch=image_batch,
                analysis_types=analysis_types,
                marketplace=marketplace,
                max_concurrent=5
            )
            
            # Convert results to dictionaries
            batch_results = []
            total_cost = 0.0
            successful_count = 0
            
            for result in results:
                if isinstance(result, EnhancedAnalysisResult):
                    batch_results.append({
                        "analysis_id": result.analysis_id,
                        "primary_analysis": result.primary_analysis,
                        "confidence_score": result.confidence_score,
                        "model_used": result.model_used.value,
                        "cost_estimate": result.cost_estimate
                    })
                    total_cost += result.cost_estimate
                    successful_count += 1
                else:
                    batch_results.append({"error": str(result)})
            
            logger.info(f"Batch analysis completed: {successful_count}/{len(image_batch)} successful, cost=${total_cost:.4f}")
            
            return {
                "batch_results": batch_results,
                "total_images": len(image_batch),
                "successful_analyses": successful_count,
                "total_cost": total_cost,
                "average_confidence": sum(r.get("confidence_score", 0) for r in batch_results) / len(batch_results) if batch_results else 0
            }
            
        except Exception as e:
            logger.error(f"Batch image analysis failed: {e}")
            return {
                "error": str(e),
                "batch_results": [],
                "total_images": len(image_batch),
                "successful_analyses": 0
            }
    
    async def optimize_for_marketplace(
        self,
        image_data: Any,
        marketplace: str = "ebay",
        target_quality: float = 0.9
    ) -> Dict[str, Any]:
        """
        Optimize image specifically for marketplace requirements.
        
        Args:
            image_data: Input image data
            marketplace: Target marketplace
            target_quality: Target quality score
            
        Returns:
            Marketplace-optimized image and compliance report
        """
        try:
            logger.info(f"Optimizing image for {marketplace} marketplace")
            
            # Get marketplace-specific pipeline
            pipeline = self.processing_pipelines.get("marketplace_optimization", [
                ProcessingOperation.QUALITY_ENHANCEMENT,
                ProcessingOperation.COLOR_CORRECTION
            ])
            
            # Process image
            processing_result = await self.process_image_advanced(
                image_data=image_data,
                operations=pipeline,
                quality_target=target_quality
            )
            
            # Analyze for marketplace compliance
            compliance_analysis = await self.analyze_image_enhanced(
                image_data=processing_result.get("processed_image_data", image_data),
                analysis_types=[AnalysisType.MARKETPLACE_COMPLIANCE, AnalysisType.QUALITY_ASSESSMENT],
                marketplace=marketplace
            )
            
            return {
                "optimized_image": processing_result.get("processed_image_data"),
                "quality_score": processing_result.get("quality_score", 0.0),
                "compliance_check": compliance_analysis.get("marketplace_compliance", {}),
                "optimization_suggestions": compliance_analysis.get("optimization_suggestions", []),
                "meets_requirements": processing_result.get("meets_quality_target", False),
                "processing_log": processing_result.get("processing_log", [])
            }
            
        except Exception as e:
            logger.error(f"Marketplace optimization failed: {e}")
            return {
                "error": str(e),
                "optimized_image": None,
                "quality_score": 0.0
            }
    
    async def _update_processing_stats(self, processing_time: float, success: bool, cost: float) -> None:
        """Update processing statistics."""
        self.processing_stats["total_processed"] += 1
        
        if success:
            self.processing_stats["successful_analyses"] += 1
        else:
            self.processing_stats["failed_analyses"] += 1
        
        # Update average processing time
        total_time = self.processing_stats["average_processing_time"] * (self.processing_stats["total_processed"] - 1)
        self.processing_stats["average_processing_time"] = (total_time + processing_time) / self.processing_stats["total_processed"]
        
        # Update total cost
        self.processing_stats["total_cost"] += cost
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        success_rate = (
            self.processing_stats["successful_analyses"] / self.processing_stats["total_processed"]
            if self.processing_stats["total_processed"] > 0 else 0.0
        )
        
        return {
            **self.processing_stats,
            "success_rate": success_rate,
            "agent_id": self.agent_id,
            "uptime": (datetime.now(timezone.utc) - self.created_at).total_seconds()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on enhanced image agent."""
        try:
            # Test basic functionality
            test_result = await self.vision_service._calculate_quality_score(None)
            
            stats = await self.get_processing_stats()
            
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "vision_service_available": True,
                "processing_stats": stats,
                "supported_formats": self.supported_formats,
                "max_batch_size": self.max_batch_size,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_id": self.agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Export enhanced image agent
__all__ = ["EnhancedImageUnifiedAgent"]
