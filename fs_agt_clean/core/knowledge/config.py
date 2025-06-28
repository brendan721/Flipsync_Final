"""Configuration settings for the knowledge sharing module."""

from enum import Enum
from typing import Any, Dict, List, Optional

# Knowledge validation settings
DEFAULT_MIN_VALIDATORS = 2
DEFAULT_VALIDATION_THRESHOLD = 0.7
DEFAULT_MAX_VALIDATION_AGE_HOURS = 24

# Knowledge subscription settings
DEFAULT_SUBSCRIPTION_REFRESH_SECONDS = 60
DEFAULT_MAX_NOTIFICATIONS_PER_BATCH = 10

# Knowledge repository settings
DEFAULT_VECTOR_DIMENSIONS = 1536  # Default for OpenAI embeddings
DEFAULT_COLLECTION_NAME = "shared_knowledge"
DEFAULT_SIMILARITY_THRESHOLD = 0.85

# Knowledge entry settings
DEFAULT_MAX_CONTENT_SIZE_BYTES = 10 * 1024  # 10KB
DEFAULT_MAX_TAGS = 10
DEFAULT_MIN_CONFIDENCE = 0.5

# Knowledge types that require special validation rules
CRITICAL_KNOWLEDGE_TYPES = [
    "PRICING_STRATEGY",
    "INVENTORY_PREDICTION",
    "OPERATIONAL_INSIGHT",
]

# Knowledge types that require higher validation thresholds
VALIDATION_THRESHOLDS = {
    "PRICING_STRATEGY": 0.8,
    "INVENTORY_PREDICTION": 0.75,
    "OPERATIONAL_INSIGHT": 0.75,
    "COMPETITOR_ANALYSIS": 0.7,
    "MARKET_INSIGHT": 0.65,
    "CUSTOMER_BEHAVIOR": 0.65,
    "GENERAL": 0.6,
}

# Minimum number of validators required for each knowledge type
MIN_VALIDATORS = {
    "PRICING_STRATEGY": 3,
    "INVENTORY_PREDICTION": 3,
    "OPERATIONAL_INSIGHT": 3,
    "COMPETITOR_ANALYSIS": 2,
    "MARKET_INSIGHT": 2,
    "CUSTOMER_BEHAVIOR": 2,
    "GENERAL": 1,
}

# UnifiedAgent types that are authorized to validate specific knowledge types
AUTHORIZED_VALIDATORS = {
    "PRICING_STRATEGY": ["PricingUnifiedAgent", "ExecutiveUnifiedAgent"],
    "INVENTORY_PREDICTION": ["LogisticsUnifiedAgent", "ExecutiveUnifiedAgent"],
    "OPERATIONAL_INSIGHT": ["LogisticsUnifiedAgent", "ExecutiveUnifiedAgent"],
    "COMPETITOR_ANALYSIS": ["MarketUnifiedAgent", "ExecutiveUnifiedAgent"],
    "MARKET_INSIGHT": ["MarketUnifiedAgent", "ExecutiveUnifiedAgent"],
    "CUSTOMER_BEHAVIOR": ["MarketUnifiedAgent", "ContentUnifiedAgent", "ExecutiveUnifiedAgent"],
    "GENERAL": ["ExecutiveUnifiedAgent"],
}

# Default tags for each knowledge type
DEFAULT_TAGS = {
    "PRICING_STRATEGY": ["pricing", "strategy"],
    "INVENTORY_PREDICTION": ["inventory", "prediction"],
    "OPERATIONAL_INSIGHT": ["operations", "insight"],
    "COMPETITOR_ANALYSIS": ["competitor", "analysis"],
    "MARKET_INSIGHT": ["market", "insight"],
    "CUSTOMER_BEHAVIOR": ["customer", "behavior"],
    "GENERAL": ["general"],
}

# Knowledge sharing metrics
METRICS_ENABLED = True
DEFAULT_METRICS_WINDOW_SECONDS = 3600  # 1 hour


