"""
Gradient Descent Optimizer for FlipSync Agentic Learning System
Phase 2.1: Advanced Algorithmic Learning Integration

Implements gradient descent optimization for continuous parameter optimization
in agent learning systems, including adaptive learning rates and momentum.
"""

import logging
import numpy as np
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """Optimization objectives for gradient descent."""
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_PROFIT = "maximize_profit"
    MAXIMIZE_ACCURACY = "maximize_accuracy"
    MINIMIZE_TIME = "minimize_time"
    MAXIMIZE_EFFICIENCY = "maximize_efficiency"


@dataclass
class GradientDescentConfig:
    """Configuration for gradient descent optimization."""
    learning_rate: float = 0.01
    momentum: float = 0.9
    max_iterations: int = 1000
    convergence_threshold: float = 1e-6
    adaptive_learning_rate: bool = True
    learning_rate_decay: float = 0.95
    gradient_clipping: float = 1.0
    batch_size: int = 32


@dataclass
class OptimizationResult:
    """Result of gradient descent optimization."""
    optimized_parameters: Dict[str, float]
    final_objective_value: float
    iterations_completed: int
    convergence_achieved: bool
    optimization_time: float
    gradient_history: List[Dict[str, float]]
    objective_history: List[float]


class GradientDescentOptimizer:
    """
    Advanced gradient descent optimizer for agent learning systems.
    
    Features:
    - Adaptive learning rates with decay
    - Momentum-based optimization
    - Gradient clipping for stability
    - Multiple optimization objectives
    - Convergence detection
    - Performance monitoring
    """

    def __init__(self, config: GradientDescentConfig):
        """Initialize the gradient descent optimizer.
        
        Args:
            config: Configuration for optimization parameters
        """
        self.config = config
        self.optimization_history: List[OptimizationResult] = []
        
        # Momentum tracking
        self.velocity: Dict[str, float] = {}
        
        # Adaptive learning rate tracking
        self.current_learning_rate = config.learning_rate
        self.learning_rate_history: List[float] = []

    async def optimize(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        initial_parameters: Dict[str, float],
        objective: OptimizationObjective,
        constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        gradient_function: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None
    ) -> OptimizationResult:
        """
        Perform gradient descent optimization.
        
        Args:
            objective_function: Function to optimize (takes parameters, returns scalar)
            initial_parameters: Starting parameter values
            objective: Optimization objective (minimize/maximize)
            constraints: Optional parameter bounds as (min, max) tuples
            gradient_function: Optional analytical gradient function
            
        Returns:
            OptimizationResult with optimization details
        """
        start_time = time.time()
        
        # Initialize optimization state
        current_params = initial_parameters.copy()
        self.velocity = {key: 0.0 for key in current_params.keys()}
        self.current_learning_rate = self.config.learning_rate
        
        # History tracking
        gradient_history = []
        objective_history = []
        
        logger.info(f"🎯 Starting gradient descent optimization with {len(current_params)} parameters")
        
        for iteration in range(self.config.max_iterations):
            # Calculate objective value
            current_objective = await self._evaluate_objective(
                objective_function, current_params, objective
            )
            objective_history.append(current_objective)
            
            # Calculate gradients
            if gradient_function:
                gradients = gradient_function(current_params)
            else:
                gradients = await self._numerical_gradient(
                    objective_function, current_params, objective
                )
            
            gradient_history.append(gradients.copy())
            
            # Apply gradient clipping
            gradients = self._clip_gradients(gradients)
            
            # Check convergence
            gradient_norm = np.sqrt(sum(g**2 for g in gradients.values()))
            if gradient_norm < self.config.convergence_threshold:
                logger.info(f"✅ Convergence achieved at iteration {iteration}")
                break
            
            # Update parameters using momentum
            current_params = self._update_parameters_with_momentum(
                current_params, gradients, constraints
            )
            
            # Update learning rate (adaptive)
            if self.config.adaptive_learning_rate:
                self._update_learning_rate(iteration)
            
            # Log progress periodically
            if iteration % 100 == 0:
                logger.debug(
                    f"Iteration {iteration}: objective={current_objective:.6f}, "
                    f"gradient_norm={gradient_norm:.6f}, lr={self.current_learning_rate:.6f}"
                )
        
        # Final evaluation
        final_objective = await self._evaluate_objective(
            objective_function, current_params, objective
        )
        
        optimization_time = time.time() - start_time
        convergence_achieved = gradient_norm < self.config.convergence_threshold
        
        result = OptimizationResult(
            optimized_parameters=current_params,
            final_objective_value=final_objective,
            iterations_completed=iteration + 1,
            convergence_achieved=convergence_achieved,
            optimization_time=optimization_time,
            gradient_history=gradient_history,
            objective_history=objective_history
        )
        
        self.optimization_history.append(result)
        
        logger.info(
            f"🎯 Optimization completed: {iteration + 1} iterations, "
            f"final_objective={final_objective:.6f}, time={optimization_time:.3f}s"
        )
        
        return result

    async def _evaluate_objective(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameters: Dict[str, float],
        objective: OptimizationObjective
    ) -> float:
        """Evaluate objective function with proper sign handling."""
        try:
            value = objective_function(parameters)
            
            # Handle maximization by negating the value
            if objective in [OptimizationObjective.MAXIMIZE_PROFIT, 
                           OptimizationObjective.MAXIMIZE_ACCURACY,
                           OptimizationObjective.MAXIMIZE_EFFICIENCY]:
                return -value
            else:
                return value
                
        except Exception as e:
            logger.error(f"Error evaluating objective function: {e}")
            return float('inf')

    async def _numerical_gradient(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameters: Dict[str, float],
        objective: OptimizationObjective,
        epsilon: float = 1e-8
    ) -> Dict[str, float]:
        """Calculate numerical gradients using finite differences."""
        gradients = {}
        
        for param_name, param_value in parameters.items():
            # Forward difference
            params_forward = parameters.copy()
            params_forward[param_name] = param_value + epsilon
            
            params_backward = parameters.copy()
            params_backward[param_name] = param_value - epsilon
            
            # Calculate gradient using central difference
            forward_value = await self._evaluate_objective(
                objective_function, params_forward, objective
            )
            backward_value = await self._evaluate_objective(
                objective_function, params_backward, objective
            )
            
            gradients[param_name] = (forward_value - backward_value) / (2 * epsilon)
        
        return gradients

    def _clip_gradients(self, gradients: Dict[str, float]) -> Dict[str, float]:
        """Apply gradient clipping to prevent exploding gradients."""
        if self.config.gradient_clipping <= 0:
            return gradients
        
        # Calculate gradient norm
        gradient_norm = np.sqrt(sum(g**2 for g in gradients.values()))
        
        if gradient_norm > self.config.gradient_clipping:
            # Scale gradients to clip norm
            scale_factor = self.config.gradient_clipping / gradient_norm
            return {key: value * scale_factor for key, value in gradients.items()}
        
        return gradients

    def _update_parameters_with_momentum(
        self,
        parameters: Dict[str, float],
        gradients: Dict[str, float],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, float]:
        """Update parameters using momentum-based gradient descent."""
        updated_params = {}
        
        for param_name, param_value in parameters.items():
            gradient = gradients.get(param_name, 0.0)
            
            # Update velocity with momentum
            self.velocity[param_name] = (
                self.config.momentum * self.velocity[param_name] - 
                self.current_learning_rate * gradient
            )
            
            # Update parameter
            new_value = param_value + self.velocity[param_name]
            
            # Apply constraints if provided
            if constraints and param_name in constraints:
                min_val, max_val = constraints[param_name]
                new_value = max(min_val, min(max_val, new_value))
            
            updated_params[param_name] = new_value
        
        return updated_params

    def _update_learning_rate(self, iteration: int):
        """Update learning rate with decay schedule."""
        if iteration > 0 and iteration % 100 == 0:
            self.current_learning_rate *= self.config.learning_rate_decay
            self.learning_rate_history.append(self.current_learning_rate)
            
            logger.debug(f"Learning rate updated to {self.current_learning_rate:.6f}")

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
                "final_objective": recent_result.final_objective_value,
                "parameter_count": len(recent_result.optimized_parameters)
            },
            "average_optimization_time": np.mean([r.optimization_time for r in self.optimization_history]),
            "convergence_rate": np.mean([r.convergence_achieved for r in self.optimization_history]),
            "current_learning_rate": self.current_learning_rate
        }
