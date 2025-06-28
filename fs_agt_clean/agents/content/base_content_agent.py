"""Base content agent for FlipSync content generation and optimization."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)


class BaseContentUnifiedAgent(ABC):
    """
    Base agent for content operations.
    Handles content generation, optimization, and management.
    """

    def __init__(
        self,
        agent_id: str,
        content_type: str,
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the base content agent.

        Args:
            agent_id: Unique identifier for this agent
            content_type: Type of content this agent handles
            config_manager: Configuration manager
            alert_manager: Alert manager for monitoring
            battery_optimizer: Battery optimizer for mobile efficiency
            config: Optional configuration overrides
        """
        self.agent_id = agent_id or str(uuid4())
        self.content_type = content_type
        self.config_manager = config_manager or ConfigManager()
        self.alert_manager = alert_manager or AlertManager()
        self.battery_optimizer = battery_optimizer or BatteryOptimizer()
        self.config = config or {}

        # Initialize metrics
        self.metrics = {
            "content_generated": 0,
            "content_optimized": 0,
            "quality_score": 0.0,
            "generation_latency": 0.0,
            "optimization_latency": 0.0,
            "token_usage": 0,
        }

        logger.info(f"Initialized BaseContentUnifiedAgent: {agent_id} for {content_type}")

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        return ["model_name", "max_tokens", "temperature", "quality_threshold"]

    async def initialize(self) -> None:
        """Initialize content generation resources."""
        required_fields = self._get_required_config_fields()
        if not all(field in self.config for field in required_fields):
            raise ValueError("Invalid content agent configuration")
        await self._setup_content_resources()

    @abstractmethod
    async def _setup_content_resources(self) -> None:
        """Set up content generation resources."""
        pass

    @abstractmethod
    async def _cleanup_content_resources(self) -> None:
        """Clean up content generation resources."""
        pass

    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process content-related events."""
        event_type = event.get("type")
        if event_type == "generate":
            await self._handle_generation_event(event)
        elif event_type == "optimize":
            await self._handle_optimization_event(event)
        else:
            logger.warning("Unknown event type: %s", event_type)

    @abstractmethod
    async def _handle_generation_event(self, event: Dict[str, Any]) -> None:
        """Handle content generation events."""
        pass

    @abstractmethod
    async def _handle_optimization_event(self, event: Dict[str, Any]) -> None:
        """Handle content optimization events."""
        pass

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content tasks."""
        task_type = task.get("type")
        if task_type == "generate_content":
            return await self._generate_content(task)
        elif task_type == "optimize_content":
            return await self._optimize_content(task)
        elif task_type == "analyze_content":
            return await self._analyze_content(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    @abstractmethod
    async def _generate_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new content."""
        pass

    @abstractmethod
    async def _optimize_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing content."""
        pass

    async def _analyze_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content quality and performance."""
        try:
            content = task.get("content", "")
            if not content:
                return {"error": "No content provided for analysis"}

            # Basic content analysis
            analysis = {
                "word_count": len(content.split()),
                "character_count": len(content),
                "sentence_count": len([s for s in content.split(".") if s.strip()]),
                "readability_score": self._calculate_readability_score(content),
                "seo_score": self._calculate_seo_score(
                    content, task.get("keywords", [])
                ),
                "quality_score": self._calculate_quality_score(content),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return {"analysis": analysis, "success": True}

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {"error": str(e), "success": False}

    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)."""
        try:
            sentences = [s for s in content.split(".") if s.strip()]
            words = content.split()

            if not sentences or not words:
                return 0.0

            avg_sentence_length = len(words) / len(sentences)

            # Simplified readability calculation
            # Higher score = more readable
            score = 206.835 - (1.015 * avg_sentence_length)
            return max(0.0, min(100.0, score))

        except Exception:
            return 50.0  # Default moderate readability

    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Calculate SEO score based on keyword usage and content structure."""
        try:
            if not keywords:
                return 50.0  # Default score if no keywords provided

            content_lower = content.lower()
            score = 0.0

            # Check keyword presence
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 20.0

            # Check content length (optimal 300-600 words)
            word_count = len(content.split())
            if 300 <= word_count <= 600:
                score += 20.0
            elif word_count > 100:
                score += 10.0

            # Check for headings (simple heuristic)
            if any(line.strip().isupper() for line in content.split("\n")):
                score += 10.0

            return min(100.0, score)

        except Exception:
            return 50.0  # Default moderate SEO score

    def _calculate_quality_score(self, content: str) -> float:
        """Calculate overall content quality score."""
        try:
            if not content.strip():
                return 0.0

            score = 0.0

            # Length score
            word_count = len(content.split())
            if word_count >= 50:
                score += 25.0
            elif word_count >= 20:
                score += 15.0

            # Structure score
            sentences = [s for s in content.split(".") if s.strip()]
            if len(sentences) >= 3:
                score += 25.0
            elif len(sentences) >= 1:
                score += 15.0

            # Variety score (different sentence lengths)
            if sentences:
                lengths = [len(s.split()) for s in sentences]
                if len(set(lengths)) > 1:
                    score += 25.0

            # Completeness score
            if content.strip().endswith("."):
                score += 25.0

            return min(100.0, score)

        except Exception:
            return 50.0  # Default moderate quality

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            **self.metrics,
            "agent_id": self.agent_id,
            "content_type": self.content_type,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def shutdown(self) -> None:
        """Clean up content resources."""
        await self._cleanup_content_resources()
        logger.info(f"Content agent {self.agent_id} shut down successfully")
