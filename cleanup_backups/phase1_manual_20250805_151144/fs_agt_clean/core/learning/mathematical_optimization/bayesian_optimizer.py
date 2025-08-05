"""
Bayesian Optimizer for FlipSync Agentic Learning System
Phase 2.1: Advanced Algorithmic Learning Integration

Implements Bayesian optimization for efficient hyperparameter tuning and
global optimization with Gaussian Process surrogate models and acquisition functions.
"""

import asyncio
import logging
import numpy as np
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from scipy.stats import norm
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class AcquisitionFunction(Enum):
    """Acquisition functions for Bayesian optimization."""

    EXPECTED_IMPROVEMENT = "expected_improvement"
    UPPER_CONFIDENCE_BOUND = "upper_confidence_bound"
    PROBABILITY_OF_IMPROVEMENT = "probability_of_improvement"


@dataclass
class BayesianConfig:
    """Configuration for Bayesian optimization."""

    max_iterations: int = 100
    acquisition_function: AcquisitionFunction = AcquisitionFunction.EXPECTED_IMPROVEMENT
    exploration_weight: float = 2.0  # For UCB
    improvement_threshold: float = 0.01  # For PI
    random_seed: Optional[int] = None
    initial_random_samples: int = 5
    kernel_length_scale: float = 1.0
    kernel_variance: float = 1.0
    noise_variance: float = 1e-6


@dataclass
class BayesianResult:
    """Result of Bayesian optimization."""

    best_parameters: Dict[str, float]
    best_objective_value: float
    iterations_completed: int
    optimization_time: float
    evaluation_history: List[Tuple[Dict[str, float], float]]
    acquisition_history: List[float]
    convergence_achieved: bool


class GaussianProcess:
    """Simple Gaussian Process implementation for Bayesian optimization."""

    def __init__(
        self, length_scale: float = 1.0, variance: float = 1.0, noise: float = 1e-6
    ):
        self.length_scale = length_scale
        self.variance = variance
        self.noise = noise
        self.X_train = []
        self.y_train = []
        self.K_inv = None

    def rbf_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Radial basis function (RBF) kernel."""
        sqdist = (
            np.sum(X1**2, axis=1).reshape(-1, 1)
            + np.sum(X2**2, axis=1)
            - 2 * np.dot(X1, X2.T)
        )
        return self.variance * np.exp(-0.5 / self.length_scale**2 * sqdist)

    def fit(self, X: List[np.ndarray], y: List[float]):
        """Fit the Gaussian Process to training data."""
        self.X_train = np.array(X)
        self.y_train = np.array(y)

        if len(self.X_train) == 0:
            return

        # Compute kernel matrix
        K = self.rbf_kernel(self.X_train, self.X_train)
        K += self.noise * np.eye(len(self.X_train))

        # Compute inverse for predictions
        try:
            self.K_inv = np.linalg.inv(K)
        except np.linalg.LinAlgError:
            # Add more noise if matrix is singular
            K += 1e-3 * np.eye(len(self.X_train))
            self.K_inv = np.linalg.inv(K)

    def predict(self, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict mean and variance at test points."""
        if len(self.X_train) == 0:
            return np.zeros(len(X_test)), np.ones(len(X_test))

        X_test = np.array(X_test)
        if X_test.ndim == 1:
            X_test = X_test.reshape(1, -1)

        # Compute kernel matrices
        K_star = self.rbf_kernel(self.X_train, X_test)
        K_star_star = self.rbf_kernel(X_test, X_test)

        # Predict mean
        mean = K_star.T @ self.K_inv @ self.y_train

        # Predict variance
        variance = np.diag(K_star_star) - np.diag(K_star.T @ self.K_inv @ K_star)
        variance = np.maximum(variance, 1e-8)  # Ensure positive variance

        return mean, variance


