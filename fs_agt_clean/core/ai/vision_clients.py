"""
Vision Analysis Service for FlipSync AI-Powered Product Creation.

This module provides scalable vision analysis capabilities using a multistep pipeline
with zero OpenAI dependencies for cost-optimized processing.

Features:
- Scalable multistep pipeline (barcode → OCR → cloud vision)
- Zero OpenAI dependencies
- Cost-optimized processing with free local analysis
- Production-grade error handling
- Picture-to-product generation functionality
- Integration with AI-Powered Product Creation Workflow
"""

import logging
from typing import Dict, Optional

# Import the new scalable vision service
from .scalable_vision_service import (
    ScalableVisionPipeline,
    VisionServiceType,
    ImageAnalysisResult,
)

logger = logging.getLogger(__name__)


class VisionClientFactory:
    """Factory for creating vision clients based on configuration."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize vision client factory."""
        self.config = config or {}
        logger.info("VisionClientFactory initialized with functional implementation")

    def create_client(
        self,
        service_type: VisionServiceType = VisionServiceType.BARCODE_OCR_GOOGLE,
        **kwargs,
    ) -> ScalableVisionPipeline:
        """Create vision client based on service type - consolidated to ScalableVisionPipeline."""
        try:
            # All service types now use the consolidated ScalableVisionPipeline
            config = kwargs.get("config", {})
            logger.info(f"Creating ScalableVisionPipeline for {service_type.value}")
            return ScalableVisionPipeline(config)
        except Exception as e:
            logger.error(f"Failed to create vision client: {e}")
            # Return fallback client
            return ScalableVisionPipeline()

    def create_ollama_client(self, **kwargs) -> ScalableVisionPipeline:
        """Create Ollama vision client - consolidated to ScalableVisionPipeline."""
        config = kwargs.get("config", {})
        return ScalableVisionPipeline(config)

    def create_gpt4_client(self, **kwargs) -> ScalableVisionPipeline:
        """Create GPT-4 vision client - consolidated to ScalableVisionPipeline."""
        config = kwargs.get("config", {})
        return ScalableVisionPipeline(config)


class EnhancedVisionManager:
    """Enhanced vision manager with functional implementation."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize enhanced vision manager."""
        self.config = config or {}
        self.client_factory = VisionClientFactory(config)
        logger.info("EnhancedVisionManager initialized with functional implementation")

    async def analyze_image(
        self,
        image_data,
        analysis_type: str = "product_identification",
        marketplace: str = "ebay",
        additional_context: str = "",
        service_type: VisionServiceType = VisionServiceType.BARCODE_OCR_GOOGLE,
    ) -> Dict:
        """Analyze image using specified service type."""
        try:
            # Get or create client
            client = self.client_factory.create_client(service_type)

            # Analyze image
            result = await client.analyze_image(
                image_data, analysis_type, marketplace, additional_context
            )

            # Convert to dictionary for compatibility
            return result.to_dict()

        except Exception as e:
            logger.error(f"Enhanced vision analysis failed: {e}")
            return {
                "analysis": f"Vision analysis failed: {str(e)}",
                "confidence": 0.0,
                "product_details": {"error": str(e)},
                "processing_method": "error_fallback",
                "cost_estimate": 0.0,
            }


# Create global instances for compatibility
enhanced_vision_manager = EnhancedVisionManager()
vision_analysis_service = ScalableVisionPipeline()
# GPT4VisionClient is now consolidated into ScalableVisionPipeline
gpt4_vision_client = ScalableVisionPipeline()  # Backward compatibility alias
vision_client_factory = VisionClientFactory()

logger.info(
    "Vision clients functional implementation loaded - ready for AI-Powered Product Creation"
)

# Export the main components
__all__ = [
    "VisionAnalysisService",
    "ScalableVisionPipeline",
    "VisionServiceType",
    "ImageAnalysisResult",
    "VisionClientFactory",
    "EnhancedVisionManager",
    "enhanced_vision_manager",
    "vision_analysis_service",
    "gpt4_vision_client",
    "vision_client_factory",
]

# Backward compatibility
VisionAnalysisService = ScalableVisionPipeline
