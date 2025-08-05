"""
Evolutionary Algorithm for FlipSync Agentic Learning System
Phase 2.1: Advanced Algorithmic Learning Integration

Implements genetic algorithm and evolutionary strategies for global optimization
and strategic planning in agent learning systems.
"""

import logging
import numpy as np
import time
from typing import Any, Dict, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SelectionMethod(Enum):
    """Selection methods for evolutionary algorithm."""
    TOURNAMENT = "tournament"
    ROULETTE_WHEEL = "roulette_wheel"
    RANK_BASED = "rank_based"
    ELITIST = "elitist"


class CrossoverMethod(Enum):
    """Crossover methods for evolutionary algorithm."""
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    ARITHMETIC = "arithmetic"


class MutationMethod(Enum):
    """Mutation methods for evolutionary algorithm."""
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    POLYNOMIAL = "polynomial"


@dataclass
class EvolutionaryConfig:
    """Configuration for evolutionary algorithm."""
    population_size: int = 50
    max_generations: int = 100
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    crossover_method: CrossoverMethod = CrossoverMethod.ARITHMETIC
    mutation_method: MutationMethod = MutationMethod.GAUSSIAN
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    mutation_strength: float = 0.1
    tournament_size: int = 3
    elitism_rate: float = 0.1
    convergence_threshold: float = 1e-6
    diversity_threshold: float = 0.01


@dataclass
class Individual:
    """Individual in the evolutionary algorithm population."""
    parameters: Dict[str, float]
    fitness: float
    age: int = 0


@dataclass
class EvolutionaryResult:
    """Result of evolutionary algorithm optimization."""
    best_individual: Individual
    population_history: List[List[Individual]]
    fitness_history: List[List[float]]
    diversity_history: List[float]
    optimization_time: float
    generations_completed: int
    convergence_achieved: bool


