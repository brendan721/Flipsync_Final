"""
Mathematical Optimization Package for FlipSync Agentic Learning System
Phase 2.1: Advanced Algorithmic Learning Integration

This package provides sophisticated mathematical optimization algorithms
for agent learning systems including gradient descent, Bayesian optimization,
evolutionary algorithms, and Thompson sampling.
"""

from .gradient_descent_optimizer import (
    GradientDescentOptimizer,
    GradientDescentConfig,
    OptimizationObjective,
    OptimizationResult
)

from .bayesian_optimizer import (
    BayesianOptimizer,
    BayesianConfig,
    BayesianResult,
    AcquisitionFunction,
    GaussianProcess
)

from .evolutionary_algorithm import (
    EvolutionaryAlgorithm,
    EvolutionaryConfig,
    EvolutionaryResult,
    Individual,
    SelectionMethod,
    CrossoverMethod,
    MutationMethod
)

from .thompson_sampling import (
    ThompsonSampling,
    ThompsonConfig,
    ThompsonResult,
    ArmStatistics,
    PriorType
)

__all__ = [
    # Gradient Descent
    "GradientDescentOptimizer",
    "GradientDescentConfig", 
    "OptimizationObjective",
    "OptimizationResult",
    
    # Bayesian Optimization
    "BayesianOptimizer",
    "BayesianConfig",
    "BayesianResult",
    "AcquisitionFunction",
    "GaussianProcess",
    
    # Evolutionary Algorithm
    "EvolutionaryAlgorithm",
    "EvolutionaryConfig",
    "EvolutionaryResult",
    "Individual",
    "SelectionMethod",
    "CrossoverMethod",
    "MutationMethod",
    
    # Thompson Sampling
    "ThompsonSampling",
    "ThompsonConfig",
    "ThompsonResult",
    "ArmStatistics",
    "PriorType"
]
