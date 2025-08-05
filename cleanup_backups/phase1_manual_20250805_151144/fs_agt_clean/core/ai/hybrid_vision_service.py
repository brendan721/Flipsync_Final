"""
Hybrid Vision Service for FlipSync - Local + OpenAI Vision Processing
===================================================================

Provides intelligent routing between local template-based vision processing
and OpenAI GPT-4o Vision API based on confidence thresholds and use cases.

Features:
- Local-first processing with OpenAI escalation
- Confidence-based routing decisions
- Performance optimization (<2000ms local, strategic OpenAI usage)
- Cost reduction through intelligent escalation
- Backward compatibility with existing vision clients
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Union
from enum import Enum

from fs_agt_clean.core.ai.local_vision_processor import (
    LocalVisionProcessor,
    LocalAnalysisType,
    LocalVisionResult,
)
from fs_agt_clean.core.ai.vision_clients import (
    VisionAnalysisService,
    ImageAnalysisResult,
)

logger = logging.getLogger(__name__)


class VisionProcessingMode(Enum):
    """Vision processing modes for hybrid service."""

    LOCAL_ONLY = "local_only"
    LOCAL_WITH_ESCALATION = "local_with_escalation"
    OPENAI_STRATEGIC = "openai_strategic"
    PARALLEL_VALIDATION = "parallel_validation"


class HybridVisionResult:
    """Result from hybrid vision processing."""

    def __init__(
        self,
        analysis: str,
        confidence: float,
        processing_mode: str,
        processing_time_ms: int,
        cost_estimate: float = 0.0,
        local_result: Optional[LocalVisionResult] = None,
        openai_result: Optional[ImageAnalysisResult] = None,
        escalation_used: bool = False,
        escalation_reason: str = "",
    ):
        self.analysis = analysis
        self.confidence = confidence
        self.processing_mode = processing_mode
        self.processing_time_ms = processing_time_ms
        self.cost_estimate = cost_estimate
        self.local_result = local_result
        self.openai_result = openai_result
        self.escalation_used = escalation_used
        self.escalation_reason = escalation_reason


class HybridVisionService:
    """
    Hybrid vision service that intelligently routes between local and OpenAI processing.

    Provides cost-effective vision analysis by using local template-based processing
    first, then escalating to OpenAI GPT-4o Vision only when necessary.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize hybrid vision service."""
        self.config = config or {}

        # Configuration parameters
        self.local_confidence_threshold = self.config.get(
            "local_confidence_threshold", 0.7
        )
        self.escalation_threshold = self.config.get("escalation_threshold", 0.5)
        self.max_local_processing_time = self.config.get(
            "max_local_processing_time", 2000
        )
        self.cost_budget_daily = self.config.get("cost_budget_daily", 5.0)
        self.current_daily_cost = 0.0

        # Processing mode preferences
        self.default_mode = VisionProcessingMode(
            self.config.get("default_mode", "local_with_escalation")
        )

        # Initialize processors
        self.local_processor = LocalVisionProcessor(config)
        self.openai_client = HybridLLMClient()