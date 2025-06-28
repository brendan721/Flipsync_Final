#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Collaborative Filtering Recommendation Algorithm

This module implements user-based and item-based collaborative filtering
techniques for generating recommendations based on user-item interaction
patterns.

The implementation supports multiple similarity metrics and provides
confidence scores with recommendations.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial.distance import cosine

logger = logging.getLogger(__name__)


class SimilarityMetric(str, Enum):
    """Supported similarity metrics for collaborative filtering."""

    COSINE = "cosine"
    PEARSON = "pearson"
    JACCARD = "jaccard"
    EUCLIDEAN = "euclidean"


class FilteringType(str, Enum):
    """Types of collaborative filtering approaches."""

    USER_BASED = "user_based"
    ITEM_BASED = "item_based"


@dataclass
class RecommendationConfig:
    """Configuration for the collaborative filtering algorithm."""

    min_similarity: float = 0.1  # Minimum similarity threshold
    top_n_similar: int = 20  # Number of similar users/items to consider
    top_n_recommendations: int = 10  # Number of recommendations to generate
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    filtering_type: FilteringType = FilteringType.USER_BASED
    min_interactions: int = 5  # Minimum interactions required
    normalize_scores: bool = True  # Whether to normalize recommendation scores


@dataclass
class Recommendation:
    """Recommendation result with item/user ID, score, and confidence."""

    id: str
    score: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


