#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hybrid Recommendation Algorithm

This module implements a hybrid recommendation system that combines multiple
recommendation approaches (collaborative filtering and content-based filtering)
to provide more accurate and diverse recommendations.

The implementation supports various combination strategies and adaptive
weighting based on recommendation confidence.
"""

import heapq
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# Import our own recommendation algorithms
from fs_agt_clean.core.recommendations.algorithms.collaborative import (
    CollaborativeFiltering,
)
from fs_agt_clean.core.recommendations.algorithms.collaborative import (
    Recommendation as CFRecommendation,
)
from fs_agt_clean.core.recommendations.algorithms.content_based import (
    ContentBasedFiltering,
)
from fs_agt_clean.core.recommendations.algorithms.content_based import (
    Recommendation as CBRecommendation,
)

logger = logging.getLogger(__name__)


class CombinationStrategy(str, Enum):
    """Strategies for combining recommendations from different algorithms."""

    WEIGHTED = "weighted"  # Weighted average of scores
    SWITCHING = "switching"  # Use primary algorithm, fall back to secondary if needed
    CASCADE = "cascade"  # Refine results from one algorithm using another
    MIXED = "mixed"  # Interleave results from both algorithms
    FEATURE_COMBINED = "feature_combined"  # Combine at the feature level


@dataclass
class HybridConfig:
    """Configuration for the hybrid recommendation algorithm."""

    collaborative_weight: float = 0.7  # Weight for collaborative filtering scores
    content_based_weight: float = 0.3  # Weight for content-based filtering scores
    top_n_recommendations: int = 10  # Number of recommendations to generate
    combination_strategy: CombinationStrategy = CombinationStrategy.WEIGHTED
    min_confidence: float = 0.1  # Minimum confidence threshold
    cold_start_threshold: int = (
        5  # Number of interactions below which to use content-based
    )
    adaptive_weighting: bool = True  # Whether to adapt weights based on confidence
    diversity_factor: float = 0.2  # Factor for promoting recommendation diversity


@dataclass
class Recommendation:
    """Recommendation result with item ID, score, confidence, and source."""

    id: str
    score: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    sources: List[str] = field(default_factory=list)


class HybridRecommender:
    """
    Hybrid recommendation system that combines multiple recommendation approaches.

    This class integrates collaborative filtering and content-based filtering
    to provide more robust recommendations with higher accuracy and diversity.
    """

    def __init__(
        self,
        collaborative_model: Optional[CollaborativeFiltering] = None,
        content_based_model: Optional[ContentBasedFiltering] = None,
        config: Optional[HybridConfig] = None,
    ):
        """
        Initialize the hybrid recommender with models and configuration.

        Args:
            collaborative_model: Trained collaborative filtering model (optional)
            content_based_model: Trained content-based filtering model (optional)
            config: Configuration for the hybrid algorithm (optional)
        """
        self.config = config or HybridConfig()
        self.collaborative_model = collaborative_model
        self.content_based_model = content_based_model
        self.user_interaction_counts = {}  # Maps user IDs to interaction counts

        logger.info(
            "Initialized hybrid recommender with %s strategy",
            self.config.combination_strategy,
        )

    def fit(
        self,
        user_item_interactions: Dict[str, Dict[str, float]],
        items: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Fit both recommendation models with the given data.

        Args:
            user_item_interactions: UnifiedUser-item interaction data
            items: Item data with features
        """
        logger.info("Fitting hybrid recommendation models")

        # Count interactions per user for cold start handling
        for user_id, interactions in user_item_interactions.items():
            self.user_interaction_counts[user_id] = len(interactions)

        # Initialize and fit models if they haven't been provided
        if self.collaborative_model is None:
            self.collaborative_model = CollaborativeFiltering()
            self.collaborative_model.fit(user_item_interactions)
            logger.info("Trained collaborative filtering model")

        if self.content_based_model is None:
            self.content_based_model = ContentBasedFiltering()
            self.content_based_model.fit(items, user_item_interactions)
            logger.info("Trained content-based filtering model")

    def recommend(
        self,
        user_id: str,
        excluded_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations for a user using the hybrid approach.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations
            context: Optional context information for contextual recommendations

        Returns:
            List of recommendations with scores and confidence values
        """
        # Choose combination strategy based on configuration
        if self.config.combination_strategy == CombinationStrategy.WEIGHTED:
            return self._weighted_recommendations(user_id, excluded_ids, context)
        elif self.config.combination_strategy == CombinationStrategy.SWITCHING:
            return self._switching_recommendations(user_id, excluded_ids, context)
        elif self.config.combination_strategy == CombinationStrategy.CASCADE:
            return self._cascade_recommendations(user_id, excluded_ids, context)
        elif self.config.combination_strategy == CombinationStrategy.MIXED:
            return self._mixed_recommendations(user_id, excluded_ids, context)
        elif self.config.combination_strategy == CombinationStrategy.FEATURE_COMBINED:
            return self._feature_combined_recommendations(
                user_id, excluded_ids, context
            )
        else:
            # Default to weighted strategy
            return self._weighted_recommendations(user_id, excluded_ids, context)

    def _weighted_recommendations(
        self,
        user_id: str,
        excluded_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations using a weighted average of scores from both models.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations
            context: Optional context information

        Returns:
            List of weighted hybrid recommendations
        """
        excluded_ids = excluded_ids or []

        # Get interaction count for cold start handling
        interaction_count = self.user_interaction_counts.get(user_id, 0)

        # Adjust weights for cold start users
        cf_weight = self.config.collaborative_weight
        cb_weight = self.config.content_based_weight

        if interaction_count < self.config.cold_start_threshold:
            # For cold start users, rely more on content-based filtering
            cold_start_factor = interaction_count / self.config.cold_start_threshold
            cf_weight = self.config.collaborative_weight * cold_start_factor
            cb_weight = 1.0 - cf_weight

            logger.info(
                "Cold start user detected (%s interactions). Adjusted weights: CF=%.2f, CB=%.2f",
                interaction_count,
                cf_weight,
                cb_weight,
            )

        # Get recommendations from both models
        cf_recommendations = []
        cb_recommendations = []

        try:
            cf_recommendations = self.collaborative_model.recommend(
                user_id, excluded_ids
            )
        except Exception as e:
            logger.error("Error getting collaborative recommendations: %s", e)

        try:
            cb_recommendations = self.content_based_model.recommend_for_user(
                user_id, excluded_ids
            )
        except Exception as e:
            logger.error("Error getting content-based recommendations: %s", e)

        if not cf_recommendations and not cb_recommendations:
            logger.warning("No recommendations available for user %s", user_id)
            return []

        # If one model fails to provide recommendations, use only the other model
        if not cf_recommendations:
            logger.info("Using only content-based recommendations")
            return [
                self._convert_recommendation(rec, "content_based", 1.0)
                for rec in cb_recommendations
            ]

        if not cb_recommendations:
            logger.info("Using only collaborative recommendations")
            return [
                self._convert_recommendation(rec, "collaborative", 1.0)
                for rec in cf_recommendations
            ]

        # Combine recommendations with weighted scores
        item_scores = {}
        item_confidences = {}
        item_sources = defaultdict(list)

        # Process collaborative filtering recommendations
        for rec in cf_recommendations:
            item_id = rec.id
            if item_id in excluded_ids:
                continue

            item_scores[item_id] = rec.score * cf_weight
            item_confidences[item_id] = rec.confidence * cf_weight
            item_sources[item_id].append("collaborative")

        # Process content-based recommendations
        for rec in cb_recommendations:
            item_id = rec.id
            if item_id in excluded_ids:
                continue

            if item_id in item_scores:
                # Item already recommended by collaborative filtering
                if self.config.adaptive_weighting:
                    # Use the recommendation with higher confidence
                    cf_confidence = item_confidences[item_id] / cf_weight
                    if rec.confidence > cf_confidence:
                        # Content-based has higher confidence
                        item_scores[item_id] = (
                            item_scores[item_id] + rec.score * cb_weight * 2
                        ) / (cf_weight + cb_weight * 2)
                        item_confidences[item_id] = (
                            item_confidences[item_id] + rec.confidence * cb_weight * 2
                        ) / (cf_weight + cb_weight * 2)
                    else:
                        # Collaborative has higher confidence
                        item_scores[item_id] = (
                            item_scores[item_id] * 2 + rec.score * cb_weight
                        ) / (cf_weight * 2 + cb_weight)
                        item_confidences[item_id] = (
                            item_confidences[item_id] * 2 + rec.confidence * cb_weight
                        ) / (cf_weight * 2 + cb_weight)
                else:
                    # Simple weighted average
                    item_scores[item_id] += rec.score * cb_weight
                    item_confidences[item_id] += rec.confidence * cb_weight
            else:
                # New item from content-based filtering
                item_scores[item_id] = rec.score * cb_weight
                item_confidences[item_id] = rec.confidence * cb_weight

            item_sources[item_id].append("content_based")

        # Normalize scores for items with recommendations from both sources
        for item_id in item_scores:
            if len(item_sources[item_id]) > 1:
                # If we have recommendations from both sources, normalize by total weight
                total_weight = (
                    cf_weight if "collaborative" in item_sources[item_id] else 0
                )
                total_weight += (
                    cb_weight if "content_based" in item_sources[item_id] else 0
                )

                if total_weight > 0:
                    item_scores[item_id] /= total_weight
                    item_confidences[item_id] /= total_weight

                # Boost confidence for items recommended by multiple sources
                item_confidences[item_id] *= 1.0 + 0.2 * (
                    len(item_sources[item_id]) - 1
                )

        # Create hybrid recommendations
        hybrid_recommendations = []

        for item_id, score in item_scores.items():
            if score >= self.config.min_confidence:
                # Get metadata from either model
                metadata = None

                # Try to get from content-based model first as it usually has more metadata
                if (
                    "content_based" in item_sources[item_id]
                    and self.content_based_model.items
                ):
                    metadata = self.content_based_model.items.get(item_id)

                hybrid_recommendations.append(
                    Recommendation(
                        id=item_id,
                        score=score,
                        confidence=item_confidences[item_id],
                        metadata=metadata,
                        sources=item_sources[item_id],
                    )
                )

        # Sort by score and limit to top N
        hybrid_recommendations.sort(key=lambda x: x.score, reverse=True)

        # Apply diversity factor if configured
        if self.config.diversity_factor > 0:
            hybrid_recommendations = self._diversify_recommendations(
                hybrid_recommendations
            )

        return hybrid_recommendations[: self.config.top_n_recommendations]

    def _switching_recommendations(
        self,
        user_id: str,
        excluded_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations using a switching strategy based on user history.

        This approach uses the primary model (usually collaborative filtering) but
        switches to the secondary model for cold start users or when the primary
        model doesn't provide enough recommendations.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations
            context: Optional context information

        Returns:
            List of recommendations from the appropriate model
        """
        excluded_ids = excluded_ids or []

        # Get interaction count for cold start handling
        interaction_count = self.user_interaction_counts.get(user_id, 0)

        # For cold start users, use content-based recommendations
        if interaction_count < self.config.cold_start_threshold:
            logger.info(
                "Cold start user detected (%s interactions). Using content-based recommendations.",
                interaction_count,
            )

            cb_recommendations = self.content_based_model.recommend_for_user(
                user_id, excluded_ids
            )

            if cb_recommendations:
                return [
                    self._convert_recommendation(rec, "content_based", 1.0)
                    for rec in cb_recommendations
                ]

        # Default to collaborative filtering recommendations
        cf_recommendations = self.collaborative_model.recommend(user_id, excluded_ids)

        # If collaborative filtering produced enough recommendations, use those
        if len(cf_recommendations) >= self.config.top_n_recommendations / 2:
            return [
                self._convert_recommendation(rec, "collaborative", 1.0)
                for rec in cf_recommendations
            ]

        # Otherwise, supplement with content-based recommendations
        logger.info(
            "Not enough collaborative recommendations (%s). Supplementing with content-based recommendations.",
            len(cf_recommendations),
        )

        cb_recommendations = self.content_based_model.recommend_for_user(
            user_id, excluded_ids
        )

        # Exclude items already recommended by collaborative filtering
        cf_item_ids = {rec.id for rec in cf_recommendations}
        cb_recommendations = [
            rec for rec in cb_recommendations if rec.id not in cf_item_ids
        ]

        # Combine recommendations
        hybrid_recommendations = [
            self._convert_recommendation(rec, "collaborative", 1.0)
            for rec in cf_recommendations
        ]

        # Add content-based recommendations to reach the desired count
        remaining_spots = self.config.top_n_recommendations - len(
            hybrid_recommendations
        )

        if remaining_spots > 0 and cb_recommendations:
            for rec in cb_recommendations[:remaining_spots]:
                hybrid_recommendations.append(
                    self._convert_recommendation(rec, "content_based", 0.9)
                )

        return hybrid_recommendations

    def _cascade_recommendations(
        self,
        user_id: str,
        excluded_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations using a cascade strategy.

        This approach uses one model to generate recommendations, then refines
        them using the other model. For example, collaborative filtering provides
        a candidate set, then content-based filtering re-ranks them.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations
            context: Optional context information

        Returns:
            List of cascade-refined recommendations
        """
        excluded_ids = excluded_ids or []

        # Step 1: Generate candidate recommendations using collaborative filtering
        candidate_recs = self.collaborative_model.recommend(user_id, excluded_ids)

        if not candidate_recs:
            logger.info(
                "No collaborative recommendations available. Using content-based."
            )
            cb_recommendations = self.content_based_model.recommend_for_user(
                user_id, excluded_ids
            )
            return [
                self._convert_recommendation(rec, "content_based", 1.0)
                for rec in cb_recommendations
            ]

        # Step 2: Extract candidate item IDs for refinement
        candidate_items = [rec.id for rec in candidate_recs]
        candidate_scores = {rec.id: rec.score for rec in candidate_recs}
        candidate_confidences = {rec.id: rec.confidence for rec in candidate_recs}

        # Step 3: Generate content-based similarities for these items
        item_similarities = {}
        for item_id in candidate_items:
            # Skip items that are not in the content-based model's dataset
            if item_id not in self.content_based_model.item_index_map:
                continue

            # Get similar items for this candidate
            similar_items = self.content_based_model.similar_items(
                item_id, excluded_ids + candidate_items
            )

            # Store similarities
            item_similarities[item_id] = {rec.id: rec.score for rec in similar_items}

        # Step 4: Re-rank candidate items based on their content similarity
        reranked_scores = {}
        reranked_confidences = {}

        for item_id in candidate_items:
            # Start with the collaborative filtering score
            cf_score = candidate_scores[item_id]
            cf_confidence = candidate_confidences[item_id]

            # Get content-based similarity boost
            content_boost = 0
            if item_id in item_similarities:
                # Average similarity to other candidate items
                similarities = item_similarities[item_id].values()
                if similarities:
                    content_boost = sum(similarities) / len(similarities)

            # Combine scores (weighted average with emphasis on collaborative filtering)
            reranked_scores[item_id] = cf_score * 0.8 + content_boost * 0.2

            # Adjust confidence based on content similarity
            reranked_confidences[item_id] = cf_confidence * (1.0 + content_boost * 0.5)

        # Step 5: Create hybrid recommendations
        hybrid_recommendations = []

        for item_id in candidate_items:
            # Get metadata from content-based model if available
            metadata = None
            if (
                self.content_based_model.items
                and item_id in self.content_based_model.items
            ):
                metadata = self.content_based_model.items.get(item_id)

            hybrid_recommendations.append(
                Recommendation(
                    id=item_id,
                    score=reranked_scores.get(item_id, candidate_scores[item_id]),
                    confidence=reranked_confidences.get(
                        item_id, candidate_confidences[item_id]
                    ),
                    metadata=metadata,
                    sources=["collaborative", "content_based_refinement"],
                )
            )

        # Sort by reranked score and limit to top N
        hybrid_recommendations.sort(key=lambda x: x.score, reverse=True)

        return hybrid_recommendations[: self.config.top_n_recommendations]

    def _mixed_recommendations(
        self,
        user_id: str,
        excluded_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations by interleaving results from both models.

        This approach alternates between recommendations from both models to
        create a diverse set of recommendations.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations
            context: Optional context information

        Returns:
            List of interleaved recommendations
        """
        excluded_ids = excluded_ids or []

        # Get recommendations from both models
        cf_recommendations = self.collaborative_model.recommend(user_id, excluded_ids)
        cb_recommendations = self.content_based_model.recommend_for_user(
            user_id, excluded_ids
        )

        if not cf_recommendations and not cb_recommendations:
            logger.warning("No recommendations available for user %s", user_id)
            return []

        # Convert to hybrid recommendation format
        cf_hybrid_recs = [
            self._convert_recommendation(rec, "collaborative", 1.0)
            for rec in cf_recommendations
        ]
        cb_hybrid_recs = [
            self._convert_recommendation(rec, "content_based", 1.0)
            for rec in cb_recommendations
        ]

        # Create interleaved recommendations
        interleaved_recommendations = []

        # Calculate relative weights for each source based on configuration
        cf_ratio = self.config.collaborative_weight / (
            self.config.collaborative_weight + self.config.content_based_weight
        )
        cb_ratio = 1.0 - cf_ratio

        # Calculate how many recommendations to take from each source
        cf_count = int(self.config.top_n_recommendations * cf_ratio)
        cb_count = self.config.top_n_recommendations - cf_count

        # Use sets to track already added items
        added_items = set()

        # Add top collaborative recommendations
        for rec in cf_hybrid_recs:
            if (
                rec.id not in added_items
                and len(interleaved_recommendations) < cf_count
            ):
                interleaved_recommendations.append(rec)
                added_items.add(rec.id)

        # Add top content-based recommendations
        for rec in cb_hybrid_recs:
            if (
                rec.id not in added_items
                and len(interleaved_recommendations) < self.config.top_n_recommendations
            ):
                interleaved_recommendations.append(rec)
                added_items.add(rec.id)

        # If we still need more recommendations, take from the remaining pool
        remaining_cf = [rec for rec in cf_hybrid_recs if rec.id not in added_items]
        remaining_cb = [rec for rec in cb_hybrid_recs if rec.id not in added_items]

        # Alternate between sources until we have enough
        cf_idx, cb_idx = 0, 0
        while len(interleaved_recommendations) < self.config.top_n_recommendations:
            if cf_idx < len(remaining_cf) and (
                cb_idx >= len(remaining_cb) or cf_idx <= cb_idx
            ):
                interleaved_recommendations.append(remaining_cf[cf_idx])
                added_items.add(remaining_cf[cf_idx].id)
                cf_idx += 1
            elif cb_idx < len(remaining_cb):
                interleaved_recommendations.append(remaining_cb[cb_idx])
                added_items.add(remaining_cb[cb_idx].id)
                cb_idx += 1
            else:
                # No more recommendations available
                break

        # Sort by score
        interleaved_recommendations.sort(key=lambda x: x.score, reverse=True)

        return interleaved_recommendations

    def _feature_combined_recommendations(
        self,
        user_id: str,
        excluded_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations by combining features from both approaches.

        This is an advanced approach that requires access to the internal
        features of both models. Currently implemented as a weighted approach.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations
            context: Optional context information

        Returns:
            List of feature-combined recommendations
        """
        # This approach is complex and requires deep integration with both models
        # For now, fall back to weighted recommendations
        logger.info(
            "Feature-combined approach not fully implemented. Using weighted approach."
        )
        return self._weighted_recommendations(user_id, excluded_ids, context)

    def _convert_recommendation(
        self,
        recommendation: Union[CFRecommendation, CBRecommendation],
        source: str,
        weight: float = 1.0,
    ) -> Recommendation:
        """
        Convert a model-specific recommendation to a hybrid recommendation.

        Args:
            recommendation: Original recommendation from a specific model
            source: Source model ("collaborative" or "content_based")
            weight: Weight to apply to the score (default 1.0)

        Returns:
            Hybrid recommendation
        """
        return Recommendation(
            id=recommendation.id,
            score=recommendation.score * weight,
            confidence=recommendation.confidence * weight,
            metadata=recommendation.metadata,
            sources=[source],
        )

    def _diversify_recommendations(
        self, recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        Apply diversity optimization to avoid recommending too many similar items.

        Args:
            recommendations: List of recommendations to diversify

        Returns:
            Diversified list of recommendations
        """
        if not recommendations or len(recommendations) <= 1:
            return recommendations

        # Simple greedy diversity approach
        # Start with the highest scored item
        diversified = [recommendations[0]]
        candidates = recommendations[1:]

        # Get the sources and category information for diversification
        selected_sources = set(diversified[0].sources)
        selected_categories = set()

        if diversified[0].metadata and "category" in diversified[0].metadata:
            category = diversified[0].metadata["category"]
            if isinstance(category, list):
                selected_categories.update(category)
            else:
                selected_categories.add(category)

        # Add remaining items with diversity consideration
        while candidates and len(diversified) < self.config.top_n_recommendations:
            # Find the best candidate considering both score and diversity
            best_candidate = None
            best_score = -1

            for i, candidate in enumerate(candidates):
                # Calculate base score
                score = candidate.score

                # Apply diversity boost based on different sources
                source_diversity = 0
                for source in candidate.sources:
                    if source not in selected_sources:
                        source_diversity += 0.1

                # Apply diversity boost based on different categories
                category_diversity = 0
                if candidate.metadata and "category" in candidate.metadata:
                    category = candidate.metadata["category"]
                    if isinstance(category, list):
                        different_categories = [
                            c for c in category if c not in selected_categories
                        ]
                        category_diversity = len(different_categories) * 0.05
                    elif category not in selected_categories:
                        category_diversity = 0.1

                # Apply diversity factor
                diversity_boost = (
                    source_diversity + category_diversity
                ) * self.config.diversity_factor
                adjusted_score = score * (1.0 + diversity_boost)

                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_candidate = (i, candidate)

            if best_candidate:
                idx, candidate = best_candidate
                diversified.append(candidate)
                candidates.pop(idx)

                # Update selected sources and categories
                selected_sources.update(candidate.sources)
                if candidate.metadata and "category" in candidate.metadata:
                    category = candidate.metadata["category"]
                    if isinstance(category, list):
                        selected_categories.update(category)
                    else:
                        selected_categories.add(category)
            else:
                break

        return diversified

    def evaluate(
        self, test_interactions: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Evaluate the hybrid recommendation algorithm on test data.

        Args:
            test_interactions: Test user-item interactions

        Returns:
            Dictionary with evaluation metrics
        """
        precision_sum = 0.0
        recall_sum = 0.0
        f1_sum = 0.0
        user_count = 0

        for user_id, user_items in test_interactions.items():
            if not user_items:
                continue

            # Get items the user has actually interacted with
            actual_items = set(user_items.keys())

            # Generate recommendations for this user
            recommendations = self.recommend(user_id)
            recommended_items = {rec.id for rec in recommendations}

            # Calculate precision and recall
            if recommended_items:
                correctly_recommended = actual_items.intersection(recommended_items)
                precision = len(correctly_recommended) / len(recommended_items)
                recall = len(correctly_recommended) / len(actual_items)

                precision_sum += precision
                recall_sum += recall

                if precision + recall > 0:
                    f1 = 2 * precision * recall / (precision + recall)
                    f1_sum += f1

            user_count += 1

        if user_count == 0:
            return {"precision": 0, "recall": 0, "f1": 0}

        return {
            "precision": precision_sum / user_count,
            "recall": recall_sum / user_count,
            "f1": f1_sum / user_count,
        }
