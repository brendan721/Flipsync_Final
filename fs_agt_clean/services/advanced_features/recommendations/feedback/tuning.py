#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Recommendation Algorithm Tuning

This module automatically tunes recommendation algorithms based on feedback data.
It optimizes algorithm parameters and weights to improve recommendation quality
over time.

It includes:
1. Parameter optimization for recommendation algorithms
2. A/B test-based parameter tuning
3. Incremental learning from feedback
4. Multi-objective optimization (relevance, diversity, novelty)
5. Hyperparameter search strategies
"""

import copy
import json
import logging
import math
import random
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.types import JsonDict

logger = logging.getLogger(__name__)


class TuningObjective(str, Enum):
    """Optimization objectives for recommendation tuning."""

    RELEVANCE = "relevance"  # Maximize relevance/accuracy
    DIVERSITY = "diversity"  # Increase diversity of recommendations
    NOVELTY = "novelty"  # Increase novelty/serendipity
    CONVERSION = "conversion"  # Maximize conversion rate
    REVENUE = "revenue"  # Maximize revenue
    CTR = "ctr"  # Maximize click-through rate
    ENGAGEMENT = "engagement"  # Maximize user engagement
    MULTI_OBJECTIVE = "multi"  # Balance multiple objectives


class TuningMethod(str, Enum):
    """Methods for tuning recommendation algorithms."""

    GRID_SEARCH = "grid_search"  # Exhaustive search over parameter space
    RANDOM_SEARCH = "random_search"  # Random sampling of parameter space
    BAYESIAN = "bayesian"  # Bayesian optimization
    GENETIC = "genetic"  # Genetic algorithm optimization
    INCREMENTAL = "incremental"  # Incremental parameter updates
    REINFORCEMENT = "reinforcement"  # Reinforcement learning-based tuning
    MULTI_ARMED_BANDIT = "mab"  # Multi-armed bandit approach
    HYBRID = "hybrid"  # Combination of methods


@dataclass
class AlgorithmParameter:
    """Represents a tunable parameter for a recommendation algorithm."""

    name: str
    current_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    possible_values: Optional[List[Any]] = None
    parameter_type: str = "float"  # float, int, bool, categorical
    description: str = ""

    def is_valid_value(self, value: Any) -> bool:
        """Check if a value is valid for this parameter."""
        if self.possible_values is not None:
            return bool(value in self.possible_values)

        if self.parameter_type == "float":
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
            return True

        if self.parameter_type == "int":
            if not isinstance(value, int):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
            return True

        if self.parameter_type == "bool":
            return isinstance(value, bool)

        return True  # For other types

    def sample_value(self) -> Any:
        """Sample a random valid value for this parameter."""
        if self.possible_values is not None:
            return random.choice(self.possible_values)

        if self.parameter_type == "bool":
            return random.choice([True, False])

        if self.parameter_type == "int":
            min_val = int(self.min_value) if self.min_value is not None else 0
            max_val = int(self.max_value) if self.max_value is not None else 100
            return random.randint(min_val, max_val)

        if self.parameter_type == "float":
            min_val = self.min_value if self.min_value is not None else 0.0
            max_val = self.max_value if self.max_value is not None else 1.0
            return min_val + random.random() * (max_val - min_val)

        return self.current_value  # Fallback to current value


@dataclass
class AlgorithmConfig:
    """Configuration for a recommendation algorithm."""

    algorithm_id: str
    algorithm_type: str
    parameters: Dict[str, AlgorithmParameter] = field(default_factory=dict)
    objective_weights: Dict[TuningObjective, float] = field(default_factory=dict)
    enabled: bool = True
    last_updated: datetime = field(default_factory=datetime.now)
    version: int = 1
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "algorithm_id": self.algorithm_id,
            "algorithm_type": self.algorithm_type,
            "parameters": {
                name: {
                    "current_value": param.current_value,
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "step": param.step,
                    "possible_values": param.possible_values,
                    "parameter_type": param.parameter_type,
                    "description": param.description,
                }
                for name, param in self.parameters.items()
            },
            "objective_weights": {
                obj.value: weight for obj, weight in self.objective_weights.items()
            },
            "enabled": self.enabled,
            "last_updated": self.last_updated.isoformat(),
            "version": self.version,
            "description": self.description,
        }

    def get_param_dict(self) -> Dict[str, Any]:
        """Get current parameter values as a dictionary."""
        return {name: param.current_value for name, param in self.parameters.items()}

    def update_param(self, name: str, value: Any) -> bool:
        """Update a parameter value if valid."""
        if name not in self.parameters:
            return bool(False)

        param = self.parameters[name]
        if not param.is_valid_value(value):
            return False

        param.current_value = value
        self.last_updated = datetime.now()
        self.version += 1
        return True

    def update_params(self, param_dict: Dict[str, Any]) -> Dict[str, bool]:
        """Update multiple parameters, returning success status for each."""
        results = {}
        for name, value in param_dict.items():
            results[name] = self.update_param(name, value)
        return results

    def clone(self) -> "AlgorithmConfig":
        """Create a copy of this configuration."""
        return copy.deepcopy(self)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a recommendation algorithm configuration."""

    algorithm_id: str
    config_version: int
    timestamp: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.0
    diversity_score: float = 0.0
    novelty_score: float = 0.0
    ctr: float = 0.0
    conversion_rate: float = 0.0
    revenue_per_recommendation: float = 0.0
    engagement_score: float = 0.0
    feedback_count: int = 0
    positive_feedback_ratio: float = 0.0
    average_rating: float = 0.0
    sample_size: int = 0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "algorithm_id": self.algorithm_id,
            "config_version": self.config_version,
            "timestamp": self.timestamp.isoformat(),
            "relevance_score": self.relevance_score,
            "diversity_score": self.diversity_score,
            "novelty_score": self.novelty_score,
            "ctr": self.ctr,
            "conversion_rate": self.conversion_rate,
            "revenue_per_recommendation": self.revenue_per_recommendation,
            "engagement_score": self.engagement_score,
            "feedback_count": self.feedback_count,
            "positive_feedback_ratio": self.positive_feedback_ratio,
            "average_rating": self.average_rating,
            "sample_size": self.sample_size,
            "confidence": self.confidence,
        }

    def get_objective_score(self, objective: TuningObjective) -> float:
        """Get score for a specific objective."""
        scores = {
            TuningObjective.RELEVANCE: self.relevance_score,
            TuningObjective.DIVERSITY: self.diversity_score,
            TuningObjective.NOVELTY: self.novelty_score,
            TuningObjective.CONVERSION: self.conversion_rate,
            TuningObjective.REVENUE: self.revenue_per_recommendation,
            TuningObjective.CTR: self.ctr,
            TuningObjective.ENGAGEMENT: self.engagement_score,
        }
        return scores.get(objective, 0.0)

    def get_weighted_score(
        self, objective_weights: Dict[TuningObjective, float]
    ) -> float:
        """Calculate weighted score across multiple objectives."""
        if not objective_weights:
            return (
                self.relevance_score + self.diversity_score + self.novelty_score
            ) / 3

        total_weight = sum(objective_weights.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            weight * self.get_objective_score(obj)
            for obj, weight in objective_weights.items()
        )
        return weighted_sum / total_weight


