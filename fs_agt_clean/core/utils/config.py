"""Configuration utility module with vision-aligned optimizations.

This module provides a configuration utility that aligns with the FlipSync vision:
- Mobile-First Approach: Offline capability, battery awareness, payload optimization
- UnifiedAgent Coordination System: Hierarchical communication, orchestration support
- Conversational Interface: NLP support, personalized assistance
"""

import json
import logging
import os
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field


class UnifiedAgentCoordinationConfig(BaseModel):
    """Configuration for agent coordination."""

    hierarchical_enabled: bool = True
    orchestration_enabled: bool = True
    decision_engine_enabled: bool = True
    pipeline_enabled: bool = True
    agent_registry_url: str = "http://localhost:8000/registry"
    coordination_protocol: str = "event-based"  # event-based, message-based, rpc-based
    message_format: str = "json"  # json, protobuf, avro
    correlation_id_enabled: bool = True
    priority_levels: List[str] = ["high", "medium", "low"]


class ConversationalConfig(BaseModel):
    """Configuration for conversational interface."""

    nlp_enabled: bool = True
    query_routing_enabled: bool = True
    personalization_enabled: bool = True
    proactive_recommendations_enabled: bool = True
    nlp_model: str = "local"  # local, remote, hybrid
    conversation_context_ttl: int = 3600  # seconds
    max_conversation_history: int = 10
    default_language: str = "en"


class MobileConfig(BaseModel):
    """Configuration for mobile-first approach."""

    context: Optional[Dict[str, Any]] = None
    battery_optimization_enabled: bool = True
    offline_mode_enabled: bool = False
    payload_optimization_enabled: bool = True
    ui_optimization_enabled: bool = True
    sync_interval: int = 60  # seconds
    max_offline_storage: int = 100  # MB
    low_battery_threshold: int = 20  # percentage


class SecurityConfig(BaseModel):
    """Configuration for security and reliability."""

    encryption_enabled: bool = True
    access_control_enabled: bool = True
    health_monitoring_enabled: bool = True
    fallback_enabled: bool = True
    encryption_algorithm: str = "AES-256"
    token_expiration: int = 3600  # seconds
    max_failed_attempts: int = 5
    lockout_duration: int = 300  # seconds