class BayesianOptimizer:
    """
    Advanced Bayesian optimizer for global optimization.

    Features:
    - Gaussian Process surrogate models
    - Multiple acquisition functions
    - Efficient global optimization
    - Uncertainty quantification
    - Convergence detection
    """

    def __init__(self, config: BayesianConfig):
        """Initialize the Bayesian optimizer.

        Args:
            config: Configuration for optimization parameters
        """
        self.config = config
        self.optimization_history: List[BayesianResult] = []

        if config.random_seed is not None:
            np.random.seed(config.random_seed)

        # Initialize Gaussian Process
        self.gp = GaussianProcess(
            length_scale=config.kernel_length_scale,
            variance=config.kernel_variance,
            noise=config.noise_variance,
        )

    async def optimize(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameter_bounds: Dict[str, Tuple[float, float]],
        maximize: bool = True,
        timeout_ms: float = 800.0,
    ) -> BayesianResult:
        """
        Perform Bayesian optimization with timeout and fallback.

        Args:
            objective_function: Function to optimize
            parameter_bounds: Parameter bounds as {param: (min, max)}
            maximize: Whether to maximize (True) or minimize (False) the objective
            timeout_ms: Timeout in milliseconds (default: 800ms)

        Returns:
            BayesianResult with optimization details
        """
        try:
            # Implement timeout wrapper
            result = await asyncio.wait_for(
                self._run_optimization(objective_function, parameter_bounds, maximize),
                timeout=timeout_ms / 1000.0,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(
                f"Bayesian optimization timeout ({timeout_ms}ms), using fallback"
            )
            return await self._fallback_optimization(
                objective_function, parameter_bounds, maximize
            )

    async def _run_optimization(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameter_bounds: Dict[str, Tuple[float, float]],
        maximize: bool = True,
    ) -> BayesianResult:
        """Run the actual Bayesian optimization process."""
        start_time = time.time()

        # Initialize optimization state
        param_names = list(parameter_bounds.keys())
        bounds_array = np.array([parameter_bounds[name] for name in param_names])

        # History tracking
        evaluation_history = []
        acquisition_history = []

        # Best found so far
        best_params = None
        best_value = -np.inf if maximize else np.inf

        logger.info(
            f"🎯 Starting Bayesian optimization with {len(param_names)} parameters"
        )

        # Initial random sampling
        for i in range(self.config.initial_random_samples):
            # Sample random parameters within bounds
            random_params = {}
            param_vector = []

            for j, param_name in enumerate(param_names):
                min_val, max_val = bounds_array[j]
                value = np.random.uniform(min_val, max_val)
                random_params[param_name] = value
                param_vector.append(value)

            # Evaluate objective
            obj_value = await self._evaluate_objective(
                objective_function, random_params
            )
            evaluation_history.append((random_params.copy(), obj_value))

            # Update best
            if (maximize and obj_value > best_value) or (
                not maximize and obj_value < best_value
            ):
                best_value = obj_value
                best_params = random_params.copy()

            logger.debug(f"Random sample {i+1}: {obj_value:.6f}")

        # Main Bayesian optimization loop
        for iteration in range(
            self.config.max_iterations - self.config.initial_random_samples
        ):
            # Prepare training data for GP
            X_train = []
            y_train = []

            for params, value in evaluation_history:
                param_vector = [params[name] for name in param_names]
                X_train.append(param_vector)
                # Negate for maximization to convert to minimization
                y_train.append(-value if maximize else value)

            # Fit Gaussian Process
            self.gp.fit(X_train, y_train)

            # Find next point to evaluate using acquisition function
            next_params = await self._optimize_acquisition(
                param_names, bounds_array, maximize
            )

            # Evaluate objective at next point
            obj_value = await self._evaluate_objective(objective_function, next_params)
            evaluation_history.append((next_params.copy(), obj_value))

            # Calculate acquisition value for history
            param_vector = [next_params[name] for name in param_names]
            acq_value = await self._calculate_acquisition(
                np.array(param_vector).reshape(1, -1), maximize
            )
            acquisition_history.append(acq_value[0])

            # Update best
            if (maximize and obj_value > best_value) or (
                not maximize and obj_value < best_value
            ):
                best_value = obj_value
                best_params = next_params.copy()

            # Check convergence (simple improvement-based)
            if len(evaluation_history) > 10:
                recent_values = [val for _, val in evaluation_history[-10:]]
                if maximize:
                    improvement = max(recent_values) - max(
                        [val for _, val in evaluation_history[:-10]]
                    )
                else:
                    improvement = min(
                        [val for _, val in evaluation_history[:-10]]
                    ) - min(recent_values)

                if improvement < self.config.improvement_threshold:
                    logger.info(
                        f"✅ Convergence achieved at iteration {iteration + self.config.initial_random_samples}"
                    )
                    break

            # Log progress
            if iteration % 10 == 0:
                logger.debug(
                    f"Iteration {iteration + self.config.initial_random_samples}: "
                    f"best={best_value:.6f}, current={obj_value:.6f}"
                )

        optimization_time = time.time() - start_time
        convergence_achieved = len(evaluation_history) < self.config.max_iterations

        result = BayesianResult(
            best_parameters=best_params,
            best_objective_value=best_value,
            iterations_completed=len(evaluation_history),
            optimization_time=optimization_time,
            evaluation_history=evaluation_history,
            acquisition_history=acquisition_history,
            convergence_achieved=convergence_achieved,
        )

        self.optimization_history.append(result)

        logger.info(
            f"🎯 Bayesian optimization completed: {len(evaluation_history)} evaluations, "
            f"best_value={best_value:.6f}, time={optimization_time:.3f}s"
        )

        return result

    async def _evaluate_objective(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameters: Dict[str, float],
    ) -> float:
        """Evaluate objective function safely."""
        try:
            return objective_function(parameters)
        except Exception as e:
            logger.error(f"Error evaluating objective function: {e}")
            return -np.inf  # Return worst possible value

    async def _optimize_acquisition(
        self, param_names: List[str], bounds_array: np.ndarray, maximize: bool
    ) -> Dict[str, float]:
        """Optimize acquisition function to find next evaluation point."""

        def acquisition_objective(x):
            """Objective for acquisition optimization (minimize)."""
            # Use synchronous calculation to avoid asyncio.run() in running loop
            acq_value = self._calculate_acquisition_sync(x.reshape(1, -1), maximize)
            return -acq_value[0]  # Minimize negative acquisition

        # Multiple random starts for global optimization
        best_x = None
        best_acq = np.inf

        for _ in range(10):  # 10 random starts
            # Random starting point
            x0 = np.array(
                [
                    np.random.uniform(bounds_array[i, 0], bounds_array[i, 1])
                    for i in range(len(param_names))
                ]
            )

            # Optimize acquisition function
            result = minimize(
                acquisition_objective, x0, bounds=bounds_array, method="L-BFGS-B"
            )

            if result.success and result.fun < best_acq:
                best_acq = result.fun
                best_x = result.x

        # Convert back to parameter dictionary
        if best_x is None:
            # Fallback to random point
            best_x = np.array(
                [
                    np.random.uniform(bounds_array[i, 0], bounds_array[i, 1])
                    for i in range(len(param_names))
                ]
            )

        return {param_names[i]: best_x[i] for i in range(len(param_names))}

    async def _calculate_acquisition(self, X: np.ndarray, maximize: bool) -> np.ndarray:
        """Calculate acquisition function values."""
        return self._calculate_acquisition_sync(X, maximize)

    def _calculate_acquisition_sync(self, X: np.ndarray, maximize: bool) -> np.ndarray:
        """Calculate acquisition function values synchronously."""
        if len(self.gp.X_train) == 0:
            return np.ones(len(X))  # Return uniform acquisition for first points

        # Get GP predictions
        mean, variance = self.gp.predict(X)
        std = np.sqrt(variance)

        if self.config.acquisition_function == AcquisitionFunction.EXPECTED_IMPROVEMENT:
            return self._expected_improvement(mean, std, maximize)
        elif (
            self.config.acquisition_function
            == AcquisitionFunction.UPPER_CONFIDENCE_BOUND
        ):
            return self._upper_confidence_bound(mean, std, maximize)
        elif (
            self.config.acquisition_function
            == AcquisitionFunction.PROBABILITY_OF_IMPROVEMENT
        ):
            return self._probability_of_improvement(mean, std, maximize)
        else:
            return self._expected_improvement(mean, std, maximize)

    def _expected_improvement(
        self, mean: np.ndarray, std: np.ndarray, maximize: bool
    ) -> np.ndarray:
        """Expected Improvement acquisition function."""
        if maximize:
            best_f = -min(self.gp.y_train)  # Convert back from minimization
            improvement = mean + best_f
        else:
            best_f = min(self.gp.y_train)
            improvement = best_f - mean

        z = improvement / (std + 1e-8)
        ei = improvement * norm.cdf(z) + std * norm.pdf(z)
        return np.maximum(ei, 0.0)

    def _upper_confidence_bound(
        self, mean: np.ndarray, std: np.ndarray, maximize: bool
    ) -> np.ndarray:
        """Upper Confidence Bound acquisition function."""
        if maximize:
            return (
                -mean + self.config.exploration_weight * std
            )  # Convert from minimization
        else:
            return mean - self.config.exploration_weight * std

    def _probability_of_improvement(
        self, mean: np.ndarray, std: np.ndarray, maximize: bool
    ) -> np.ndarray:
        """Probability of Improvement acquisition function."""
        if maximize:
            best_f = -min(self.gp.y_train)
            improvement = mean - best_f - self.config.improvement_threshold
        else:
            best_f = min(self.gp.y_train)
            improvement = best_f - mean - self.config.improvement_threshold

        z = improvement / (std + 1e-8)
        return norm.cdf(z)

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        if not self.optimization_history:
            return {"message": "No optimization history available"}

        recent_result = self.optimization_history[-1]

        return {
            "total_optimizations": len(self.optimization_history),
            "recent_optimization": {
                "iterations": recent_result.iterations_completed,
                "convergence_achieved": recent_result.convergence_achieved,
                "optimization_time": recent_result.optimization_time,
                "best_objective": recent_result.best_objective_value,
                "parameter_count": len(recent_result.best_parameters),
            },
            "average_optimization_time": np.mean(
                [r.optimization_time for r in self.optimization_history]
            ),
            "convergence_rate": np.mean(
                [r.convergence_achieved for r in self.optimization_history]
            ),
            "acquisition_function": self.config.acquisition_function.value,
        }

    async def _fallback_optimization(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameter_bounds: Dict[str, Tuple[float, float]],
        maximize: bool = True,
    ) -> BayesianResult:
        """Fallback optimization using simple random search when Bayesian times out."""
        start_time = time.time()
        param_names = list(parameter_bounds.keys())
        bounds_array = np.array([parameter_bounds[name] for name in param_names])

        best_params = None
        best_value = float("-inf") if maximize else float("inf")
        evaluation_history = []

        # Simple random search with limited evaluations
        for i in range(10):  # Quick fallback with 10 random samples
            # Generate random parameters
            random_params_array = np.random.uniform(
                bounds_array[:, 0], bounds_array[:, 1]
            )
            random_params = {
                param_names[j]: random_params_array[j] for j in range(len(param_names))
            }

            # Evaluate objective
            try:
                value = objective_function(random_params)
                evaluation_history.append((random_params.copy(), value))

                # Update best
                if (maximize and value > best_value) or (
                    not maximize and value < best_value
                ):
                    best_value = value
                    best_params = random_params.copy()

            except Exception as e:
                logger.warning(f"Fallback evaluation failed: {e}")
                continue

        # Return fallback result
        return BayesianResult(
            best_parameters=best_params or {name: 0.0 for name in param_names},
            best_value=best_value if best_params else 0.0,
            convergence_achieved=False,  # Fallback never "converges"
            total_evaluations=len(evaluation_history),
            optimization_time=time.time() - start_time,
            evaluation_history=evaluation_history,
            acquisition_history=[],  # No acquisition in fallback
            gp_predictions=[],  # No GP in fallback
        )