@dataclass
class TuningExperiment:
    """An experiment for tuning algorithm parameters."""

    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    algorithm_id: str = ""
    base_config: Optional[AlgorithmConfig] = None
    objective: TuningObjective = TuningObjective.MULTI_OBJECTIVE
    objective_weights: Dict[TuningObjective, float] = field(default_factory=dict)
    method: TuningMethod = TuningMethod.INCREMENTAL
    candidate_configs: List[AlgorithmConfig] = field(default_factory=list)
    performance_history: List[PerformanceMetrics] = field(default_factory=list)
    best_config: Optional[AlgorithmConfig] = None
    best_score: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    max_iterations: int = 10
    current_iteration: int = 0
    status: str = "created"  # created, running, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "experiment_id": self.experiment_id,
            "algorithm_id": self.algorithm_id,
            "base_config": self.base_config.to_dict() if self.base_config else None,
            "objective": self.objective.value,
            "objective_weights": {
                obj.value: weight for obj, weight in self.objective_weights.items()
            },
            "method": self.method.value,
            "candidate_configs_count": len(self.candidate_configs),
            "performance_history_count": len(self.performance_history),
            "best_config": self.best_config.to_dict() if self.best_config else None,
            "best_score": self.best_score,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "status": self.status,
        }


class FeedbackBasedTuner:
    """Tunes recommendation algorithms based on feedback data."""

    def __init__(self, storage_service=None, analytics_service=None):
        self.storage_service = storage_service
        self.analytics_service = analytics_service

        # In-memory caches
        self._algorithm_configs = {}  # algorithm_id -> AlgorithmConfig
        self._performance_history = defaultdict(
            list
        )  # algorithm_id -> List[PerformanceMetrics]
        self._active_experiments = {}  # experiment_id -> TuningExperiment
        self._parameter_importance = defaultdict(
            dict
        )  # algorithm_id -> {param_name -> importance}

    def register_algorithm(
        self,
        algorithm_id: str,
        algorithm_type: str,
        parameters: Dict[str, Dict[str, Any]],
        objective_weights: Optional[Dict[str, float]] = None,
        description: str = "",
    ) -> AlgorithmConfig:
        """Register a recommendation algorithm for tuning."""
        # Convert parameter dictionaries to AlgorithmParameter objects
        param_objects = {}
        for name, param_dict in parameters.items():
            param_objects[name] = AlgorithmParameter(
                name=name,
                current_value=param_dict.get("current_value"),
                min_value=param_dict.get("min_value"),
                max_value=param_dict.get("max_value"),
                step=param_dict.get("step"),
                possible_values=param_dict.get("possible_values"),
                parameter_type=param_dict.get("parameter_type", "float"),
                description=param_dict.get("description", ""),
            )

        # Convert objective weights
        obj_weights = {}
        if objective_weights:
            for obj_str, weight in objective_weights.items():
                try:
                    obj = TuningObjective(obj_str)
                    obj_weights[obj] = weight
                except ValueError:
                    logger.warning("Unknown tuning objective: %s", obj_str)

        # Create algorithm configuration
        config = AlgorithmConfig(
            algorithm_id=algorithm_id,
            algorithm_type=algorithm_type,
            parameters=param_objects,
            objective_weights=obj_weights,
            description=description,
        )

        # Store configuration
        self._algorithm_configs[algorithm_id] = config

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_algorithm_config(config)

        return config

    def update_metrics(self, metrics: PerformanceMetrics) -> bool:
        """Update performance metrics for an algorithm configuration."""
        # Validate algorithm exists
        if metrics.algorithm_id not in self._algorithm_configs:
            logger.warning(
                "Cannot update metrics for unknown algorithm: %s", metrics.algorithm_id
            )
            return bool(False)

        # Add to performance history
        self._performance_history[metrics.algorithm_id].append(metrics)

        # Keep history sorted by timestamp
        self._performance_history[metrics.algorithm_id].sort(key=lambda x: x.timestamp)

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_performance_metrics(metrics)

        # Update active experiments that use this algorithm
        for exp in self._active_experiments.values():
            if exp.algorithm_id == metrics.algorithm_id and exp.status == "running":
                exp.performance_history.append(metrics)

                # Check if this is a better configuration
                score = metrics.get_weighted_score(exp.objective_weights)
                if score > exp.best_score:
                    exp.best_score = score
                    # Find matching config in candidates
                    for candidate in exp.candidate_configs:
                        if candidate.version == metrics.config_version:
                            exp.best_config = candidate.clone()
                            break

        return True

    def get_algorithm_config(self, algorithm_id: str) -> Optional[AlgorithmConfig]:
        """Get the current configuration for an algorithm."""
        return self._algorithm_configs.get(algorithm_id)

    def get_metrics(
        self,
        algorithm_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[PerformanceMetrics]:
        """Get performance metrics for an algorithm."""
        if algorithm_id not in self._performance_history:
            return []

        metrics = self._performance_history[algorithm_id]

        # Apply time filters
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]

        # Apply limit and sort by recency
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        return metrics[:limit]

    def create_experiment(
        self,
        algorithm_id: str,
        method: Union[TuningMethod, str] = TuningMethod.INCREMENTAL,
        objective: Union[TuningObjective, str] = TuningObjective.MULTI_OBJECTIVE,
        objective_weights: Optional[Dict[Union[TuningObjective, str], float]] = None,
        max_iterations: int = 10,
    ) -> Optional[TuningExperiment]:
        """Create a new tuning experiment."""
        # Validate algorithm exists
        if algorithm_id not in self._algorithm_configs:
            logger.warning(
                "Cannot create experiment for unknown algorithm: %s", algorithm_id
            )
            return None

        # Get base configuration
        base_config = self._algorithm_configs[algorithm_id]

        # Convert method string to enum if needed
        if isinstance(method, str):
            try:
                method = TuningMethod(method)
            except ValueError:
                logger.warning("Unknown tuning method: %s, using default", method)
                method = TuningMethod.INCREMENTAL

        # Convert objective string to enum if needed
        if isinstance(objective, str):
            try:
                objective = TuningObjective(objective)
            except ValueError:
                logger.warning("Unknown tuning objective: %s, using default", objective)
                objective = TuningObjective.MULTI_OBJECTIVE

        # Convert objective weights
        obj_weights = {}
        if objective_weights:
            for obj_key, weight in objective_weights.items():
                if isinstance(obj_key, str):
                    try:
                        obj = TuningObjective(obj_key)
                        obj_weights[obj] = weight
                    except ValueError:
                        logger.warning("Unknown tuning objective: %s", obj_key)
                else:
                    obj_weights[obj_key] = weight

        # Create initial experiment
        experiment = TuningExperiment(
            algorithm_id=algorithm_id,
            base_config=base_config.clone(),
            method=method,
            objective=objective,
            objective_weights=obj_weights,
            max_iterations=max_iterations,
        )

        # Store experiment
        self._active_experiments[experiment.experiment_id] = experiment

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_experiment(experiment)

        return experiment

    def start_experiment(self, experiment_id: str) -> bool:
        """Start running a tuning experiment."""
        if experiment_id not in self._active_experiments:
            logger.warning("Cannot start unknown experiment: %s", experiment_id)
            return bool(False)

        experiment = self._active_experiments[experiment_id]
        if experiment.status != "created":
            logger.warning("Experiment is already in status: %s", experiment.status)
            return False

        # Update status
        experiment.status = "running"

        # Generate initial configurations based on method
        self._generate_candidate_configs(experiment)

        # Initialize with any existing performance metrics
        if experiment.algorithm_id in self._performance_history:
            recent_metrics = self._performance_history[experiment.algorithm_id]
            # Add relevant metrics to experiment history
            for metric in recent_metrics:
                # Only include metrics for configurations in our candidates
                for candidate in experiment.candidate_configs:
                    if candidate.version == metric.config_version:
                        experiment.performance_history.append(metric)

                        # Check if this is better than current best
                        score = metric.get_weighted_score(experiment.objective_weights)
                        if score > experiment.best_score:
                            experiment.best_score = score
                            experiment.best_config = candidate.clone()

        # Update storage
        if self.storage_service:
            self.storage_service.update_experiment(experiment)

        return True

    def _generate_candidate_configs(self, experiment: TuningExperiment) -> None:
        """Generate candidate configurations for an experiment."""
        base_config = experiment.base_config

        if experiment.method == TuningMethod.GRID_SEARCH:
            candidates = self._generate_grid_search_candidates(base_config)
        elif experiment.method == TuningMethod.RANDOM_SEARCH:
            candidates = self._generate_random_search_candidates(
                base_config, experiment.max_iterations * 2
            )
        elif experiment.method == TuningMethod.BAYESIAN:
            candidates = self._generate_bayesian_candidates(base_config, experiment)
        elif experiment.method == TuningMethod.GENETIC:
            candidates = self._generate_genetic_candidates(base_config, experiment)
        else:  # Default to incremental
            candidates = self._generate_incremental_candidates(base_config)

        experiment.candidate_configs = candidates

    def _generate_grid_search_candidates(
        self, base_config: AlgorithmConfig
    ) -> List[AlgorithmConfig]:
        """Generate candidate configurations using grid search."""
        # Identify parameters suitable for grid search
        grid_params = {}
        for name, param in base_config.parameters.items():
            values = []

            # Skip parameters without defined ranges
            if param.parameter_type == "bool":
                values = [True, False]
            elif param.possible_values is not None:
                values = param.possible_values
            elif (
                param.min_value is not None
                and param.max_value is not None
                and param.step is not None
            ):
                if param.parameter_type == "int":
                    values = list(
                        range(
                            int(param.min_value),
                            int(param.max_value) + 1,
                            int(param.step),
                        )
                    )
                else:  # float
                    values = [
                        param.min_value + i * param.step
                        for i in range(
                            int((param.max_value - param.min_value) / param.step) + 1
                        )
                    ]

            if values:
                grid_params[name] = values

        # If no suitable parameters, return base config
        if not grid_params:
            return [base_config.clone()]

        # Generate all combinations
        candidates = []

        # Helper function for recursive generation
        def generate_combinations(config, param_names, current_idx=0):
            if current_idx >= len(param_names):
                candidates.append(config.clone())
                return

            param_name = param_names[current_idx]
            for value in grid_params[param_name]:
                new_config = config.clone()
                new_config.update_param(param_name, value)
                generate_combinations(new_config, param_names, current_idx + 1)

        generate_combinations(base_config, list(grid_params.keys()))

        return candidates

    def _generate_random_search_candidates(
        self, base_config: AlgorithmConfig, count: int
    ) -> List[AlgorithmConfig]:
        """Generate candidate configurations using random search."""
        candidates = [base_config.clone()]  # Always include base config

        # Generate random variations
        for _ in range(count - 1):
            config = base_config.clone()

            # Randomly modify parameters
            for name, param in config.parameters.items():
                # 50% chance to modify each parameter
                if random.random() < 0.5:
                    new_value = param.sample_value()
                    config.update_param(name, new_value)

            candidates.append(config)

        return candidates

    def _generate_bayesian_candidates(
        self, base_config: AlgorithmConfig, experiment: TuningExperiment
    ) -> List[AlgorithmConfig]:
        """Generate candidate configurations using Bayesian optimization."""
        # This is a simplified placeholder for Bayesian optimization
        # In practice, you'd use a library like scikit-optimize or GPyOpt

        # Start with base config and some random variations
        candidates = [base_config.clone()]
        candidates.extend(self._generate_random_search_candidates(base_config, 5))

        # TODO: Implement proper Bayesian optimization

        return candidates

    def _generate_genetic_candidates(
        self, base_config: AlgorithmConfig, experiment: TuningExperiment
    ) -> List[AlgorithmConfig]:
        """Generate candidate configurations using genetic algorithms."""
        # This is a simplified placeholder for genetic algorithms

        # Start with base config and some random variations
        candidates = [base_config.clone()]
        candidates.extend(self._generate_random_search_candidates(base_config, 9))

        # TODO: Implement proper genetic algorithm optimization

        return candidates

    def _generate_incremental_candidates(
        self, base_config: AlgorithmConfig
    ) -> List[AlgorithmConfig]:
        """Generate candidate configurations using incremental parameter changes."""
        candidates = [base_config.clone()]  # Always include base config

        # Generate variations by changing one parameter at a time
        for name, param in base_config.parameters.items():
            if param.parameter_type == "bool":
                # Create a config with the opposite boolean value
                config = base_config.clone()
                config.update_param(name, not param.current_value)
                candidates.append(config)

            elif param.parameter_type == "int" or param.parameter_type == "float":
                if param.min_value is not None and param.max_value is not None:
                    # Create configs with incremented and decremented values
                    step = (
                        param.step
                        if param.step is not None
                        else (1 if param.parameter_type == "int" else 0.1)
                    )

                    # Increment
                    if param.current_value + step <= param.max_value:
                        config = base_config.clone()
                        config.update_param(name, param.current_value + step)
                        candidates.append(config)

                    # Decrement
                    if param.current_value - step >= param.min_value:
                        config = base_config.clone()
                        config.update_param(name, param.current_value - step)
                        candidates.append(config)

            elif param.possible_values is not None:
                # Create configs with each possible value except current
                for value in param.possible_values:
                    if value != param.current_value:
                        config = base_config.clone()
                        config.update_param(name, value)
                        candidates.append(config)

        return candidates

    def get_experiment(self, experiment_id: str) -> Optional[TuningExperiment]:
        """Get an experiment by ID."""
        return self._active_experiments.get(experiment_id)

    def get_best_config(self, algorithm_id: str) -> Optional[AlgorithmConfig]:
        """Get the best configuration for an algorithm based on historical performance."""
        if algorithm_id not in self._algorithm_configs:
            return None

        # Check for active experiments with this algorithm
        best_experiment = None
        best_score = -float("inf")

        for exp in self._active_experiments.values():
            if (
                exp.algorithm_id == algorithm_id
                and exp.best_config
                and exp.best_score > best_score
            ):
                best_experiment = exp
                best_score = exp.best_score

        if best_experiment and best_experiment.best_config:
            return best_experiment.best_config

        # If no experiment data, return current config
        return self._algorithm_configs.get(algorithm_id)

    def apply_tuning_results(self, experiment_id: str) -> bool:
        """Apply the results of a tuning experiment to the algorithm configuration."""
        if experiment_id not in self._active_experiments:
            return bool(False)

        experiment = self._active_experiments[experiment_id]
        if not experiment.best_config:
            return False

        # Update main algorithm configuration
        self._algorithm_configs[experiment.algorithm_id] = (
            experiment.best_config.clone()
        )

        # Mark experiment as completed
        experiment.status = "completed"
        experiment.end_time = datetime.now()

        # Update storage
        if self.storage_service:
            self.storage_service.update_algorithm_config(
                self._algorithm_configs[experiment.algorithm_id]
            )
            self.storage_service.update_experiment(experiment)

        return True

    def cancel_experiment(self, experiment_id: str) -> bool:
        """Cancel a running experiment."""
        if experiment_id not in self._active_experiments:
            return False

        experiment = self._active_experiments[experiment_id]
        if experiment.status not in ["created", "running"]:
            return False

        experiment.status = "cancelled"
        experiment.end_time = datetime.now()

        # Update storage
        if self.storage_service:
            self.storage_service.update_experiment(experiment)

        return True