class EvolutionaryAlgorithm:
    """
    Advanced evolutionary algorithm for global optimization.
    
    Features:
    - Multiple selection strategies
    - Various crossover and mutation operators
    - Diversity preservation mechanisms
    - Elitism and age-based selection
    - Convergence detection
    - Population statistics tracking
    """

    def __init__(self, config: EvolutionaryConfig):
        """Initialize the evolutionary algorithm.
        
        Args:
            config: Configuration for evolutionary parameters
        """
        self.config = config
        self.optimization_history: List[EvolutionaryResult] = []
        self.current_generation = 0

    async def optimize(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        parameter_bounds: Dict[str, Tuple[float, float]],
        maximize: bool = True
    ) -> EvolutionaryResult:
        """
        Perform evolutionary optimization.
        
        Args:
            objective_function: Function to optimize
            parameter_bounds: Parameter bounds as {param: (min, max)}
            maximize: Whether to maximize (True) or minimize (False) the objective
            
        Returns:
            EvolutionaryResult with optimization details
        """
        start_time = time.time()
        
        # Initialize population
        population = await self._initialize_population(parameter_bounds, objective_function, maximize)
        
        # History tracking
        population_history = [population.copy()]
        fitness_history = [[ind.fitness for ind in population]]
        diversity_history = [self._calculate_diversity(population)]
        
        best_individual = max(population, key=lambda x: x.fitness)
        
        logger.info(f"🧬 Starting evolutionary optimization with population size {self.config.population_size}")
        
        # Main evolutionary loop
        for generation in range(self.config.max_generations):
            self.current_generation = generation
            
            # Selection
            selected_parents = await self._selection(population)
            
            # Crossover and Mutation
            offspring = await self._reproduction(selected_parents, parameter_bounds)
            
            # Evaluate offspring
            await self._evaluate_population(offspring, objective_function, maximize)
            
            # Survival selection (combine parents and offspring)
            population = await self._survival_selection(population, offspring)
            
            # Update best individual
            current_best = max(population, key=lambda x: x.fitness)
            if current_best.fitness > best_individual.fitness:
                best_individual = current_best
            
            # Track history
            population_history.append(population.copy())
            fitness_history.append([ind.fitness for ind in population])
            diversity_history.append(self._calculate_diversity(population))
            
            # Check convergence
            if await self._check_convergence(fitness_history, diversity_history):
                logger.info(f"✅ Convergence achieved at generation {generation}")
                break
            
            # Age population
            for individual in population:
                individual.age += 1
            
            # Log progress
            if generation % 10 == 0:
                avg_fitness = np.mean([ind.fitness for ind in population])
                diversity = diversity_history[-1]
                logger.debug(
                    f"Generation {generation}: best={best_individual.fitness:.6f}, "
                    f"avg={avg_fitness:.6f}, diversity={diversity:.6f}"
                )
        
        optimization_time = time.time() - start_time
        convergence_achieved = generation < self.config.max_generations - 1
        
        result = EvolutionaryResult(
            best_individual=best_individual,
            population_history=population_history,
            fitness_history=fitness_history,
            diversity_history=diversity_history,
            optimization_time=optimization_time,
            generations_completed=generation + 1,
            convergence_achieved=convergence_achieved
        )
        
        self.optimization_history.append(result)
        
        logger.info(
            f"🧬 Evolutionary optimization completed: {generation + 1} generations, "
            f"best_fitness={best_individual.fitness:.6f}, time={optimization_time:.3f}s"
        )
        
        return result

    async def _initialize_population(
        self,
        parameter_bounds: Dict[str, Tuple[float, float]],
        objective_function: Callable[[Dict[str, float]], float],
        maximize: bool
    ) -> List[Individual]:
        """Initialize random population within parameter bounds."""
        population = []
        param_names = list(parameter_bounds.keys())
        
        for _ in range(self.config.population_size):
            # Generate random parameters
            parameters = {}
            for param_name in param_names:
                min_val, max_val = parameter_bounds[param_name]
                parameters[param_name] = np.random.uniform(min_val, max_val)
            
            # Create individual
            individual = Individual(parameters=parameters, fitness=0.0)
            population.append(individual)
        
        # Evaluate initial population
        await self._evaluate_population(population, objective_function, maximize)
        
        return population

    async def _evaluate_population(
        self,
        population: List[Individual],
        objective_function: Callable[[Dict[str, float]], float],
        maximize: bool
    ):
        """Evaluate fitness for all individuals in population."""
        for individual in population:
            try:
                raw_fitness = objective_function(individual.parameters)
                # Convert to maximization problem if needed
                individual.fitness = raw_fitness if maximize else -raw_fitness
            except Exception as e:
                logger.error(f"Error evaluating individual: {e}")
                individual.fitness = -np.inf

    async def _selection(self, population: List[Individual]) -> List[Individual]:
        """Select parents for reproduction."""
        if self.config.selection_method == SelectionMethod.TOURNAMENT:
            return self._tournament_selection(population)
        elif self.config.selection_method == SelectionMethod.ROULETTE_WHEEL:
            return self._roulette_wheel_selection(population)
        elif self.config.selection_method == SelectionMethod.RANK_BASED:
            return self._rank_based_selection(population)
        elif self.config.selection_method == SelectionMethod.ELITIST:
            return self._elitist_selection(population)
        else:
            return self._tournament_selection(population)

    def _tournament_selection(self, population: List[Individual]) -> List[Individual]:
        """Tournament selection method."""
        selected = []
        
        for _ in range(self.config.population_size):
            # Select random individuals for tournament
            tournament = np.random.choice(population, size=self.config.tournament_size, replace=False)
            # Select best from tournament
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected

    def _roulette_wheel_selection(self, population: List[Individual]) -> List[Individual]:
        """Roulette wheel selection method."""
        # Shift fitness to ensure all values are positive
        min_fitness = min(ind.fitness for ind in population)
        shifted_fitness = [ind.fitness - min_fitness + 1e-8 for ind in population]
        total_fitness = sum(shifted_fitness)
        
        selected = []
        for _ in range(self.config.population_size):
            pick = np.random.uniform(0, total_fitness)
            current = 0
            for i, individual in enumerate(population):
                current += shifted_fitness[i]
                if current >= pick:
                    selected.append(individual)
                    break
        
        return selected

    def _rank_based_selection(self, population: List[Individual]) -> List[Individual]:
        """Rank-based selection method."""
        # Sort population by fitness
        sorted_pop = sorted(population, key=lambda x: x.fitness)
        
        # Assign selection probabilities based on rank
        ranks = np.arange(1, len(population) + 1)
        probabilities = ranks / np.sum(ranks)
        
        selected = []
        for _ in range(self.config.population_size):
            idx = np.random.choice(len(population), p=probabilities)
            selected.append(sorted_pop[idx])
        
        return selected

    def _elitist_selection(self, population: List[Individual]) -> List[Individual]:
        """Elitist selection method."""
        # Sort by fitness (descending)
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        
        # Select top individuals
        elite_count = int(self.config.elitism_rate * self.config.population_size)
        selected = sorted_pop[:elite_count]
        
        # Fill remaining with tournament selection
        remaining_count = self.config.population_size - elite_count
        for _ in range(remaining_count):
            tournament = np.random.choice(population, size=self.config.tournament_size, replace=False)
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected

    async def _reproduction(
        self,
        parents: List[Individual],
        parameter_bounds: Dict[str, Tuple[float, float]]
    ) -> List[Individual]:
        """Create offspring through crossover and mutation."""
        offspring = []
        param_names = list(parameter_bounds.keys())
        
        # Create pairs for crossover
        np.random.shuffle(parents)
        
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1] if i + 1 < len(parents) else parents[0]
            
            # Crossover
            if np.random.random() < self.config.crossover_rate:
                child1_params, child2_params = self._crossover(
                    parent1.parameters, parent2.parameters, param_names
                )
            else:
                child1_params = parent1.parameters.copy()
                child2_params = parent2.parameters.copy()
            
            # Mutation
            child1_params = self._mutate(child1_params, parameter_bounds)
            child2_params = self._mutate(child2_params, parameter_bounds)
            
            # Create offspring individuals
            offspring.append(Individual(parameters=child1_params, fitness=0.0))
            offspring.append(Individual(parameters=child2_params, fitness=0.0))
        
        return offspring

    def _crossover(
        self,
        parent1_params: Dict[str, float],
        parent2_params: Dict[str, float],
        param_names: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Perform crossover between two parents."""
        if self.config.crossover_method == CrossoverMethod.SINGLE_POINT:
            return self._single_point_crossover(parent1_params, parent2_params, param_names)
        elif self.config.crossover_method == CrossoverMethod.TWO_POINT:
            return self._two_point_crossover(parent1_params, parent2_params, param_names)
        elif self.config.crossover_method == CrossoverMethod.UNIFORM:
            return self._uniform_crossover(parent1_params, parent2_params, param_names)
        elif self.config.crossover_method == CrossoverMethod.ARITHMETIC:
            return self._arithmetic_crossover(parent1_params, parent2_params, param_names)
        else:
            return self._arithmetic_crossover(parent1_params, parent2_params, param_names)

    def _arithmetic_crossover(
        self,
        parent1_params: Dict[str, float],
        parent2_params: Dict[str, float],
        param_names: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Arithmetic crossover (weighted average)."""
        alpha = np.random.random()
        
        child1_params = {}
        child2_params = {}
        
        for param_name in param_names:
            p1_val = parent1_params[param_name]
            p2_val = parent2_params[param_name]
            
            child1_params[param_name] = alpha * p1_val + (1 - alpha) * p2_val
            child2_params[param_name] = (1 - alpha) * p1_val + alpha * p2_val
        
        return child1_params, child2_params

    def _uniform_crossover(
        self,
        parent1_params: Dict[str, float],
        parent2_params: Dict[str, float],
        param_names: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Uniform crossover."""
        child1_params = {}
        child2_params = {}
        
        for param_name in param_names:
            if np.random.random() < 0.5:
                child1_params[param_name] = parent1_params[param_name]
                child2_params[param_name] = parent2_params[param_name]
            else:
                child1_params[param_name] = parent2_params[param_name]
                child2_params[param_name] = parent1_params[param_name]
        
        return child1_params, child2_params

    def _single_point_crossover(
        self,
        parent1_params: Dict[str, float],
        parent2_params: Dict[str, float],
        param_names: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Single-point crossover."""
        crossover_point = np.random.randint(1, len(param_names))
        
        child1_params = {}
        child2_params = {}
        
        for i, param_name in enumerate(param_names):
            if i < crossover_point:
                child1_params[param_name] = parent1_params[param_name]
                child2_params[param_name] = parent2_params[param_name]
            else:
                child1_params[param_name] = parent2_params[param_name]
                child2_params[param_name] = parent1_params[param_name]
        
        return child1_params, child2_params

    def _two_point_crossover(
        self,
        parent1_params: Dict[str, float],
        parent2_params: Dict[str, float],
        param_names: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Two-point crossover."""
        point1 = np.random.randint(0, len(param_names))
        point2 = np.random.randint(point1, len(param_names))
        
        child1_params = {}
        child2_params = {}
        
        for i, param_name in enumerate(param_names):
            if point1 <= i < point2:
                child1_params[param_name] = parent2_params[param_name]
                child2_params[param_name] = parent1_params[param_name]
            else:
                child1_params[param_name] = parent1_params[param_name]
                child2_params[param_name] = parent2_params[param_name]
        
        return child1_params, child2_params

    def _mutate(
        self,
        parameters: Dict[str, float],
        parameter_bounds: Dict[str, Tuple[float, float]]
    ) -> Dict[str, float]:
        """Apply mutation to parameters."""
        mutated_params = parameters.copy()
        
        for param_name, param_value in parameters.items():
            if np.random.random() < self.config.mutation_rate:
                min_val, max_val = parameter_bounds[param_name]
                
                if self.config.mutation_method == MutationMethod.GAUSSIAN:
                    # Gaussian mutation
                    mutation = np.random.normal(0, self.config.mutation_strength * (max_val - min_val))
                    new_value = param_value + mutation
                elif self.config.mutation_method == MutationMethod.UNIFORM:
                    # Uniform mutation
                    new_value = np.random.uniform(min_val, max_val)
                else:
                    # Default to Gaussian
                    mutation = np.random.normal(0, self.config.mutation_strength * (max_val - min_val))
                    new_value = param_value + mutation
                
                # Ensure bounds
                mutated_params[param_name] = np.clip(new_value, min_val, max_val)
        
        return mutated_params

    async def _survival_selection(
        self,
        parents: List[Individual],
        offspring: List[Individual]
    ) -> List[Individual]:
        """Select survivors for next generation."""
        # Combine parents and offspring
        combined = parents + offspring
        
        # Sort by fitness (descending)
        combined.sort(key=lambda x: x.fitness, reverse=True)
        
        # Select top individuals
        return combined[:self.config.population_size]

    def _calculate_diversity(self, population: List[Individual]) -> float:
        """Calculate population diversity."""
        if len(population) < 2:
            return 0.0
        
        # Calculate average pairwise distance
        total_distance = 0.0
        count = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                distance = self._individual_distance(population[i], population[j])
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0

    def _individual_distance(self, ind1: Individual, ind2: Individual) -> float:
        """Calculate distance between two individuals."""
        distance = 0.0
        param_count = 0
        
        for param_name in ind1.parameters:
            if param_name in ind2.parameters:
                diff = ind1.parameters[param_name] - ind2.parameters[param_name]
                distance += diff ** 2
                param_count += 1
        
        return np.sqrt(distance / param_count) if param_count > 0 else 0.0

    async def _check_convergence(
        self,
        fitness_history: List[List[float]],
        diversity_history: List[float]
    ) -> bool:
        """Check if algorithm has converged."""
        if len(fitness_history) < 10:
            return False
        
        # Check fitness improvement
        recent_best = [max(generation) for generation in fitness_history[-10:]]
        fitness_improvement = max(recent_best) - min(recent_best)
        
        # Check diversity
        recent_diversity = diversity_history[-1]
        
        return (fitness_improvement < self.config.convergence_threshold and 
                recent_diversity < self.config.diversity_threshold)

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        if not self.optimization_history:
            return {"message": "No optimization history available"}
        
        recent_result = self.optimization_history[-1]
        
        return {
            "total_optimizations": len(self.optimization_history),
            "recent_optimization": {
                "generations": recent_result.generations_completed,
                "convergence_achieved": recent_result.convergence_achieved,
                "optimization_time": recent_result.optimization_time,
                "best_fitness": recent_result.best_individual.fitness,
                "final_diversity": recent_result.diversity_history[-1] if recent_result.diversity_history else 0.0
            },
            "average_optimization_time": np.mean([r.optimization_time for r in self.optimization_history]),
            "convergence_rate": np.mean([r.convergence_achieved for r in self.optimization_history]),
            "population_size": self.config.population_size,
            "selection_method": self.config.selection_method.value
        }