class Settings(BaseModel):
    """Application settings with vision-aligned optimizations."""

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # JWT settings
    jwt_secret_key: str = "your-secret-key"  # Should be overridden in production
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Monitoring settings
    enable_metrics: bool = True
    metrics_port: int = 9090
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "my-token"
    INFLUXDB_ORG: str = "my-org"
    INFLUXDB_BUCKET: str = "my-bucket"

    # Vision-aligned settings
    mobile: MobileConfig = Field(default_factory=MobileConfig)
    agent_coordination: UnifiedAgentCoordinationConfig = Field(
        default_factory=UnifiedAgentCoordinationConfig
    )
    conversational: ConversationalConfig = Field(default_factory=ConversationalConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # State management
    state_persistence_enabled: bool = True
    state_store_type: str = "memory"  # memory, redis, file
    state_encryption_enabled: bool = True

    # Performance optimization
    performance_metrics_enabled: bool = True
    resource_usage_tracking: bool = True
    concurrent_operations_limit: int = 10

    class Config:
        env_prefix = "FS_"
        case_sensitive = False

    # Mobile-First Methods

    def is_mobile_context(self) -> bool:
        """Check if the settings are being used in a mobile context."""
        return self.mobile.context is not None

    def is_low_battery(self) -> bool:
        """Check if the device is in a low battery state."""
        if self.is_mobile_context() and self.mobile.battery_optimization_enabled:
            battery_level = self.mobile.context.get("battery_level", 100)
            return battery_level < self.mobile.low_battery_threshold
        return False

    def adjust_processing_intensity(self, intensity: float) -> float:
        """Adjust processing intensity based on battery state."""
        if self.is_low_battery():
            return intensity * 0.5
        return intensity

    def optimize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize payload size for mobile networks."""
        if self.is_mobile_context() and self.mobile.payload_optimization_enabled:
            optimized_payload = {}
            for key, value in payload.items():
                if isinstance(value, str) and len(value) > 100:
                    optimized_payload[key] = value[:100] + "..."
                elif isinstance(value, dict):
                    optimized_payload[key] = self.optimize_payload(value)
                elif isinstance(value, list) and len(value) > 20:
                    optimized_payload[key] = value[:20]
                else:
                    optimized_payload[key] = value
            return optimized_payload
        return payload

    def is_offline(self) -> bool:
        """Check if the device is in offline mode."""
        if self.is_mobile_context() and self.mobile.offline_mode_enabled:
            network_state = self.mobile.context.get("network_state", "online")
            return network_state == "offline"
        return False

    def handle_offline(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle operations in offline mode."""
        if self.is_offline():
            # Queue operation for when online
            return {
                "status": "queued",
                "message": "Operation queued for when online",
                "operation": operation,
                "data": data,
            }
        return {"status": "online", "message": "Operation can proceed online"}

    def save_local_state(self, state: Dict[str, Any]) -> bool:
        """Save state locally for offline use."""
        if self.is_mobile_context() and self.mobile.offline_mode_enabled:
            # In a real implementation, this would save to local storage
            return True
        return False

    def load_local_state(self) -> Dict[str, Any]:
        """Load state from local storage."""
        if self.is_mobile_context() and self.mobile.offline_mode_enabled:
            # In a real implementation, this would load from local storage
            return {"loaded": True}
        return {}

    def format_for_mobile_ui(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for mobile UI."""
        if self.is_mobile_context() and self.mobile.ui_optimization_enabled:
            # Optimize data structure for mobile UI
            return {"mobile_optimized": True, "data": self.optimize_payload(data)}
        return data

    # UnifiedAgent Coordination Methods

    def get_agent_hierarchy(self) -> Dict[str, List[str]]:
        """Get the agent hierarchy configuration."""
        if not self.agent_coordination.hierarchical_enabled:
            return {}

        # In a real implementation, this would load from configuration
        return {
            "executive": ["market", "content", "logistics"],
            "market": ["amazon", "ebay", "inventory"],
            "content": ["description", "image", "seo"],
            "logistics": ["shipping", "tracking", "returns"],
        }

    def get_orchestration_config(self) -> Dict[str, Any]:
        """Get orchestration configuration."""
        if not self.agent_coordination.orchestration_enabled:
            return {}

        return {
            "registry_url": self.agent_coordination.agent_registry_url,
            "protocol": self.agent_coordination.coordination_protocol,
            "message_format": self.agent_coordination.message_format,
            "correlation_enabled": self.agent_coordination.correlation_id_enabled,
        }

    def get_decision_engine_config(self) -> Dict[str, Any]:
        """Get decision engine configuration."""
        if not self.agent_coordination.decision_engine_enabled:
            return {}

        return {
            "strategy": "hierarchical",
            "fallback_strategy": "majority_vote",
            "priority_levels": self.agent_coordination.priority_levels,
            "timeout_ms": 5000,
        }

    def get_pipeline_config(self) -> Dict[str, Any]:
        """Get pipeline controller configuration."""
        if not self.agent_coordination.pipeline_enabled:
            return {}

        return {
            "max_parallel_tasks": 5,
            "max_pipeline_depth": 10,
            "timeout_ms": 30000,
            "retry_count": 3,
        }

    # Conversational Interface Methods

    def format_for_nlp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for NLP processing."""
        if not self.conversational.nlp_enabled:
            return data

        # Extract text content for NLP processing
        nlp_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                nlp_data[key] = value
            elif isinstance(value, dict) and "text" in value:
                nlp_data[key] = value["text"]

        return {
            "original": data,
            "nlp_data": nlp_data,
            "language": self.conversational.default_language,
        }

    def route_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a query to the appropriate handler."""
        if not self.conversational.query_routing_enabled:
            return {"handler": "default", "query": query, "context": context}

        # Simple keyword-based routing
        if "price" in query or "cost" in query:
            return {"handler": "pricing", "query": query, "context": context}
        elif "ship" in query or "delivery" in query:
            return {"handler": "shipping", "query": query, "context": context}
        elif "product" in query or "item" in query:
            return {"handler": "product", "query": query, "context": context}
        else:
            return {"handler": "general", "query": query, "context": context}

    def personalize_response(
        self, response: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Personalize a response based on user profile."""
        if not self.conversational.personalization_enabled or not user_profile:
            return response

        # Add personalization
        if "name" in user_profile:
            if "message" in response:
                response["message"] = (
                    f"Hi {user_profile['name']}, {response['message']}"
                )

        if "preferences" in user_profile:
            response["personalized"] = True
            response["user_preferences"] = user_profile["preferences"]

        return response

    def generate_recommendations(
        self, user_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate proactive recommendations based on user data."""
        if not self.conversational.proactive_recommendations_enabled:
            return []

        # Simple recommendation logic
        recommendations = []

        if "recent_searches" in user_data:
            recommendations.append(
                {
                    "type": "search_based",
                    "message": "Based on your recent searches, you might be interested in:",
                    "items": user_data["recent_searches"][:3],
                }
            )

        if "purchase_history" in user_data:
            recommendations.append(
                {
                    "type": "purchase_based",
                    "message": "Customers who bought similar items also bought:",
                    "items": ["Related item 1", "Related item 2"],
                }
            )

        return recommendations

    # Technical Implementation Methods

    def format_message(
        self, message_type: str, payload: Dict[str, Any], priority: str = "medium"
    ) -> Dict[str, Any]:
        """Format a message according to the standard protocol."""
        if not self.agent_coordination.correlation_id_enabled:
            return payload

        import time
        import uuid

        return {
            "message_id": str(uuid.uuid4()),
            "correlation_id": payload.get("correlation_id", str(uuid.uuid4())),
            "timestamp": int(time.time()),
            "message_type": message_type,
            "priority": priority,
            "payload": payload,
        }

    def persist_state(self, state_key: str, state_data: Dict[str, Any]) -> bool:
        """Persist state data."""
        if not self.state_persistence_enabled:
            return False

        # In a real implementation, this would save to the configured state store
        logging.info(
            f"Persisting state for {state_key}: {json.dumps(state_data)[:100]}..."
        )
        return True

    def retrieve_state(self, state_key: str) -> Dict[str, Any]:
        """Retrieve persisted state data."""
        if not self.state_persistence_enabled:
            return {}

        # In a real implementation, this would load from the configured state store
        logging.info(f"Retrieving state for {state_key}")
        return {"state_key": state_key, "dummy_data": True}

    def secure_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Secure data with encryption and access control."""
        if not self.security.encryption_enabled:
            return data

        # In a real implementation, this would encrypt sensitive data
        return {
            "encrypted": True,
            "algorithm": self.security.encryption_algorithm,
            "data": f"<encrypted_{len(str(data))}_bytes>",
        }

    def track_performance(self, operation: str, duration_ms: float) -> None:
        """Track performance metrics for an operation."""
        if not self.performance_metrics_enabled:
            return

        # In a real implementation, this would record metrics
        logging.debug(f"Performance: {operation} took {duration_ms}ms")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def get_settings_with_mobile_context(mobile_context: Dict[str, Any]) -> Settings:
    """Get settings with mobile context information."""
    settings = Settings()
    settings.mobile.context = mobile_context
    return settings


def get_settings_for_agent(agent_type: str) -> Settings:
    """Get settings configured for a specific agent type."""
    settings = Settings()

    # Adjust settings based on agent type
    if agent_type == "executive":
        # Executive agents need full coordination capabilities
        settings.agent_coordination.hierarchical_enabled = True
        settings.agent_coordination.orchestration_enabled = True
        settings.agent_coordination.decision_engine_enabled = True
    elif agent_type == "market":
        # Market agents need decision engine but not orchestration
        settings.agent_coordination.hierarchical_enabled = True
        settings.agent_coordination.orchestration_enabled = False
        settings.agent_coordination.decision_engine_enabled = True
    elif agent_type == "mobile":
        # Mobile agents need mobile optimizations
        settings.mobile.battery_optimization_enabled = True
        settings.mobile.offline_mode_enabled = True
        settings.mobile.payload_optimization_enabled = True
        settings.mobile.ui_optimization_enabled = True

    return settings