# Helper functions


def calculate_performance_metrics(
    algorithm_id: str,
    config_version: int,
    feedback_events: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
) -> PerformanceMetrics:
    """Calculate performance metrics based on feedback and recommendation data."""
    metrics = PerformanceMetrics(
        algorithm_id=algorithm_id,
        config_version=config_version,
        sample_size=len(recommendations),
    )

    if not feedback_events or not recommendations:
        return metrics

    # Count feedback events by type
    feedback_count = len(feedback_events)
    metrics.feedback_count = feedback_count

    # Calculate positive feedback ratio
    positive_count = sum(
        1
        for event in feedback_events
        if event.get("type") in ["like", "helpful", "rating"]
        and event.get("value", 0) > 0
    )
    if feedback_count > 0:
        metrics.positive_feedback_ratio = positive_count / feedback_count

    # Calculate average rating
    ratings = [
        event.get("value", 0)
        for event in feedback_events
        if event.get("type") == "rating" and event.get("value") is not None
    ]
    if ratings:
        metrics.average_rating = sum(ratings) / len(ratings)

    # Calculate CTR
    clicks = sum(1 for event in feedback_events if event.get("type") == "click")
    if len(recommendations) > 0:
        metrics.ctr = clicks / len(recommendations)

    # Calculate conversion rate
    conversions = sum(1 for event in feedback_events if event.get("type") == "purchase")
    if len(recommendations) > 0:
        metrics.conversion_rate = conversions / len(recommendations)

    # Calculate revenue per recommendation
    total_revenue = sum(
        event.get("metadata", {}).get("revenue", 0)
        for event in feedback_events
        if event.get("type") == "purchase"
    )
    if len(recommendations) > 0:
        metrics.revenue_per_recommendation = total_revenue / len(recommendations)

    # Calculate engagement score (simplified)
    engagement_events = sum(
        1
        for event in feedback_events
        if event.get("type") in ["click", "view", "save", "share"]
    )
    if len(recommendations) > 0:
        metrics.engagement_score = engagement_events / len(recommendations)

    # Calculate relevance score (simplified)
    if metrics.positive_feedback_ratio > 0:
        metrics.relevance_score = (
            metrics.positive_feedback_ratio + metrics.average_rating / 5
        ) / 2

    # Calculate confidence based on sample size
    # Using a simplified approach that increases with more samples
    metrics.confidence = min(1.0, metrics.sample_size / 1000)

    return metrics


