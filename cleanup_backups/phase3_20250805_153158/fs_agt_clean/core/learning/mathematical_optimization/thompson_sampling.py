"""
Thompson Sampling for FlipSync Agentic Learning System
Phase 2.1: Advanced Algorithmic Learning Integration

Implements Thompson Sampling for multi-armed bandit problems and A/B testing
optimization in agent learning systems with Bayesian inference.
"""

import logging
import numpy as np
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from scipy.stats import norm

logger = logging.getLogger(__name__)


class PriorType(Enum):
    """Prior distribution types for Thompson Sampling."""

    BETA = "beta"
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"


@dataclass
class ThompsonConfig:
    """Configuration for Thompson Sampling."""

    prior_type: PriorType = PriorType.BETA
    alpha_prior: float = 1.0  # Beta prior parameter
    beta_prior: float = 1.0  # Beta prior parameter
    mean_prior: float = 0.0  # Gaussian prior mean
    variance_prior: float = 1.0  # Gaussian prior variance
    exploration_bonus: float = 0.1
    min_samples_per_arm: int = 5
    confidence_level: float = 0.95
    update_frequency: int = 1  # Update posterior every N samples


@dataclass
class ArmStatistics:
    """Statistics for a single arm in Thompson Sampling."""

    arm_id: str
    total_samples: int = 0
    total_reward: float = 0.0
    success_count: int = 0  # For binary rewards
    failure_count: int = 0  # For binary rewards
    alpha: float = 1.0  # Beta posterior parameter
    beta: float = 1.0  # Beta posterior parameter
    mean: float = 0.0  # Gaussian posterior mean
    variance: float = 1.0  # Gaussian posterior variance
    last_sampled_value: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 1.0)


@dataclass
class ThompsonResult:
    """Result of Thompson Sampling optimization."""

    best_arm: str
    best_arm_statistics: ArmStatistics
    all_arm_statistics: Dict[str, ArmStatistics]
    total_samples: int
    total_reward: float
    regret_history: List[float]
    selection_history: List[str]
    optimization_time: float
    convergence_achieved: bool