class CollaborativeFiltering:
    """
    Collaborative filtering recommendation algorithm implementation.

    This class provides both user-based and item-based collaborative
    filtering implementations with various similarity metrics and
    configuration options.
    """

    def __init__(self, config: Optional[RecommendationConfig] = None):
        """
        Initialize collaborative filtering with optional configuration.

        Args:
            config: Configuration for the algorithm (optional)
        """
        self.config = config or RecommendationConfig()
        self.user_item_matrix = None
        self.item_user_matrix = None
        self.user_similarity_matrix = None
        self.item_similarity_matrix = None
        self.user_index_map = {}  # Maps user IDs to matrix indices
        self.item_index_map = {}  # Maps item IDs to matrix indices
        self.index_user_map = {}  # Maps matrix indices to user IDs
        self.index_item_map = {}  # Maps matrix indices to item IDs

        logger.info(
            "Initialized collaborative filtering with %s approach",
            self.config.filtering_type,
        )

    def fit(self, user_item_interactions: Dict[str, Dict[str, float]]) -> None:
        """
        Build the user-item matrix and compute similarity matrices.

        Args:
            user_item_interactions: Nested dictionary with user IDs as keys,
                item IDs as inner keys, and ratings/interaction values as inner values
        """
        logger.info("Building user-item matrices for collaborative filtering")

        # Build user and item index mappings
        users = list(user_item_interactions.keys())
        items = set()
        for user_items in user_item_interactions.values():
            items.update(user_items.keys())
        items = list(items)

        self.user_index_map = {user: idx for idx, user in enumerate(users)}
        self.item_index_map = {item: idx for idx, item in enumerate(items)}
        self.index_user_map = {idx: user for user, idx in self.user_index_map.items()}
        self.index_item_map = {idx: item for item, idx in self.item_index_map.items()}

        # Build sparse matrices for efficiency
        rows, cols, data = [], [], []
        for user, user_items in user_item_interactions.items():
            if user in self.user_index_map:
                user_idx = self.user_index_map[user]
                for item, rating in user_items.items():
                    if item in self.item_index_map:
                        item_idx = self.item_index_map[item]
                        rows.append(user_idx)
                        cols.append(item_idx)
                        data.append(float(rating))

        n_users = len(self.user_index_map)
        n_items = len(self.item_index_map)

        # Create sparse matrices
        self.user_item_matrix = csr_matrix(
            (data, (rows, cols)), shape=(n_users, n_items)
        )
        self.item_user_matrix = self.user_item_matrix.T

        # Compute similarity matrices based on configuration
        self._compute_similarity_matrices()

        logger.info(
            "Built user-item matrix with %s users and %s items", n_users, n_items
        )

    def _compute_similarity_matrices(self) -> None:
        """Compute similarity matrices based on the configured similarity metric."""
        logger.info(
            "Computing similarity matrices using %s metric",
            self.config.similarity_metric,
        )

        if self.user_item_matrix is None or self.item_user_matrix is None:
            raise ValueError("Matrices not initialized. Call fit() first.")

        # Compute appropriate similarity matrix based on filtering type
        if self.config.filtering_type == FilteringType.USER_BASED:
            self.user_similarity_matrix = self._compute_similarity(
                self.user_item_matrix
            )
            logger.info(
                "Computed user similarity matrix with shape %s",
                self.user_similarity_matrix.shape,
            )
        else:
            self.item_similarity_matrix = self._compute_similarity(
                self.item_user_matrix
            )
            logger.info(
                "Computed item similarity matrix with shape %s",
                self.item_similarity_matrix.shape,
            )

    def _compute_similarity(self, matrix: csr_matrix) -> np.ndarray:
        """
        Compute similarity matrix based on the specified metric.

        Args:
            matrix: Input matrix (user-item or item-user)

        Returns:
            Similarity matrix
        """
        n_vectors = matrix.shape[0]
        similarity_matrix = np.zeros((n_vectors, n_vectors))

        # Compute similarities based on the chosen metric
        if self.config.similarity_metric == SimilarityMetric.COSINE:
            # Optimize computation for sparse matrices
            matrix_normalized = matrix.copy()
            # Get L2 norm for each row
            row_norms = np.sqrt(matrix.power(2).sum(axis=1).A1)
            # Avoid division by zero
            row_norms[row_norms == 0] = 1.0
            # Normalize each row by its L2 norm
            for i in range(n_vectors):
                matrix_normalized.data[
                    matrix_normalized.indptr[i] : matrix_normalized.indptr[i + 1]
                ] /= row_norms[i]
            # Compute similarities
            similarity_matrix = (matrix_normalized @ matrix_normalized.T).toarray()
            np.fill_diagonal(similarity_matrix, 1.0)

        elif self.config.similarity_metric == SimilarityMetric.PEARSON:
            # Center the data (subtract mean of each row)
            matrix_centered = matrix.copy()
            means = matrix.sum(axis=1).A1 / (matrix != 0).sum(axis=1).A1
            means[np.isnan(means)] = 0
            for i in range(n_vectors):
                if means[i] != 0:
                    row_indices = slice(matrix.indptr[i], matrix.indptr[i + 1])
                    matrix_centered.data[row_indices] -= means[i]
            # Compute similarities using centered data
            norm = np.sqrt(np.sum(matrix_centered.power(2), axis=1).A1)
            norm[norm == 0] = 1.0
            similarity_matrix = (
                matrix_centered @ matrix_centered.T
            ).toarray() / np.outer(norm, norm)
            np.fill_diagonal(similarity_matrix, 1.0)

        elif self.config.similarity_metric == SimilarityMetric.JACCARD:
            # For Jaccard, we only care about interaction existence, not values
            binary_matrix = matrix.copy()
            binary_matrix.data = np.ones_like(binary_matrix.data)
            for i in range(n_vectors):
                for j in range(i, n_vectors):
                    set_i = set(binary_matrix[i].indices)
                    set_j = set(binary_matrix[j].indices)
                    if not set_i and not set_j:
                        similarity_matrix[i, j] = similarity_matrix[j, i] = 0
                    else:
                        intersection = len(set_i.intersection(set_j))
                        union = len(set_i.union(set_j))
                        similarity_matrix[i, j] = similarity_matrix[j, i] = (
                            intersection / union
                        )

        elif self.config.similarity_metric == SimilarityMetric.EUCLIDEAN:
            # Compute Euclidean distance and convert to similarity
            for i in range(n_vectors):
                for j in range(i, n_vectors):
                    vec_i = matrix[i].toarray().flatten()
                    vec_j = matrix[j].toarray().flatten()
                    # Only consider items that both users have rated
                    mask = np.logical_and(vec_i != 0, vec_j != 0)
                    if mask.sum() > 0:
                        distance = np.sqrt(np.sum((vec_i[mask] - vec_j[mask]) ** 2))
                        # Convert distance to similarity: 1 / (1 + distance)
                        similarity = 1 / (1 + distance)
                        similarity_matrix[i, j] = similarity_matrix[j, i] = similarity
                    else:
                        similarity_matrix[i, j] = similarity_matrix[j, i] = 0

        # Apply threshold
        similarity_matrix[similarity_matrix < self.config.min_similarity] = 0

        return similarity_matrix

    def recommend(
        self, user_or_item_id: str, excluded_ids: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Generate recommendations for a user or similar items for an item.

        Args:
            user_or_item_id: UnifiedUser ID (for user-based) or item ID (for item-based)
            excluded_ids: IDs to exclude from recommendations (e.g., already purchased)

        Returns:
            List of recommendations with scores and confidence values
        """
        if self.config.filtering_type == FilteringType.USER_BASED:
            return self._user_based_recommend(user_or_item_id, excluded_ids)
        else:
            return self._item_based_recommend(user_or_item_id, excluded_ids)

    def _user_based_recommend(
        self, user_id: str, excluded_ids: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Generate recommendations for a user based on similar users.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of item recommendations
        """
        if user_id not in self.user_index_map:
            logger.warning("UnifiedUser %s not found in training data", user_id)
            return []

        excluded_indices = set()
        if excluded_ids:
            excluded_indices = {
                self.item_index_map[item_id]
                for item_id in excluded_ids
                if item_id in self.item_index_map
            }

        user_idx = self.user_index_map[user_id]
        user_vector = self.user_item_matrix[user_idx].toarray().flatten()

        # Already interacted items
        user_items = set(np.where(user_vector > 0)[0])
        excluded_indices.update(user_items)

        # Get similar users
        user_similarities = self.user_similarity_matrix[user_idx]
        similar_user_indices = np.argsort(user_similarities)[::-1]

        # Limit to top N similar users
        similar_user_indices = similar_user_indices[: self.config.top_n_similar]

        # Remove users with similarity below threshold
        similar_user_indices = similar_user_indices[
            user_similarities[similar_user_indices] >= self.config.min_similarity
        ]

        if len(similar_user_indices) == 0:
            logger.warning("No similar users found for user %s", user_id)
            return []

        # Compute weighted ratings for each item
        n_items = self.user_item_matrix.shape[1]
        weighted_ratings = np.zeros(n_items)
        similarity_sums = np.zeros(n_items)

        for similar_user_idx in similar_user_indices:
            similarity = user_similarities[similar_user_idx]
            if similarity <= 0:
                continue

            similar_user_vector = (
                self.user_item_matrix[similar_user_idx].toarray().flatten()
            )

            # Update weighted ratings for items the similar user has interacted with
            for item_idx in np.where(similar_user_vector > 0)[0]:
                if item_idx not in excluded_indices:
                    rating = similar_user_vector[item_idx]
                    weighted_ratings[item_idx] += similarity * rating
                    similarity_sums[item_idx] += similarity

        # Calculate final scores and confidence
        item_scores = np.zeros(n_items)
        confidence_scores = np.zeros(n_items)

        for item_idx in range(n_items):
            if similarity_sums[item_idx] > 0:
                item_scores[item_idx] = (
                    weighted_ratings[item_idx] / similarity_sums[item_idx]
                )
                # Confidence based on number of similar users who rated this item
                n_ratings = np.sum(self.user_item_matrix[:, item_idx].toarray() > 0)
                confidence_scores[item_idx] = min(
                    1.0, n_ratings / self.config.min_interactions
                )

        # Get top N recommendations
        recommended_indices = np.where(item_scores > 0)[0]
        top_indices = recommended_indices[
            np.argsort(item_scores[recommended_indices])[::-1]
        ]
        top_indices = top_indices[: self.config.top_n_recommendations]

        # Create recommendation objects
        recommendations = []
        for idx in top_indices:
            item_id = self.index_item_map[idx]
            score = float(item_scores[idx])
            confidence = float(confidence_scores[idx])
            recommendations.append(
                Recommendation(id=item_id, score=score, confidence=confidence)
            )

        return recommendations

    def _item_based_recommend(
        self, item_id: str, excluded_ids: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Find similar items based on user interaction patterns.

        Args:
            item_id: Item ID to find similar items for
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of similar item recommendations
        """
        if item_id not in self.item_index_map:
            logger.warning("Item %s not found in training data", item_id)
            return []

        excluded_indices = set()
        if excluded_ids:
            excluded_indices = {
                self.item_index_map[excluded_id]
                for excluded_id in excluded_ids
                if excluded_id in self.item_index_map
            }

        item_idx = self.item_index_map[item_id]
        excluded_indices.add(item_idx)  # Exclude the input item itself

        # Get similar items
        item_similarities = self.item_similarity_matrix[item_idx]
        similar_item_indices = np.argsort(item_similarities)[::-1]

        # Filter and limit to top N
        filtered_indices = [
            idx
            for idx in similar_item_indices
            if idx not in excluded_indices
            and item_similarities[idx] >= self.config.min_similarity
        ]
        filtered_indices = filtered_indices[: self.config.top_n_recommendations]

        if not filtered_indices:
            logger.warning("No similar items found for item %s", item_id)
            return []

        # Create recommendation objects
        recommendations = []
        for idx in filtered_indices:
            similar_item_id = self.index_item_map[idx]
            similarity = float(item_similarities[idx])

            # For item-based, the confidence is based on the number of co-occurrences
            co_occurrence = np.sum(
                np.logical_and(
                    self.item_user_matrix[item_idx].toarray() > 0,
                    self.item_user_matrix[idx].toarray() > 0,
                )
            )
            total_users = np.sum(self.item_user_matrix[item_idx].toarray() > 0)
            confidence = min(1.0, co_occurrence / max(1, total_users))

            recommendations.append(
                Recommendation(
                    id=similar_item_id, score=similarity, confidence=float(confidence)
                )
            )

        return recommendations

    def evaluate(
        self, test_interactions: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Evaluate the recommendation algorithm on test data.

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
            if user_id not in self.user_index_map or not user_items:
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