def create_grid_search_experiment(
    tuner: FeedbackBasedTuner,
    algorithm_id: str,
    objective: TuningObjective = TuningObjective.RELEVANCE,
) -> Optional[TuningExperiment]:
    """Create and start a grid search tuning experiment."""
    experiment = tuner.create_experiment(
        algorithm_id=algorithm_id, method=TuningMethod.GRID_SEARCH, objective=objective
    )

    if experiment and tuner.start_experiment(experiment.experiment_id):
        return experiment

    return None


def create_incremental_tuning_experiment(
    tuner: FeedbackBasedTuner,
    algorithm_id: str,
    objective_weights: Dict[TuningObjective, float] = None,
) -> Optional[TuningExperiment]:
    """Create and start an incremental tuning experiment."""
    if objective_weights is None:
        objective_weights = {
            TuningObjective.RELEVANCE: 0.6,
            TuningObjective.DIVERSITY: 0.2,
            TuningObjective.NOVELTY: 0.2,
        }

    experiment = tuner.create_experiment(
        algorithm_id=algorithm_id,
        method=TuningMethod.INCREMENTAL,
        objective=TuningObjective.MULTI_OBJECTIVE,
        objective_weights=objective_weights,
    )

    if experiment and tuner.start_experiment(experiment.experiment_id):
        return experiment

    return None
