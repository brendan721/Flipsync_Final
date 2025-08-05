"""
Vision Service - Clean Interface for FlipSync Vision Analysis
===========================================================

This module provides a clean interface to the scalable vision pipeline
with zero OpenAI dependencies.
"""

from .scalable_vision_service import (
    ScalableVisionPipeline,
    VisionServiceType,
    ImageAnalysisResult,
    vision_service,
)

# Create the main vision analysis service
VisionAnalysisService = ScalableVisionPipeline

# Export the main components
__all__ = [
    "VisionAnalysisService",
    "ScalableVisionPipeline", 
    "VisionServiceType",
    "ImageAnalysisResult",
    "vision_service",
]