class KnowledgeSharingConfig:
    """Configuration for knowledge sharing."""

    def __init__(
        self,
        min_validators: Optional[Dict[str, int]] = None,
        validation_thresholds: Optional[Dict[str, float]] = None,
        max_validation_age_hours: int = DEFAULT_MAX_VALIDATION_AGE_HOURS,
        subscription_refresh_seconds: int = DEFAULT_SUBSCRIPTION_REFRESH_SECONDS,
        max_notifications_per_batch: int = DEFAULT_MAX_NOTIFICATIONS_PER_BATCH,
        vector_dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_content_size_bytes: int = DEFAULT_MAX_CONTENT_SIZE_BYTES,
        max_tags: int = DEFAULT_MAX_TAGS,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        metrics_enabled: bool = METRICS_ENABLED,
        metrics_window_seconds: int = DEFAULT_METRICS_WINDOW_SECONDS,
        authorized_validators: Optional[Dict[str, List[str]]] = None,
        default_tags: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize knowledge sharing configuration.

        Args:
            min_validators: Minimum number of validators required for each knowledge type
            validation_thresholds: Validation score thresholds for each knowledge type
            max_validation_age_hours: Maximum age of validations in hours
            subscription_refresh_seconds: How often to refresh subscriptions in seconds
            max_notifications_per_batch: Maximum number of notifications to send in a batch
            vector_dimensions: Dimensions of the vector embeddings
            collection_name: Name of the vector store collection
            similarity_threshold: Threshold for similarity search
            max_content_size_bytes: Maximum size of knowledge content in bytes
            max_tags: Maximum number of tags per knowledge entry
            min_confidence: Minimum confidence score for knowledge entries
            metrics_enabled: Whether to collect metrics
            metrics_window_seconds: Window for metrics collection in seconds
            authorized_validators: UnifiedAgent types authorized to validate each knowledge type
            default_tags: Default tags for each knowledge type
        """
        self.min_validators = min_validators or MIN_VALIDATORS
        self.validation_thresholds = validation_thresholds or VALIDATION_THRESHOLDS
        self.max_validation_age_hours = max_validation_age_hours
        self.subscription_refresh_seconds = subscription_refresh_seconds
        self.max_notifications_per_batch = max_notifications_per_batch
        self.vector_dimensions = vector_dimensions
        self.collection_name = collection_name
        self.similarity_threshold = similarity_threshold
        self.max_content_size_bytes = max_content_size_bytes
        self.max_tags = max_tags
        self.min_confidence = min_confidence
        self.metrics_enabled = metrics_enabled
        self.metrics_window_seconds = metrics_window_seconds
        self.authorized_validators = authorized_validators or AUTHORIZED_VALIDATORS
        self.default_tags = default_tags or DEFAULT_TAGS

    def get_validation_threshold(self, knowledge_type: str) -> float:
        """Get validation threshold for a knowledge type."""
        return self.validation_thresholds.get(
            knowledge_type, DEFAULT_VALIDATION_THRESHOLD
        )

    def get_min_validators(self, knowledge_type: str) -> int:
        """Get minimum number of validators for a knowledge type."""
        return self.min_validators.get(knowledge_type, DEFAULT_MIN_VALIDATORS)

    def is_authorized_validator(self, agent_type: str, knowledge_type: str) -> bool:
        """Check if an agent type is authorized to validate a knowledge type."""
        authorized = self.authorized_validators.get(knowledge_type, [])
        return agent_type in authorized

    def get_default_tags(self, knowledge_type: str) -> List[str]:
        """Get default tags for a knowledge type."""
        return self.default_tags.get(knowledge_type, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "min_validators": self.min_validators,
            "validation_thresholds": self.validation_thresholds,
            "max_validation_age_hours": self.max_validation_age_hours,
            "subscription_refresh_seconds": self.subscription_refresh_seconds,
            "max_notifications_per_batch": self.max_notifications_per_batch,
            "vector_dimensions": self.vector_dimensions,
            "collection_name": self.collection_name,
            "similarity_threshold": self.similarity_threshold,
            "max_content_size_bytes": self.max_content_size_bytes,
            "max_tags": self.max_tags,
            "min_confidence": self.min_confidence,
            "metrics_enabled": self.metrics_enabled,
            "metrics_window_seconds": self.metrics_window_seconds,
            "authorized_validators": self.authorized_validators,
            "default_tags": self.default_tags,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "KnowledgeSharingConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)


# Default configuration instance
default_config = KnowledgeSharingConfig()
