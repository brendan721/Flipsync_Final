#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Content-Based Recommendation Algorithm

This module implements content-based filtering techniques for generating
recommendations based on item features/attributes and user preferences.

The implementation supports feature extraction, weighting, and similarity
calculation to match user profiles with items.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class FeatureType(str, Enum):
    """Types of features that can be used for content-based filtering."""

    TEXT = "text"  # Text features (descriptions, titles, etc.)
    CATEGORICAL = "categorical"  # Categorical features (genre, type, etc.)
    NUMERICAL = "numerical"  # Numerical features (price, ratings, etc.)
    TAGS = "tags"  # Tag-based features


@dataclass
class ContentBasedConfig:
    """Configuration for the content-based filtering algorithm."""

    min_similarity: float = 0.1  # Minimum similarity threshold
    top_n_recommendations: int = 10  # Number of recommendations to generate
    text_fields: List[str] = field(default_factory=lambda: ["title", "description"])
    categorical_fields: List[str] = field(default_factory=lambda: ["category", "genre"])
    numerical_fields: List[str] = field(default_factory=lambda: ["price", "rating"])
    tag_fields: List[str] = field(default_factory=lambda: ["tags", "keywords"])
    text_weight: float = 1.0  # Weight for text features
    categorical_weight: float = 1.0  # Weight for categorical features
    numerical_weight: float = 0.5  # Weight for numerical features
    tag_weight: float = 2.0  # Weight for tag features
    min_interactions: int = 3  # Minimum user interactions for profile building


@dataclass
class Recommendation:
    """Recommendation result with item ID, score, and confidence."""

    id: str
    score: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


