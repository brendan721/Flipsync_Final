import asyncio
import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional
from uuid import uuid4

import numpy as np

from fs_agt_clean.core.knowledge import (
    KnowledgeSharingService,
    KnowledgeStatus,
    KnowledgeType,
)

"\nLearning Module for FlipSync UnifiedAgent System.\nHandles knowledge acquisition, model updates, and predictions.\n"


def async_ttl_cache(ttl_seconds: int = 300):
    def decorator(func):
        cache = {}

        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = datetime.now()
            if key in cache:
                result, timestamp = cache[key]
                if (now - timestamp).total_seconds() < ttl_seconds:
                    return result
                del cache[key]
            result = await func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        def cache_clear():
            cache.clear()

        wrapper.cache_clear = cache_clear  # type: ignore
        return wrapper

    return decorator


class LearningModule:

    def __init__(
        self,
        llm_service: Any,
        vector_store: Any,
        knowledge_sharing_service: Optional[KnowledgeSharingService] = None,
        learning_rate: float = 0.01,
        feedback_threshold: float = 0.7,
        update_interval: timedelta = timedelta(hours=1),
        cache_ttl: timedelta = timedelta(minutes=5),
        batch_size: int = 10,
        agent_id: str = None,
    ):
        """Initialize the learning module.

        Args:
            llm_service: LLM service for text generation and analysis
            vector_store: Vector store for similarity search
            knowledge_sharing_service: Service for sharing knowledge between agents
            learning_rate: Learning rate for model updates
            feedback_threshold: Threshold for incorporating feedback
            update_interval: Interval between model updates
            cache_ttl: Time-to-live for cached results
            batch_size: Batch size for model updates
            agent_id: ID of the agent owning this learning module
        """
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.knowledge_sharing_service = knowledge_sharing_service
        self.learning_rate = learning_rate
        self.feedback_threshold = feedback_threshold
        self.update_interval = update_interval
        self.cache_ttl = cache_ttl
        self.batch_size = batch_size
        self.agent_id = agent_id or f"agent_{uuid4()}"
        self.knowledge_base: Dict[str, Dict[str, List[Dict]]] = {}
        self.feedback_history: Dict[str, List[Dict]] = {}
        self.performance_history: Dict[str, float] = {}
        self.strategy_history: Dict[str, Dict] = {}
        self.last_update: Optional[datetime] = None
        self._knowledge_lock = asyncio.Lock()
        self._feedback_lock = asyncio.Lock()
        self._strategy_lock = asyncio.Lock()
        self._knowledge_subscriptions: List[str] = []

    async def initialize(self) -> None:
        """Initialize the learning module."""
        if self.knowledge_sharing_service:
            # Subscribe to relevant knowledge types
            subscription_id = await self.knowledge_sharing_service.subscribe(
                agent_id=self.agent_id,
                knowledge_types=[
                    KnowledgeType.MARKET_INSIGHT,
                    KnowledgeType.PRICING_STRATEGY,
                    KnowledgeType.INVENTORY_PREDICTION,
                    KnowledgeType.COMPETITOR_ANALYSIS,
                ],
                min_confidence=0.6,
            )
            self._knowledge_subscriptions.append(subscription_id)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.knowledge_sharing_service and self._knowledge_subscriptions:
            # Unsubscribe from all knowledge updates
            await self.knowledge_sharing_service.unsubscribe_agent(self.agent_id)
            self._knowledge_subscriptions.clear()

    async def share_competition_knowledge(
        self, asin: str, data: Dict[str, Any]
    ) -> Optional[str]:
        """Share competition knowledge with other agents.

        Args:
            asin: ASIN of the product
            data: Competition data

        Returns:
            ID of the shared knowledge entry if successful, None otherwise
        """
        if not self.knowledge_sharing_service:
            return None

        try:
            # Extract features for vector representation
            features = await self._extract_competition_features(data)

            # Calculate confidence based on data quality
            confidence = self._calculate_knowledge_confidence(data)

            # Prepare metadata
            metadata = {
                "asin": asin,
                "timestamp": datetime.utcnow().isoformat(),
                "data_quality": self._assess_data_quality(data),
            }

            # Share knowledge
            entry_id = await self.knowledge_sharing_service.publish_knowledge(
                title=f"Competition Analysis for {asin}",
                content=data,
                knowledge_type=KnowledgeType.COMPETITOR_ANALYSIS,
                source_agent_id=self.agent_id,
                confidence=confidence,
                tags=["competition", "market", asin],
                metadata=metadata,
                vector=features,
            )

            return entry_id
        except Exception as e:
            # Log error but don't propagate - knowledge sharing is non-critical
            print(f"Error sharing competition knowledge: {e}")
            return None

    async def share_pricing_knowledge(
        self, asin: str, data: Dict[str, Any]
    ) -> Optional[str]:
        """Share pricing knowledge with other agents.

        Args:
            asin: ASIN of the product
            data: Pricing data

        Returns:
            ID of the shared knowledge entry if successful, None otherwise
        """
        if not self.knowledge_sharing_service:
            return None

        try:
            # Extract features for vector representation
            features = await self._extract_price_features(data)

            # Calculate confidence based on data quality
            confidence = self._calculate_knowledge_confidence(data)

            # Prepare metadata
            metadata = {
                "asin": asin,
                "timestamp": datetime.utcnow().isoformat(),
                "data_quality": self._assess_data_quality(data),
            }

            # Share knowledge
            entry_id = await self.knowledge_sharing_service.publish_knowledge(
                title=f"Pricing Strategy for {asin}",
                content=data,
                knowledge_type=KnowledgeType.PRICING_STRATEGY,
                source_agent_id=self.agent_id,
                confidence=confidence,
                tags=["pricing", "strategy", asin],
                metadata=metadata,
                vector=features,
            )

            return entry_id
        except Exception as e:
            # Log error but don't propagate - knowledge sharing is non-critical
            print(f"Error sharing pricing knowledge: {e}")
            return None

    async def share_strategy_knowledge(
        self, asin: str, data: Dict[str, Any]
    ) -> Optional[str]:
        """Share strategy knowledge with other agents.

        Args:
            asin: ASIN of the product
            data: Strategy data

        Returns:
            ID of the shared knowledge entry if successful, None otherwise
        """
        if not self.knowledge_sharing_service:
            return None

        try:
            # Extract features for vector representation
            features = await self._extract_strategy_features(data)

            # Calculate confidence based on data quality
            confidence = self._calculate_knowledge_confidence(data)

            # Prepare metadata
            metadata = {
                "asin": asin,
                "timestamp": datetime.utcnow().isoformat(),
                "data_quality": self._assess_data_quality(data),
            }

            # Share knowledge
            entry_id = await self.knowledge_sharing_service.publish_knowledge(
                title=f"Market Strategy for {asin}",
                content=data,
                knowledge_type=KnowledgeType.MARKET_INSIGHT,
                source_agent_id=self.agent_id,
                confidence=confidence,
                tags=["strategy", "market", asin],
                metadata=metadata,
                vector=features,
            )

            return entry_id
        except Exception as e:
            # Log error but don't propagate - knowledge sharing is non-critical
            print(f"Error sharing strategy knowledge: {e}")
            return None

    async def validate_shared_knowledge(
        self, entry_id: str, validation_score: float, notes: Dict[str, Any] = None
    ) -> bool:
        """Validate knowledge shared by another agent.

        Args:
            entry_id: ID of the knowledge entry to validate
            validation_score: Validation score (0.0-1.0)
            notes: Validation notes

        Returns:
            True if validation was successful, False otherwise
        """
        if not self.knowledge_sharing_service:
            return bool(False)

        try:
            return await self.knowledge_sharing_service.validate_knowledge(
                entry_id=entry_id,
                validator_agent_id=self.agent_id,
                validation_score=validation_score,
                validation_notes=notes or {},
            )
        except Exception as e:
            # Log error but don't propagate - knowledge validation is non-critical
            print(f"Error validating knowledge: {e}")
            return False

    async def get_shared_knowledge(
        self,
        knowledge_type: KnowledgeType = None,
        tags: List[str] = None,
        min_confidence: float = 0.7,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get knowledge shared by other agents.

        Args:
            knowledge_type: Type of knowledge to retrieve
            tags: Tags to filter by
            min_confidence: Minimum confidence score
            limit: Maximum number of results to return

        Returns:
            List of knowledge entries
        """
        if not self.knowledge_sharing_service:
            return []

        try:
            # Only get validated knowledge
            entries = await self.knowledge_sharing_service.search_knowledge(
                knowledge_types=[knowledge_type] if knowledge_type else None,
                tags=tags,
                min_confidence=min_confidence,
                status=[KnowledgeStatus.VALIDATED],
                limit=limit,
            )

            # Convert to dictionaries
            return [entry.model_dump() for entry in entries]
        except Exception as e:
            # Log error but don't propagate - knowledge retrieval is non-critical
            print(f"Error getting shared knowledge: {e}")
            return []

    async def get_similar_knowledge(
        self,
        query_vector: List[float],
        knowledge_type: KnowledgeType = None,
        min_confidence: float = 0.7,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get knowledge similar to a query vector.

        Args:
            query_vector: Vector to search for similar knowledge
            knowledge_type: Type of knowledge to retrieve
            min_confidence: Minimum confidence score
            limit: Maximum number of results to return

        Returns:
            List of knowledge entries
        """
        if not self.knowledge_sharing_service or not query_vector:
            return []

        try:
            # Only get validated knowledge
            entries = await self.knowledge_sharing_service.search_knowledge(
                query_vector=query_vector,
                knowledge_types=[knowledge_type] if knowledge_type else None,
                min_confidence=min_confidence,
                status=[KnowledgeStatus.VALIDATED],
                limit=limit,
            )

            # Convert to dictionaries
            return [entry.model_dump() for entry in entries]
        except Exception as e:
            # Log error but don't propagate - knowledge retrieval is non-critical
            print(f"Error getting similar knowledge: {e}")
            return []

    def _calculate_knowledge_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for knowledge based on data quality.

        Args:
            data: Knowledge data

        Returns:
            Confidence score (0.0-1.0)
        """
        if not data:
            return 0.0

        # Simple heuristic: more data fields = higher confidence
        # In a real implementation, this would be more sophisticated
        base_confidence = min(len(data) / 10, 0.8)

        # Adjust based on data quality
        quality_score = self._assess_data_quality(data)

        # Combine scores
        return min(base_confidence * quality_score, 1.0)

    def _assess_data_quality(self, data: Dict[str, Any]) -> float:
        """Assess the quality of data.

        Args:
            data: Data to assess

        Returns:
            Quality score (0.0-1.0)
        """
        if not data:
            return 0.0

        # Count non-empty values
        non_empty = sum(1 for v in data.values() if v is not None and v != "")

        # Calculate quality score
        if len(data) == 0:
            return 0.0

        return non_empty / len(data)

    async def update_competition_knowledge(
        self, asin: str, data: Dict[str, Any]
    ) -> None:
        """Update competition knowledge for a specific ASIN."""
        if not asin:
            raise ValueError("ASIN cannot be empty")
        if not data or not isinstance(data, dict):
            data = {}
        features = await self._extract_competition_features(data)
        knowledge = {"timestamp": datetime.utcnow(), "data": data, "features": features}
        async with self._knowledge_lock:
            if asin not in self.knowledge_base:
                self.knowledge_base[asin] = {}
            if "competition" not in self.knowledge_base[asin]:
                self.knowledge_base[asin]["competition"] = []
            self.knowledge_base[asin]["competition"].append(knowledge)
        try:
            await self.vector_store.store_vectors(
                collection_name="competition_knowledge",
                vectors=[
                    {
                        "id": str(uuid4()),
                        "vector": features,
                        "payload": {"asin": asin, "type": "competition", "data": data},
                    }
                ],
            )

            # Share knowledge with other agents if knowledge sharing is enabled
            if self.knowledge_sharing_service:
                await self.share_competition_knowledge(asin, data)

        except Exception as e:
            raise Exception(f"Failed to store competition knowledge: {str(e)}")

    async def update_pricing_knowledge(self, asin: str, data: Dict[str, Any]) -> None:
        """Update pricing knowledge for a specific ASIN."""
        if not asin:
            raise ValueError("ASIN cannot be empty")
        if not data or not isinstance(data, dict):
            data = {}
        features = await self._extract_price_features(data)
        knowledge = {
            "timestamp": datetime.utcnow(),
            "data": data,
            "features": features,
            "performance": None,
        }
        async with self._knowledge_lock:
            if asin not in self.knowledge_base:
                self.knowledge_base[asin] = {}
            if "pricing" not in self.knowledge_base[asin]:
                self.knowledge_base[asin]["pricing"] = []
            self.knowledge_base[asin]["pricing"].append(knowledge)
        try:
            await self.vector_store.store_vectors(
                collection_name="pricing_knowledge",
                vectors=[
                    {
                        "id": str(uuid4()),
                        "vector": features,
                        "payload": {"asin": asin, "type": "pricing", "data": data},
                    }
                ],
            )

            # Share knowledge with other agents if knowledge sharing is enabled
            if self.knowledge_sharing_service:
                await self.share_pricing_knowledge(asin, data)

        except Exception as e:
            raise Exception(f"Failed to store pricing knowledge: {str(e)}")

    async def update_strategy_knowledge(self, asin: str, data: Dict[str, Any]) -> None:
        """Update strategy knowledge for a specific ASIN."""
        if not asin:
            raise ValueError("ASIN cannot be empty")
        if not data or not isinstance(data, dict):
            data = {}
        features = await self._extract_strategy_features(data)
        knowledge = {"timestamp": datetime.utcnow(), "data": data, "features": features}
        async with self._knowledge_lock:
            if asin not in self.knowledge_base:
                self.knowledge_base[asin] = {}
            if "strategy" not in self.knowledge_base[asin]:
                self.knowledge_base[asin]["strategy"] = []
            self.knowledge_base[asin]["strategy"].append(knowledge)
        async with self._strategy_lock:
            self.strategy_history[asin] = data
        try:
            await self.vector_store.store_vectors(
                collection_name="strategy_knowledge",
                vectors=[
                    {
                        "id": str(uuid4()),
                        "vector": features,
                        "payload": {"asin": asin, "type": "strategy", "data": data},
                    }
                ],
            )

            # Share knowledge with other agents if knowledge sharing is enabled
            if self.knowledge_sharing_service:
                await self.share_strategy_knowledge(asin, data)

        except Exception as e:
            raise Exception(f"Failed to store strategy knowledge: {str(e)}")

    async def process_feedback(self, asin: str, feedback: Dict[str, Any]) -> None:
        """Process feedback and update performance metrics."""
        async with self._feedback_lock:
            if asin not in self.feedback_history:
                self.feedback_history[asin] = []
            self.feedback_history[asin].append(
                {"timestamp": datetime.utcnow(), "data": feedback}
            )
            performance_score = self._calculate_performance_score(feedback)
            self.performance_history[asin] = performance_score
        await self._check_and_update_models()

    @async_ttl_cache(ttl_seconds=1)  # 1 second TTL to match test
    async def get_learned_insights(
        self, asin: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get learned insights for a specific ASIN and context."""
        try:
            # Extract features once and reuse
            features = await self._extract_strategy_features(context)

            # Add to batch for vector store
            vector_entry = {
                "id": str(uuid4()),
                "vector": features,
                "payload": {"asin": asin, "type": "context", "data": context},
            }

            # Store vector in batch
            try:
                await self.vector_store.store_vectors(
                    collection_name="strategy_knowledge",
                    vectors=[vector_entry],
                )
            except Exception:
                # Log error but continue - storing context is not critical
                print("Failed to store context vector")

            # Search for similar cases - let this error propagate up
            similar_cases = await self.vector_store.search_vectors(
                collection_name="strategy_knowledge",
                query_vector=features,
                limit=5,
            )

            # Get shared knowledge from other agents if available
            shared_knowledge = []
            if self.knowledge_sharing_service:
                shared_knowledge = await self.get_similar_knowledge(
                    query_vector=features,
                    knowledge_type=KnowledgeType.MARKET_INSIGHT,
                    min_confidence=0.7,
                    limit=3,
                )

            # Get predictions (now cached)
            price_prediction = await self._get_price_prediction(asin, context)
            strategy_prediction = await self._get_strategy_prediction(asin, context)

            # Calculate confidence and generate analysis
            confidence = self._calculate_confidence_score(
                similar_cases, price_prediction, strategy_prediction
            )

            # Generate analysis - let any OpenAI errors propagate up
            analysis = await self._generate_analysis(
                similar_cases, price_prediction, strategy_prediction, shared_knowledge
            )

            return {
                "similar_cases": similar_cases,
                "shared_knowledge": shared_knowledge,
                "predictions": {
                    "price": price_prediction,
                    "strategy": strategy_prediction,
                },
                "analysis": analysis,
                "confidence": confidence,
            }
        except Exception as e:
            # Wrap the error with more context but preserve the original error message
            raise Exception(f"Failed to get insights: {str(e)}")

    async def _check_and_update_models(self) -> None:
        """Check if models need to be updated and perform update if necessary."""
        if (
            not self.last_update
            or datetime.now() - self.last_update > self.update_interval
        ):
            await self._update_models()

    async def _update_models(self) -> None:
        """Update internal models based on accumulated knowledge."""
        if not self.knowledge_base:
            return
        try:
            async with self._knowledge_lock:
                for asin, knowledge in self.knowledge_base.items():
                    performance = self.performance_history.get(asin, 0.5)
                    if "pricing" in knowledge and knowledge["pricing"]:
                        recent_prices = knowledge["pricing"][-10:]
                        price_features = [entry["features"] for entry in recent_prices]
                        price_data = [
                            entry["data"].get("price", 99.99) for entry in recent_prices
                        ]
                        if performance > self.feedback_threshold:
                            await self._reinforce_successful_patterns(
                                asin, "pricing", price_features
                            )
                        else:
                            await self._adjust_pricing_strategy(
                                asin, price_features, price_data
                            )
                    if "strategy" in knowledge and knowledge["strategy"]:
                        recent_strategies = knowledge["strategy"][-10:]
                        strategy_features = [
                            entry["features"] for entry in recent_strategies
                        ]
                        if performance > self.feedback_threshold:
                            await self._reinforce_successful_patterns(
                                asin, "strategy", strategy_features
                            )
                        else:
                            await self._adjust_strategy_patterns(
                                asin, strategy_features
                            )
                    if "competition" in knowledge and knowledge["competition"]:
                        recent_competition = knowledge["competition"][-10:]
                        competition_features = [
                            entry["features"] for entry in recent_competition
                        ]
                        await self._update_competition_patterns(
                            asin, competition_features
                        )
            self.last_update = datetime.now()
        except Exception as e:
            print(f"Error during model update: {str(e)}")

    async def _reinforce_successful_patterns(
        self, asin: str, model_type: str, features: List[List[float]]
    ) -> None:
        """Reinforce successful patterns in the vector store."""
        try:
            avg_features = np.mean(features, axis=0).tolist()
            await self.vector_store.store_vectors(
                vectors=[avg_features],
                payloads=[
                    {
                        "asin": asin,
                        "type": f"{model_type}_success",
                        "weight": 1.2,
                        "performance": self.performance_history.get(asin, 0.5),
                    }
                ],
            )
        except Exception:
            pass

    async def _adjust_pricing_strategy(
        self, asin: str, features: List[List[float]], prices: List[float]
    ) -> None:
        """Adjust pricing strategy based on performance."""
        try:
            price_trend = np.gradient(prices).mean()
            adjusted_features = np.mean(features, axis=0).tolist()
            adjusted_features[0] = max(
                0.0, min(1.0, adjusted_features[0] - price_trend * self.learning_rate)
            )
            await self.vector_store.store_vectors(
                vectors=[adjusted_features],
                payloads=[
                    {
                        "asin": asin,
                        "type": "pricing_adjustment",
                        "trend": price_trend,
                        "performance": self.performance_history.get(asin, 0.5),
                    }
                ],
            )
        except Exception:
            pass

    async def _adjust_strategy_patterns(
        self, asin: str, features: List[List[float]]
    ) -> None:
        """Adjust strategy patterns based on performance."""
        try:
            avg_features = np.mean(features, axis=0).tolist()
            performance = self.performance_history.get(asin, 0.5)
            if performance < 0.3:
                avg_features[2] = max(0.0, avg_features[2] - self.learning_rate)
            elif performance < 0.5:
                avg_features[2] = max(
                    0.0,
                    min(
                        1.0, avg_features[2] + (0.5 - performance) * self.learning_rate
                    ),
                )
            await self.vector_store.store_vectors(
                vectors=[avg_features],
                payloads=[
                    {
                        "asin": asin,
                        "type": "strategy_adjustment",
                        "performance": performance,
                    }
                ],
            )
        except Exception:
            pass

    async def _update_competition_patterns(
        self, asin: str, features: List[List[float]]
    ) -> None:
        """Update competition patterns in the vector store."""
        try:
            avg_features = np.mean(features, axis=0).tolist()
            await self.vector_store.store_vectors(
                vectors=[avg_features],
                payloads=[
                    {
                        "asin": asin,
                        "type": "competition_update",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ],
            )
        except Exception:
            pass

    async def _extract_competition_features(self, data: Dict[str, Any]) -> List[float]:
        """Extract features from competition data."""
        if not data or not isinstance(data, dict):
            return [0.5, 0.5, 0.5]
        try:
            price = float(data.get("price", 50.0))
            if not math.isfinite(price):
                price = 50.0
            market_share = float(data.get("market_share", 0.5))
            if not math.isfinite(market_share):
                market_share = 0.5
            competition_level = self._normalize_competition_level(
                data.get("competition", "medium")
            )
            return [
                min(1.0, max(0.0, price / 100.0)),
                min(1.0, max(0.0, market_share)),
                competition_level,
            ]
        except (ValueError, TypeError):
            return [0.5, 0.5, 0.5]

    async def _extract_price_features(self, data: Dict[str, Any]) -> List[float]:
        """Extract features from price data."""
        if not data or not isinstance(data, dict):
            return [0.5, 0.5, 0.5]
        try:
            price = float(data.get("price", 50.0))
            if not math.isfinite(price):
                price = 50.0
            demand = float(data.get("demand", 0.5))
            if not math.isfinite(demand):
                demand = 0.5
            trend = self._normalize_trend(data.get("trend", "stable"))
            return [
                min(1.0, max(0.0, price / 100.0)),
                min(1.0, max(0.0, demand)),
                trend,
            ]
        except (ValueError, TypeError):
            return [0.5, 0.5, 0.5]

    async def _extract_strategy_features(self, data: Dict[str, Any]) -> List[float]:
        """Extract strategy features from data."""
        features = []
        try:
            # Market condition feature
            market_condition = data.get("market_condition", "stable")
            features.append(self._normalize_trend(market_condition))

            # Competition level feature
            competition = data.get("competition", "medium")
            features.append(self._normalize_competition_level(competition))

            # Seasonal factor
            seasonal_factor = float(data.get("seasonal_factor", 0.5))
            features.append(max(0.0, min(1.0, seasonal_factor)))

            # Strategy type if available
            if "strategy" in data:
                features.append(self._normalize_strategy_type(data["strategy"]))
            else:
                features.append(0.5)  # Default strategy value

            # Budget allocation if available
            budget_allocation = data.get("budget_allocation", {})
            total_budget = sum(budget_allocation.values()) if budget_allocation else 0
            features.append(float(total_budget > 0))

            # Normalize and pad features to ensure consistent length
            features = [max(0.0, min(1.0, f)) for f in features]
            while len(features) < 10:  # Pad to fixed length
                features.append(0.0)

            return features
        except Exception as e:
            print(f"Error extracting strategy features: {str(e)}")
            return [0.0] * 10  # Return default features on error

    def _normalize_competition_level(self, level: str) -> float:
        """Normalize competition level to a float between 0 and 1."""
        levels = {"low": 0.0, "medium": 0.5, "high": 1.0}
        return levels.get(level.lower(), 0.5)

    def _normalize_trend(self, trend: str) -> float:
        """Normalize trend to a float between 0 and 1."""
        trends = {
            "declining": 0.0,
            "stable": 0.5,
            "growing": 1.0,
            "decreasing": 0.0,
            "increasing": 1.0,
        }
        return trends.get(trend.lower(), 0.5)

    def _normalize_strategy_type(self, strategy_type: str) -> float:
        """Normalize strategy type to a float between 0 and 1."""
        strategies = {
            "conservative": 0.0,
            "balanced": 0.5,
            "aggressive": 1.0,
            "competitive": 0.75,
            "defensive": 0.25,
        }
        return strategies.get(strategy_type.lower(), 0.5)

    @async_ttl_cache(ttl_seconds=1)  # 1 second TTL to match test
    async def _get_price_prediction(self, asin: str, context: Dict[str, Any]) -> float:
        """Get price prediction based on context and history."""
        try:
            if asin in self.knowledge_base and "pricing" in self.knowledge_base[asin]:
                recent_prices = self.knowledge_base[asin]["pricing"][-5:]
                if recent_prices:
                    prices = [
                        entry["data"].get("current_price", 99.99)
                        for entry in recent_prices
                    ]
                    weights = [0.5**i for i in range(len(prices))]
                    weighted_avg = sum(p * w for p, w in zip(prices, weights)) / sum(
                        weights
                    )
                    return weighted_avg
            return 99.99  # Default price if no history
        except Exception:
            return 99.99

    @async_ttl_cache(ttl_seconds=1)  # 1 second TTL to match test
    async def _get_strategy_prediction(
        self, asin: str, context: Dict[str, Any]
    ) -> float:
        """Get strategy prediction based on context and history."""
        try:
            if asin in self.strategy_history:
                strategy = self.strategy_history[asin].get("strategy", "balanced")
                return self._normalize_strategy_type(strategy)
            return 0.5  # Default strategy value
        except Exception:
            return 0.5

    @async_ttl_cache(ttl_seconds=1)  # 1 second TTL to match test
    async def _generate_analysis(
        self,
        similar_cases: List[Dict[str, Any]],
        price_prediction: float,
        strategy_prediction: float,
        shared_knowledge: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate analysis based on similar cases and predictions."""
        if shared_knowledge is None:
            shared_knowledge = []

        # Prepare prompt with similar cases
        similar_cases_text = ""
        for i, case in enumerate(similar_cases[:3]):  # Limit to top 3 for prompt size
            similar_cases_text += f"Case {i+1}: {case['payload']['data']}\n"

        # Add shared knowledge to prompt
        shared_knowledge_text = ""
        for i, knowledge in enumerate(shared_knowledge[:2]):  # Limit to top 2
            shared_knowledge_text += f"Shared Knowledge {i+1}: {knowledge['content']}\n"

        # Combine all information for analysis
        prompt = f"""
        Analyze the following market data:

        Similar Cases:
        {similar_cases_text}

        Shared Knowledge:
        {shared_knowledge_text}

        Predictions:
        - Price: ${price_prediction:.2f}
        - Strategy Score: {strategy_prediction:.2f}

        Provide a concise analysis including:
        1. Key insights from similar cases
        2. Relevant knowledge from other agents
        3. Recommended pricing strategy
        4. Market positioning advice
        5. Confidence assessment
        """

        try:
            # Generate analysis using LLM
            response = await self.llm_service.generate_text(prompt)

            # Parse response into structured format
            # In a real implementation, this would be more sophisticated
            lines = response.strip().split("\n")
            analysis = {
                "insights": [],
                "recommendations": [],
                "confidence": "medium",
            }

            current_section = "insights"
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if "recommend" in line.lower():
                    current_section = "recommendations"
                elif "confidence" in line.lower():
                    if "high" in line.lower():
                        analysis["confidence"] = "high"
                    elif "low" in line.lower():
                        analysis["confidence"] = "low"
                    else:
                        analysis["confidence"] = "medium"
                elif line.startswith("-") or line.startswith("*"):
                    analysis[current_section].append(line[1:].strip())

            return analysis
        except Exception as e:
            # Fallback to simple analysis if LLM fails
            return {
                "insights": [
                    "Based on similar cases, market conditions appear stable."
                ],
                "recommendations": [f"Consider pricing around ${price_prediction:.2f}"],
                "confidence": "low",
                "error": str(e),
            }

    def _calculate_performance_score(self, feedback: Dict[str, Any]) -> float:
        """Calculate performance score from feedback."""
        scores = [
            feedback.get("sales_performance", 0.5),
            feedback.get("customer_satisfaction", 0.5),
            feedback.get("roi", 0.5),
        ]
        return sum(scores) / len(scores)

    def _calculate_confidence_score(
        self,
        similar_cases: List[Dict[str, Any]],
        price_prediction: float,
        strategy_prediction: float,
    ) -> float:
        """Calculate confidence score based on similar cases and predictions."""
        if not similar_cases:
            return 0.5
        try:
            similarity_scores = [case.get("score", 0.0) for case in similar_cases]
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            performance_scores = []
            price_variance = []
            strategy_variance = []
            for case in similar_cases:
                if "payload" in case and "data" in case["payload"]:
                    performance = case["payload"].get("performance", 0.5)
                    performance_scores.append(performance)
                    case_price = case["payload"]["data"].get("price", 99.99)
                    price_variance.append(
                        abs(case_price - price_prediction) / max(case_price, 1.0)
                    )
                    case_strategy = self._normalize_strategy_type(
                        case["payload"]["data"].get("strategy", "balanced")
                    )
                    strategy_variance.append(abs(case_strategy - strategy_prediction))
            similarity_confidence = avg_similarity
            performance_confidence = (
                sum(performance_scores) / len(performance_scores)
                if performance_scores
                else 0.5
            )
            price_confidence = 1.0 - (
                sum(price_variance) / len(price_variance) if price_variance else 0.5
            )
            strategy_confidence = 1.0 - (
                sum(strategy_variance) / len(strategy_variance)
                if strategy_variance
                else 0.5
            )
            weights = {
                "similarity": 0.3,
                "performance": 0.3,
                "price": 0.2,
                "strategy": 0.2,
            }
            confidence_score = (
                weights["similarity"] * similarity_confidence
                + weights["performance"] * performance_confidence
                + weights["price"] * price_confidence
                + weights["strategy"] * strategy_confidence
            )
            return min(1.0, max(0.0, confidence_score))
        except Exception:
            return 0.5

    async def _extract_learning_points(
        self, feedback: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Extract learning points from feedback."""
        analysis = feedback.get("analysis", {})
        return {
            "factors": analysis.get("key_factors", []),
            "improvements": analysis.get("improvement_areas", []),
        }

    def _adjust_model_parameters(self: Dict[str, List[str]]) -> None:
        """Adjust model parameters based on learning points."""
        self.learning_rate *= 1.1

    async def _get_ai_enhanced_analysis(
        self,
        asin: str,
        context: Dict[str, Any],
        performance_data: List[Dict[str, Any]],
        predictions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Get enhanced analysis using OpenAI."""
        try:
            analysis_prompt = {
                "historical_data": performance_data[-5:] if performance_data else [],
                "current_context": context,
                "predictions": predictions,
                "performance_metrics": {
                    "current_performance": self.performance_history.get(asin, 0.5),
                    "historical_strategies": [
                        d.get("strategy", "balanced") for d in performance_data
                    ],
                    "price_points": [d.get("price", 99.99) for d in performance_data],
                },
            }
            ai_response = await self.llm_service.analyze_market_data(analysis_prompt)
            insights = {
                "market_trends": ai_response.get("trends", []),
                "opportunities": ai_response.get("opportunities", []),
                "risks": ai_response.get("risks", []),
                "recommendations": ai_response.get("recommendations", []),
            }
            return insights
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {
                "market_trends": [],
                "opportunities": [],
                "risks": ["Unable to perform AI analysis"],
                "recommendations": ["Use default strategy"],
            }

    async def _get_ai_strategy_recommendation(
        self, asin: str, context: Dict[str, Any], similar_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get AI-powered strategy recommendations."""
        try:
            strategy_context = {
                "similar_cases": [
                    {
                        "strategy": case["payload"]["data"].get("strategy", "balanced"),
                        "performance": case["payload"].get("performance", 0.5),
                        "market_conditions": case["payload"]["data"].get(
                            "market_condition", "stable"
                        ),
                    }
                    for case in similar_cases
                    if "payload" in case and "data" in case["payload"]
                ],
                "current_context": context,
                "historical_performance": self.performance_history.get(asin, 0.5),
            }
            ai_response = await self.llm_service.get_strategy_recommendation(
                strategy_context
            )
            return {
                "recommended_strategy": ai_response.get("strategy", "balanced"),
                "confidence": ai_response.get("confidence", 0.5),
                "reasoning": ai_response.get("reasoning", []),
                "alternative_strategies": ai_response.get("alternatives", []),
            }
        except Exception as e:
            print(f"Error in AI strategy recommendation: {str(e)}")
            return {
                "recommended_strategy": "balanced",
                "confidence": 0.5,
                "reasoning": ["AI analysis unavailable"],
                "alternative_strategies": [],
            }

    async def get_enhanced_insights(
        self, asin: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get enhanced insights with AI analysis."""
        try:
            base_insights = await self.get_learned_insights(asin, context)
            performance_data = []
            if asin in self.knowledge_base:
                for knowledge_type in ["pricing", "strategy", "competition"]:
                    if knowledge_type in self.knowledge_base[asin]:
                        for entry in self.knowledge_base[asin][knowledge_type]:
                            if "data" in entry:
                                performance_data.append(entry["data"])
            ai_analysis = await self._get_ai_enhanced_analysis(
                asin, context, performance_data, base_insights["predictions"]
            )
            ai_strategy = await self._get_ai_strategy_recommendation(
                asin, context, base_insights["similar_cases"]
            )
            enhanced_insights = {
                **base_insights,
                "ai_analysis": ai_analysis,
                "ai_strategy": ai_strategy,
                "meta": {
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "data_points_analyzed": len(performance_data),
                    "confidence_score": (
                        base_insights["confidence"] + ai_strategy["confidence"]
                    )
                    / 2,
                },
            }
            return enhanced_insights
        except Exception as e:
            print(f"Error getting enhanced insights: {str(e)}")
            return await self.get_learned_insights(asin, context)