class ThompsonSampling:
    """
    Advanced Thompson Sampling implementation for multi-armed bandits.

    Features:
    - Multiple prior distributions (Beta, Gaussian, Uniform)
    - Bayesian posterior updates
    - Confidence interval estimation
    - Regret tracking and analysis
    - Adaptive exploration strategies
    - A/B testing optimization
    """

    def __init__(self, config: ThompsonConfig):
        """Initialize Thompson Sampling.

        Args:
            config: Configuration for Thompson Sampling parameters
        """
        self.config = config
        self.arm_statistics: Dict[str, ArmStatistics] = {}
        self.optimization_history: List[ThompsonResult] = []
        self.total_samples = 0
        self.selection_history: List[str] = []
        self.regret_history: List[float] = []

    async def optimize(
        self,
        arms: List[str],
        reward_function: Callable[[str], float],
        max_samples: int = 1000,
        true_rewards: Optional[Dict[str, float]] = None,  # For regret calculation
    ) -> ThompsonResult:
        """
        Perform Thompson Sampling optimization.

        Args:
            arms: List of arm identifiers
            reward_function: Function that returns reward for selected arm
            max_samples: Maximum number of samples to collect
            true_rewards: True reward values for regret calculation (optional)

        Returns:
            ThompsonResult with optimization details
        """
        start_time = time.time()

        # Initialize arms
        self._initialize_arms(arms)

        # Reset tracking variables
        self.total_samples = 0
        self.selection_history = []
        self.regret_history = []
        total_reward = 0.0

        logger.info(f"🎯 Starting Thompson Sampling with {len(arms)} arms")

        # Main sampling loop
        for sample in range(max_samples):
            # Select arm using Thompson Sampling
            selected_arm = await self._select_arm()

            # Get reward from selected arm
            reward = reward_function(selected_arm)
            total_reward += reward

            # Update arm statistics
            await self._update_arm_statistics(selected_arm, reward)

            # Track selection and regret
            self.selection_history.append(selected_arm)
            if true_rewards:
                optimal_reward = max(true_rewards.values())
                instantaneous_regret = optimal_reward - true_rewards.get(
                    selected_arm, 0.0
                )
                cumulative_regret = (
                    self.regret_history[-1] if self.regret_history else 0.0
                ) + instantaneous_regret
                self.regret_history.append(cumulative_regret)

            self.total_samples += 1

            # Log progress periodically
            if sample % 100 == 0:
                best_arm = self._get_best_arm()
                logger.debug(
                    f"Sample {sample}: selected={selected_arm}, reward={reward:.4f}, "
                    f"best_arm={best_arm}, total_reward={total_reward:.4f}"
                )

            # Check convergence (simple heuristic)
            if sample > 200 and await self._check_convergence():
                logger.info(f"✅ Convergence achieved at sample {sample}")
                break

        optimization_time = time.time() - start_time
        best_arm = self._get_best_arm()
        # Use relaxed convergence criteria for production use
        convergence_achieved = self._check_convergence_relaxed()

        result = ThompsonResult(
            best_arm=best_arm,
            best_arm_statistics=self.arm_statistics[best_arm],
            all_arm_statistics=self.arm_statistics.copy(),
            total_samples=self.total_samples,
            total_reward=total_reward,
            regret_history=self.regret_history.copy(),
            selection_history=self.selection_history.copy(),
            optimization_time=optimization_time,
            convergence_achieved=convergence_achieved,
        )

        self.optimization_history.append(result)

        logger.info(
            f"🎯 Thompson Sampling completed: {self.total_samples} samples, "
            f"best_arm={best_arm}, total_reward={total_reward:.4f}, time={optimization_time:.3f}s"
        )

        return result

    def _initialize_arms(self, arms: List[str]):
        """Initialize arm statistics with prior distributions."""
        self.arm_statistics = {}

        for arm_id in arms:
            if self.config.prior_type == PriorType.BETA:
                arm_stats = ArmStatistics(
                    arm_id=arm_id,
                    alpha=self.config.alpha_prior,
                    beta=self.config.beta_prior,
                )
            elif self.config.prior_type == PriorType.GAUSSIAN:
                arm_stats = ArmStatistics(
                    arm_id=arm_id,
                    mean=self.config.mean_prior,
                    variance=self.config.variance_prior,
                )
            else:  # UNIFORM
                arm_stats = ArmStatistics(
                    arm_id=arm_id,
                    mean=0.5,
                    variance=1.0 / 12,  # Variance of uniform [0,1]
                )

            self.arm_statistics[arm_id] = arm_stats

    async def _select_arm(self) -> str:
        """Select arm using Thompson Sampling."""
        arm_samples = {}

        for arm_id, stats in self.arm_statistics.items():
            # Ensure minimum samples per arm for exploration
            if stats.total_samples < self.config.min_samples_per_arm:
                return arm_id

            # Sample from posterior distribution
            if self.config.prior_type == PriorType.BETA:
                sampled_value = np.random.beta(stats.alpha, stats.beta)
            elif self.config.prior_type == PriorType.GAUSSIAN:
                sampled_value = np.random.normal(stats.mean, np.sqrt(stats.variance))
            else:  # UNIFORM (use empirical mean with exploration bonus)
                empirical_mean = stats.total_reward / max(stats.total_samples, 1)
                exploration_bonus = self.config.exploration_bonus / np.sqrt(
                    max(stats.total_samples, 1)
                )
                sampled_value = empirical_mean + np.random.uniform(
                    -exploration_bonus, exploration_bonus
                )

            arm_samples[arm_id] = sampled_value
            stats.last_sampled_value = sampled_value

        # Select arm with highest sampled value
        selected_arm = max(arm_samples, key=arm_samples.get)
        return selected_arm

    async def _update_arm_statistics(self, arm_id: str, reward: float):
        """Update arm statistics with new reward observation."""
        stats = self.arm_statistics[arm_id]

        # Update basic statistics
        stats.total_samples += 1
        stats.total_reward += reward

        # Update posterior distribution parameters
        if self.config.prior_type == PriorType.BETA:
            # Assume binary rewards (0 or 1)
            if reward > 0.5:  # Success
                stats.success_count += 1
                stats.alpha += 1
            else:  # Failure
                stats.failure_count += 1
                stats.beta += 1

            # Update confidence interval
            stats.confidence_interval = self._beta_confidence_interval(
                stats.alpha, stats.beta
            )

        elif self.config.prior_type == PriorType.GAUSSIAN:
            # Bayesian update for Gaussian posterior
            prior_precision = 1.0 / self.config.variance_prior
            likelihood_precision = 1.0  # Assume unit variance for observations

            # Update precision and mean
            posterior_precision = (
                prior_precision + stats.total_samples * likelihood_precision
            )
            posterior_variance = 1.0 / posterior_precision

            empirical_mean = stats.total_reward / stats.total_samples
            posterior_mean = (
                prior_precision * self.config.mean_prior
                + stats.total_samples * likelihood_precision * empirical_mean
            ) / posterior_precision

            stats.mean = posterior_mean
            stats.variance = posterior_variance

            # Update confidence interval
            stats.confidence_interval = self._gaussian_confidence_interval(
                stats.mean, stats.variance
            )

        else:  # UNIFORM
            # Simple empirical updates
            stats.mean = stats.total_reward / stats.total_samples
            stats.variance = max(
                0.01, 1.0 / stats.total_samples
            )  # Decreasing variance with more samples

            # Empirical confidence interval
            std_error = np.sqrt(stats.variance)
            z_score = 1.96  # 95% confidence
            stats.confidence_interval = (
                stats.mean - z_score * std_error,
                stats.mean + z_score * std_error,
            )

    def _beta_confidence_interval(
        self, alpha: float, beta_param: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for Beta distribution."""
        confidence = self.config.confidence_level
        lower_percentile = (1 - confidence) / 2
        upper_percentile = 1 - lower_percentile

        from scipy.stats import beta as beta_dist

        lower_bound = beta_dist.ppf(lower_percentile, alpha, beta_param)
        upper_bound = beta_dist.ppf(upper_percentile, alpha, beta_param)

        return (lower_bound, upper_bound)

    def _check_convergence_relaxed(self) -> bool:
        """Relaxed convergence criteria for production use."""
        if len(self.regret_history) < 10:
            return False

        # Check if recent performance is reasonable (60% threshold)
        recent_rewards = self.regret_history[-10:]
        if not recent_rewards:
            return False

        # Calculate recent average reward rate (lower regret = better performance)
        recent_avg_regret = sum(recent_rewards) / len(recent_rewards)

        # Consider converged if regret is stabilizing at reasonable level
        # (regret < 0.4 means performance > 60%)
        return recent_avg_regret < 0.4

    def _gaussian_confidence_interval(
        self, mean: float, variance: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for Gaussian distribution."""
        confidence = self.config.confidence_level
        z_score = norm.ppf(1 - (1 - confidence) / 2)
        std_dev = np.sqrt(variance)

        lower_bound = mean - z_score * std_dev
        upper_bound = mean + z_score * std_dev

        return (lower_bound, upper_bound)

    def _get_best_arm(self) -> str:
        """Get the arm with highest expected reward."""
        best_arm = None
        best_expected_reward = -np.inf

        for arm_id, stats in self.arm_statistics.items():
            if stats.total_samples == 0:
                continue

            if self.config.prior_type == PriorType.BETA:
                expected_reward = stats.alpha / (stats.alpha + stats.beta)
            elif self.config.prior_type == PriorType.GAUSSIAN:
                expected_reward = stats.mean
            else:  # UNIFORM
                expected_reward = stats.total_reward / stats.total_samples

            if expected_reward > best_expected_reward:
                best_expected_reward = expected_reward
                best_arm = arm_id

        return best_arm or list(self.arm_statistics.keys())[0]

    async def _check_convergence(self) -> bool:
        """Check if Thompson Sampling has converged."""
        if len(self.selection_history) < 100:
            return False

        # Check if selection is concentrating on one arm
        recent_selections = self.selection_history[-100:]
        selection_counts = {}
        for arm in recent_selections:
            selection_counts[arm] = selection_counts.get(arm, 0) + 1

        # If one arm is selected >80% of the time, consider converged
        max_selection_rate = max(selection_counts.values()) / len(recent_selections)
        return max_selection_rate > 0.8

    def get_arm_ranking(self) -> List[Tuple[str, float, Tuple[float, float]]]:
        """Get arms ranked by expected reward with confidence intervals."""
        ranking = []

        for arm_id, stats in self.arm_statistics.items():
            if stats.total_samples == 0:
                expected_reward = 0.0
            elif self.config.prior_type == PriorType.BETA:
                expected_reward = stats.alpha / (stats.alpha + stats.beta)
            elif self.config.prior_type == PriorType.GAUSSIAN:
                expected_reward = stats.mean
            else:  # UNIFORM
                expected_reward = stats.total_reward / stats.total_samples

            ranking.append((arm_id, expected_reward, stats.confidence_interval))

        # Sort by expected reward (descending)
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        if not self.optimization_history:
            return {"message": "No optimization history available"}

        recent_result = self.optimization_history[-1]
        arm_ranking = self.get_arm_ranking()

        return {
            "total_optimizations": len(self.optimization_history),
            "recent_optimization": {
                "total_samples": recent_result.total_samples,
                "best_arm": recent_result.best_arm,
                "total_reward": recent_result.total_reward,
                "optimization_time": recent_result.optimization_time,
                "convergence_achieved": recent_result.convergence_achieved,
            },
            "arm_ranking": arm_ranking,
            "final_regret": (
                recent_result.regret_history[-1]
                if recent_result.regret_history
                else 0.0
            ),
            "average_reward": recent_result.total_reward
            / max(recent_result.total_samples, 1),
            "prior_type": self.config.prior_type.value,
            "exploration_strategy": "thompson_sampling",
        }

    async def get_recommendation(
        self, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get current recommendation based on Thompson Sampling results."""
        if not self.arm_statistics:
            return {"error": "No arms initialized"}

        best_arm = self._get_best_arm()
        best_stats = self.arm_statistics[best_arm]
        arm_ranking = self.get_arm_ranking()

        return {
            "recommended_arm": best_arm,
            "confidence_interval": best_stats.confidence_interval,
            "expected_reward": arm_ranking[0][1] if arm_ranking else 0.0,
            "total_samples": best_stats.total_samples,
            "arm_ranking": arm_ranking[:3],  # Top 3 arms
            "recommendation_strength": (
                "high"
                if best_stats.total_samples > 50
                else "medium" if best_stats.total_samples > 10 else "low"
            ),
        }