class ContentBasedFiltering:
    """
    Content-based filtering recommendation algorithm implementation.

    This class provides a comprehensive content-based recommendation engine
    that processes various item features and user interactions to create
    personalized recommendations.
    """

    def __init__(self, config: Optional[ContentBasedConfig] = None):
        """
        Initialize content-based filtering with optional configuration.

        Args:
            config: Configuration for the algorithm (optional)
        """
        self.config = config or ContentBasedConfig()
        self.items = {}  # Dictionary of item data by item ID
        self.user_profiles = {}  # Dictionary of user profiles by user ID

        # Feature vectors
        self.text_features = None
        self.text_vectorizer = None
        self.categorical_features = None
        self.numerical_features = None
        self.tag_features = None

        # Item indices for mapping
        self.item_index_map = {}  # Maps item IDs to indices
        self.index_item_map = {}  # Maps indices to item IDs

        logger.info("Initialized content-based filtering recommendation engine")

    def fit(
        self,
        items: Dict[str, Dict[str, Any]],
        user_interactions: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> None:
        """
        Process item features and user interactions to build recommendation model.

        Args:
            items: Dictionary of items with their features (item_id -> features)
            user_interactions: Optional user-item interactions for building user profiles
                              (user_id -> {item_id: rating/interaction_strength})
        """
        logger.info("Building content-based model with %s items", len(items))
        self.items = items

        # Create item index mappings
        self._build_item_index_mappings()

        # Extract features from items
        self._extract_features()

        # Build user profiles if interactions are provided
        if user_interactions:
            self._build_user_profiles(user_interactions)
            logger.info("Built user profiles for %s users", len(self.user_profiles))

    def _build_item_index_mappings(self) -> None:
        """Create mappings between item IDs and numerical indices."""
        item_ids = list(self.items.keys())
        self.item_index_map = {item_id: idx for idx, item_id in enumerate(item_ids)}
        self.index_item_map = {
            idx: item_id for item_id, idx in self.item_index_map.items()
        }

    def _extract_features(self) -> None:
        """Extract and vectorize features from items."""
        logger.info("Extracting features from items")

        # Process text features
        if self.config.text_fields:
            self._extract_text_features()

        # Process categorical features
        if self.config.categorical_fields:
            self._extract_categorical_features()

        # Process numerical features
        if self.config.numerical_fields:
            self._extract_numerical_features()

        # Process tag features
        if self.config.tag_fields:
            self._extract_tag_features()

    def _extract_text_features(self) -> None:
        """Extract text features using TF-IDF vectorization."""
        # Combine all text fields for each item
        text_documents = []
        for item_id in sorted(self.items.keys(), key=lambda x: self.item_index_map[x]):
            item = self.items[item_id]
            item_text = " ".join(
                str(item.get(field, "")).lower()
                for field in self.config.text_fields
                if field in item
            )
            text_documents.append(item_text)

        # Vectorize text
        self.text_vectorizer = TfidfVectorizer(
            stop_words="english", max_features=1000, ngram_range=(1, 2)
        )

        if text_documents:
            try:
                self.text_features = self.text_vectorizer.fit_transform(text_documents)
                logger.info(
                    "Extracted text features with shape %s", self.text_features.shape
                )
            except Exception as e:
                logger.error("Error extracting text features: %s", e)
                self.text_features = None
        else:
            logger.warning("No text data available for feature extraction")
            self.text_features = None

    def _extract_categorical_features(self) -> None:
        """Extract categorical features using one-hot encoding."""
        # Get all unique categories for each categorical field
        categories_by_field = {}
        for field in self.config.categorical_fields:
            categories = set()
            for item in self.items.values():
                if field in item and item[field]:
                    # Handle both string and list categories
                    if isinstance(item[field], list):
                        categories.update(item[field])
                    else:
                        categories.add(item[field])
            categories_by_field[field] = sorted(categories)

        # Calculate total number of categorical features
        total_categories = sum(len(cats) for cats in categories_by_field.values())

        # Initialize feature matrix
        n_items = len(self.items)
        self.categorical_features = np.zeros((n_items, total_categories))

        # Maps field and category to column index
        category_indices = {}
        current_idx = 0
        for field, categories in categories_by_field.items():
            for category in categories:
                category_indices[(field, category)] = current_idx
                current_idx += 1

        # Fill the feature matrix
        for item_id, idx in self.item_index_map.items():
            item = self.items[item_id]
            for field in self.config.categorical_fields:
                if field in item and item[field]:
                    # Handle both string and list categories
                    if isinstance(item[field], list):
                        for category in item[field]:
                            col_idx = category_indices.get((field, category))
                            if col_idx is not None:
                                self.categorical_features[idx, col_idx] = 1.0
                    else:
                        col_idx = category_indices.get((field, item[field]))
                        if col_idx is not None:
                            self.categorical_features[idx, col_idx] = 1.0

        logger.info(
            "Extracted categorical features with shape %s",
            self.categorical_features.shape,
        )

    def _extract_numerical_features(self) -> None:
        """Extract and normalize numerical features."""
        n_items = len(self.items)
        n_fields = len(self.config.numerical_fields)

        # Initialize feature matrix
        self.numerical_features = np.zeros((n_items, n_fields))

        # Collect values for normalization
        field_values = {field: [] for field in self.config.numerical_fields}
        for item in self.items.values():
            for i, field in enumerate(self.config.numerical_fields):
                if field in item and item[field] is not None:
                    try:
                        value = float(item[field])
                        field_values[field].append(value)
                    except (ValueError, TypeError):
                        pass

        # Calculate min and max for each field
        field_stats = {}
        for field, values in field_values.items():
            if values:
                field_stats[field] = {
                    "min": min(values),
                    "max": max(values),
                    "range": max(values) - min(values),
                }

        # Fill the feature matrix with normalized values
        for item_id, idx in self.item_index_map.items():
            item = self.items[item_id]
            for i, field in enumerate(self.config.numerical_fields):
                if field in item and item[field] is not None and field in field_stats:
                    try:
                        value = float(item[field])
                        stats = field_stats[field]
                        if stats["range"] > 0:
                            # Normalize to [0, 1]
                            normalized = (value - stats["min"]) / stats["range"]
                            self.numerical_features[idx, i] = normalized
                    except (ValueError, TypeError):
                        pass

        logger.info(
            "Extracted numerical features with shape %s", self.numerical_features.shape
        )

    def _extract_tag_features(self) -> None:
        """Extract tag features using a binary encoding."""
        # Collect all unique tags
        all_tags = set()
        for item in self.items.values():
            for field in self.config.tag_fields:
                if field in item and item[field]:
                    tags = item[field]
                    # Handle different tag formats
                    if isinstance(tags, str):
                        # Handle comma-separated tags
                        tags = [tag.strip() for tag in tags.split(",")]
                    elif isinstance(tags, list):
                        tags = [str(tag).strip() for tag in tags]

                    all_tags.update(tags)

        all_tags = sorted(all_tags)
        tag_index = {tag: i for i, tag in enumerate(all_tags)}

        # Initialize feature matrix
        n_items = len(self.items)
        n_tags = len(all_tags)
        self.tag_features = np.zeros((n_items, n_tags))

        # Fill the feature matrix
        for item_id, idx in self.item_index_map.items():
            item = self.items[item_id]
            for field in self.config.tag_fields:
                if field in item and item[field]:
                    tags = item[field]
                    # Handle different tag formats
                    if isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(",")]
                    elif isinstance(tags, list):
                        tags = [str(tag).strip() for tag in tags]

                    for tag in tags:
                        if tag in tag_index:
                            self.tag_features[idx, tag_index[tag]] = 1.0

        logger.info("Extracted tag features with shape %s", self.tag_features.shape)

    def _build_user_profiles(
        self, user_interactions: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Build user profiles based on their interactions with items.

        Args:
            user_interactions: UnifiedUser-item interactions (user_id -> {item_id: rating})
        """
        for user_id, interactions in user_interactions.items():
            # Skip users with too few interactions
            if len(interactions) < self.config.min_interactions:
                continue

            # Get indices of items the user has interacted with
            item_indices = []
            item_weights = []
            for item_id, rating in interactions.items():
                if item_id in self.item_index_map:
                    item_indices.append(self.item_index_map[item_id])
                    item_weights.append(float(rating))

            # Normalize weights
            if item_weights:
                item_weights = np.array(item_weights)
                weight_sum = np.sum(item_weights)
                if weight_sum > 0:
                    item_weights = item_weights / weight_sum

                # Initialize user profile
                user_profile = {}

                # Average text features
                if self.text_features is not None:
                    user_text_profile = np.zeros(self.text_features.shape[1])
                    for idx, weight in zip(item_indices, item_weights):
                        user_text_profile += (
                            self.text_features[idx].toarray().flatten() * weight
                        )
                    user_profile["text"] = user_text_profile

                # Average categorical features
                if self.categorical_features is not None:
                    user_categorical_profile = np.zeros(
                        self.categorical_features.shape[1]
                    )
                    for idx, weight in zip(item_indices, item_weights):
                        user_categorical_profile += (
                            self.categorical_features[idx] * weight
                        )
                    user_profile["categorical"] = user_categorical_profile

                # Average numerical features
                if self.numerical_features is not None:
                    user_numerical_profile = np.zeros(self.numerical_features.shape[1])
                    for idx, weight in zip(item_indices, item_weights):
                        user_numerical_profile += self.numerical_features[idx] * weight
                    user_profile["numerical"] = user_numerical_profile

                # Average tag features
                if self.tag_features is not None:
                    user_tag_profile = np.zeros(self.tag_features.shape[1])
                    for idx, weight in zip(item_indices, item_weights):
                        user_tag_profile += self.tag_features[idx] * weight
                    user_profile["tags"] = user_tag_profile

                # Store user profile
                self.user_profiles[user_id] = user_profile

    def recommend_for_user(
        self, user_id: str, excluded_ids: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Generate recommendations for a user based on their profile.

        Args:
            user_id: UnifiedUser ID to recommend for
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of recommendations with scores and confidence values
        """
        if user_id not in self.user_profiles:
            logger.warning("No profile found for user %s", user_id)
            return []

        user_profile = self.user_profiles[user_id]

        # Calculate similarity between user profile and all items
        item_scores = self._calculate_user_item_similarities(user_profile)

        return self._process_scores_to_recommendations(item_scores, excluded_ids)

    def similar_items(
        self, item_id: str, excluded_ids: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Find items similar to a reference item based on content features.

        Args:
            item_id: Reference item ID
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of similar item recommendations
        """
        if item_id not in self.item_index_map:
            logger.warning("Item %s not found in the dataset", item_id)
            return []

        item_idx = self.item_index_map[item_id]

        # Calculate similarity between the reference item and all other items
        item_scores = self._calculate_item_item_similarities(item_idx)

        # Exclude the reference item itself
        excluded_ids = excluded_ids or []
        if item_id not in excluded_ids:
            excluded_ids.append(item_id)

        return self._process_scores_to_recommendations(item_scores, excluded_ids)

    def _calculate_user_item_similarities(
        self, user_profile: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        Calculate similarity scores between a user profile and all items.

        Args:
            user_profile: UnifiedUser profile with feature vectors

        Returns:
            Array of similarity scores for each item
        """
        n_items = len(self.item_index_map)
        total_scores = np.zeros(n_items)
        total_weights = 0.0

        # Calculate text feature similarities
        if "text" in user_profile and self.text_features is not None:
            text_similarities = cosine_similarity(
                user_profile["text"].reshape(1, -1), self.text_features.toarray()
            )[0]
            total_scores += text_similarities * self.config.text_weight
            total_weights += self.config.text_weight

        # Calculate categorical feature similarities
        if "categorical" in user_profile and self.categorical_features is not None:
            cat_similarities = cosine_similarity(
                user_profile["categorical"].reshape(1, -1), self.categorical_features
            )[0]
            total_scores += cat_similarities * self.config.categorical_weight
            total_weights += self.config.categorical_weight

        # Calculate numerical feature similarities
        if "numerical" in user_profile and self.numerical_features is not None:
            num_similarities = cosine_similarity(
                user_profile["numerical"].reshape(1, -1), self.numerical_features
            )[0]
            total_scores += num_similarities * self.config.numerical_weight
            total_weights += self.config.numerical_weight

        # Calculate tag feature similarities
        if "tags" in user_profile and self.tag_features is not None:
            tag_similarities = cosine_similarity(
                user_profile["tags"].reshape(1, -1), self.tag_features
            )[0]
            total_scores += tag_similarities * self.config.tag_weight
            total_weights += self.config.tag_weight

        # Normalize scores
        if total_weights > 0:
            total_scores /= total_weights

        return total_scores

    def _calculate_item_item_similarities(self, item_idx: int) -> np.ndarray:
        """
        Calculate similarity scores between a reference item and all other items.

        Args:
            item_idx: Index of the reference item

        Returns:
            Array of similarity scores for each item
        """
        n_items = len(self.item_index_map)
        total_scores = np.zeros(n_items)
        total_weights = 0.0

        # Calculate text feature similarities
        if self.text_features is not None:
            text_similarities = cosine_similarity(
                self.text_features[item_idx], self.text_features
            )[0]
            total_scores += text_similarities * self.config.text_weight
            total_weights += self.config.text_weight

        # Calculate categorical feature similarities
        if self.categorical_features is not None:
            cat_similarities = cosine_similarity(
                self.categorical_features[item_idx].reshape(1, -1),
                self.categorical_features,
            )[0]
            total_scores += cat_similarities * self.config.categorical_weight
            total_weights += self.config.categorical_weight

        # Calculate numerical feature similarities
        if self.numerical_features is not None:
            num_similarities = cosine_similarity(
                self.numerical_features[item_idx].reshape(1, -1),
                self.numerical_features,
            )[0]
            total_scores += num_similarities * self.config.numerical_weight
            total_weights += self.config.numerical_weight

        # Calculate tag feature similarities
        if self.tag_features is not None:
            tag_similarities = cosine_similarity(
                self.tag_features[item_idx].reshape(1, -1), self.tag_features
            )[0]
            total_scores += tag_similarities * self.config.tag_weight
            total_weights += self.config.tag_weight

        # Normalize scores
        if total_weights > 0:
            total_scores /= total_weights

        return total_scores

    def _process_scores_to_recommendations(
        self, scores: np.ndarray, excluded_ids: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Convert scores to recommendation objects, filtering and sorting as needed.

        Args:
            scores: Array of similarity scores for each item
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of recommendation objects
        """
        # Create set of excluded indices
        excluded_indices = set()
        if excluded_ids:
            excluded_indices = {
                self.item_index_map[item_id]
                for item_id in excluded_ids
                if item_id in self.item_index_map
            }

        # Filter out excluded items and items below threshold
        valid_indices = [
            idx
            for idx in range(len(scores))
            if idx not in excluded_indices and scores[idx] >= self.config.min_similarity
        ]

        # Sort by score
        sorted_indices = sorted(
            valid_indices, key=lambda idx: scores[idx], reverse=True
        )

        # Limit to top N
        top_indices = sorted_indices[: self.config.top_n_recommendations]

        # Create recommendation objects
        recommendations = []
        for idx in top_indices:
            item_id = self.index_item_map[idx]
            score = float(scores[idx])

            # Calculate confidence based on available features
            confidence_factors = []

            # Text confidence: presence of text features
            if self.text_features is not None:
                text_confidence = min(
                    1.0, np.sum(self.text_features[idx].toarray() > 0) / 10
                )
                confidence_factors.append(text_confidence)

            # Categorical confidence: presence of categorical features
            if self.categorical_features is not None:
                cat_confidence = min(
                    1.0, np.sum(self.categorical_features[idx] > 0) / 5
                )
                confidence_factors.append(cat_confidence)

            # Numerical confidence: presence of numerical features
            if self.numerical_features is not None:
                num_confidence = min(1.0, np.sum(self.numerical_features[idx] > 0) / 3)
                confidence_factors.append(num_confidence)

            # Tag confidence: presence of tag features
            if self.tag_features is not None:
                tag_confidence = min(1.0, np.sum(self.tag_features[idx] > 0) / 5)
                confidence_factors.append(tag_confidence)

            # Average confidence
            confidence = 0.5
            if confidence_factors:
                confidence = sum(confidence_factors) / len(confidence_factors)

            # Scale confidence by score to ensure higher scores have higher confidence
            confidence = confidence * (score / max(1.0, scores.max()))

            recommendations.append(
                Recommendation(
                    id=item_id,
                    score=score,
                    confidence=confidence,
                    metadata=self.items.get(item_id),
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
            if user_id not in self.user_profiles or not user_items:
                continue

            # Get items the user has actually interacted with
            actual_items = set(user_items.keys())

            # Generate recommendations for this user
            recommendations = self.recommend_for_user(user_id)
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
