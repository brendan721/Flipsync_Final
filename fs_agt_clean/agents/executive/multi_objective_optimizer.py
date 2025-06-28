"""
Multi-Objective Optimizer for decision-making.

This module provides optimization algorithms for making decisions that balance
multiple, potentially conflicting objectives.
"""

import logging
import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class Objective:
    """Represents a single objective to optimize."""

    def __init__(
        self,
        name: str,
        weight: float = 1.0,
        direction: str = "maximize",
        evaluation_func: Optional[Callable[[Dict[str, Any]], float]] = None,
    ):
        """
        Initialize an objective.

        Args:
            name: Name of the objective
            weight: Relative importance of this objective (0.0 to 1.0)
            direction: "maximize" or "minimize"
            evaluation_func: Function to evaluate this objective for a solution
        """
        self.name = name
        self.weight = max(0.0, min(1.0, weight))  # Clamp to [0, 1]

        if direction not in ["maximize", "minimize"]:
            raise ValueError("Direction must be 'maximize' or 'minimize'")
        self.direction = direction

        self.evaluation_func = evaluation_func

    def evaluate(self, solution: Dict[str, Any]) -> float:
        """
        Evaluate this objective for a solution.

        Args:
            solution: Solution to evaluate

        Returns:
            Objective value
        """
        if self.evaluation_func is None:
            # Default to using the objective name as a key in the solution
            if self.name not in solution:
                raise ValueError(
                    f"Solution does not contain value for objective {self.name}"
                )
            return solution[self.name]

        return self.evaluation_func(solution)

    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize an objective value to [0, 1].

        Args:
            value: Value to normalize
            min_val: Minimum possible value
            max_val: Maximum possible value

        Returns:
            Normalized value
        """
        if min_val == max_val:
            return 0.5  # Avoid division by zero

        normalized = (value - min_val) / (max_val - min_val)

        # Invert if minimizing
        if self.direction == "minimize":
            normalized = 1.0 - normalized

        return normalized


class Constraint:
    """Represents a constraint on solutions."""

    def __init__(
        self,
        name: str,
        evaluation_func: Callable[[Dict[str, Any]], bool],
        penalty: float = 1000.0,
    ):
        """
        Initialize a constraint.

        Args:
            name: Name of the constraint
            evaluation_func: Function that returns True if constraint is satisfied
            penalty: Penalty value for constraint violation
        """
        self.name = name
        self.evaluation_func = evaluation_func
        self.penalty = penalty

    def is_satisfied(self, solution: Dict[str, Any]) -> bool:
        """
        Check if a solution satisfies this constraint.

        Args:
            solution: Solution to check

        Returns:
            True if constraint is satisfied, False otherwise
        """
        return self.evaluation_func(solution)


class MultiObjectiveOptimizer:
    """
    Optimizer for multi-objective decision problems.

    This class provides algorithms for finding solutions that balance multiple,
    potentially conflicting objectives while satisfying constraints.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the optimizer.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.population_size = self.config.get("population_size", 100)
        self.generations = self.config.get("generations", 50)
        self.mutation_rate = self.config.get("mutation_rate", 0.1)
        self.crossover_rate = self.config.get("crossover_rate", 0.7)
        self.elitism_ratio = self.config.get("elitism_ratio", 0.1)

    def optimize(
        self,
        objectives: List[Objective],
        constraints: List[Constraint],
        solution_space: List[Dict[str, Any]],
        initial_solutions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find Pareto-optimal solutions for multiple objectives.

        Args:
            objectives: List of objectives to optimize
            constraints: List of constraints to satisfy
            solution_space: List of all possible solutions
            initial_solutions: Optional list of initial solutions

        Returns:
            List of Pareto-optimal solutions
        """
        if not solution_space:
            logger.warning("Empty solution space provided")
            return []

        if not objectives:
            logger.warning("No objectives provided")
            return solution_space[:1]  # Return first solution if no objectives

        # If solution space is small, evaluate all solutions
        if len(solution_space) <= self.population_size:
            return self._find_pareto_optimal(objectives, constraints, solution_space)

        # For larger solution spaces, use genetic algorithm
        return self._genetic_algorithm(
            objectives, constraints, solution_space, initial_solutions
        )

    def _find_pareto_optimal(
        self,
        objectives: List[Objective],
        constraints: List[Constraint],
        solutions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Find Pareto-optimal solutions by evaluating all solutions.

        Args:
            objectives: List of objectives to optimize
            constraints: List of constraints to satisfy
            solutions: List of solutions to evaluate

        Returns:
            List of Pareto-optimal solutions
        """
        # Evaluate all solutions
        evaluated_solutions = []

        for solution in solutions:
            # Check constraints
            satisfies_constraints = all(
                constraint.is_satisfied(solution) for constraint in constraints
            )

            if not satisfies_constraints:
                continue

            # Evaluate objectives
            objective_values = [
                objective.evaluate(solution) for objective in objectives
            ]

            evaluated_solutions.append((solution, objective_values))

        # Find Pareto-optimal solutions
        pareto_optimal = []

        for i, (solution, values1) in enumerate(evaluated_solutions):
            is_dominated = False

            for j, (_, values2) in enumerate(evaluated_solutions):
                if i == j:
                    continue

                # Check if solution i is dominated by solution j
                dominates = True

                for obj_idx, objective in enumerate(objectives):
                    if objective.direction == "maximize":
                        if values1[obj_idx] > values2[obj_idx]:
                            dominates = False
                            break
                    else:  # minimize
                        if values1[obj_idx] < values2[obj_idx]:
                            dominates = False
                            break

                if dominates:
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_optimal.append(solution)

        return pareto_optimal

    def _genetic_algorithm(
        self,
        objectives: List[Objective],
        constraints: List[Constraint],
        solution_space: List[Dict[str, Any]],
        initial_solutions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Use genetic algorithm to find Pareto-optimal solutions.

        Args:
            objectives: List of objectives to optimize
            constraints: List of constraints to satisfy
            solution_space: List of all possible solutions
            initial_solutions: Optional list of initial solutions

        Returns:
            List of Pareto-optimal solutions
        """
        # Initialize population
        population = self._initialize_population(solution_space, initial_solutions)

        # Evaluate initial population
        fitness_scores = self._evaluate_population(population, objectives, constraints)

        # Main evolution loop
        for generation in range(self.generations):
            # Select parents
            parents = self._select_parents(population, fitness_scores)

            # Create offspring
            offspring = self._create_offspring(parents, solution_space)

            # Evaluate offspring
            offspring_fitness = self._evaluate_population(
                offspring, objectives, constraints
            )

            # Combine populations with elitism
            elite_count = int(self.elitism_ratio * self.population_size)
            elite_indices = np.argsort(fitness_scores)[-elite_count:]

            elite = [population[i] for i in elite_indices]
            elite_fitness = [fitness_scores[i] for i in elite_indices]

            # Replace population
            population = elite + offspring[: (self.population_size - elite_count)]
            fitness_scores = (
                elite_fitness
                + offspring_fitness[: (self.population_size - elite_count)]
            )

            logger.debug(
                f"Generation {generation + 1}/{self.generations}, "
                f"Best fitness: {max(fitness_scores):.4f}"
            )

        # Return Pareto-optimal solutions from final population
        return self._find_pareto_optimal(objectives, constraints, population)

    def _initialize_population(
        self,
        solution_space: List[Dict[str, Any]],
        initial_solutions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Initialize the population for genetic algorithm.

        Args:
            solution_space: List of all possible solutions
            initial_solutions: Optional list of initial solutions

        Returns:
            Initial population
        """
        population = []

        # Add initial solutions if provided
        if initial_solutions:
            population.extend(initial_solutions)

        # Fill remaining population with random solutions
        remaining = self.population_size - len(population)

        if remaining > 0:
            # Sample randomly from solution space
            if len(solution_space) <= remaining:
                # If solution space is smaller than remaining population, use all solutions
                population.extend(solution_space)
                # Fill any remaining slots with random duplicates
                if len(population) < self.population_size:
                    duplicates = random.choices(
                        solution_space, k=self.population_size - len(population)
                    )
                    population.extend(duplicates)
            else:
                # Sample without replacement if possible
                sampled = random.sample(solution_space, remaining)
                population.extend(sampled)

        return population

    def _evaluate_population(
        self,
        population: List[Dict[str, Any]],
        objectives: List[Objective],
        constraints: List[Constraint],
    ) -> List[float]:
        """
        Evaluate fitness of each solution in the population.

        Args:
            population: List of solutions
            objectives: List of objectives
            constraints: List of constraints

        Returns:
            List of fitness scores
        """
        fitness_scores = []

        # Get min and max values for each objective for normalization
        objective_values = [[] for _ in objectives]

        for solution in population:
            for i, objective in enumerate(objectives):
                try:
                    value = objective.evaluate(solution)
                    objective_values[i].append(value)
                except Exception as e:
                    logger.warning(f"Error evaluating objective {objective.name}: {e}")
                    objective_values[i].append(0.0)

        # Calculate min and max for each objective
        min_values = [min(values) if values else 0.0 for values in objective_values]
        max_values = [max(values) if values else 1.0 for values in objective_values]

        # Evaluate each solution
        for solution in population:
            # Check constraints
            constraint_violations = 0

            for constraint in constraints:
                if not constraint.is_satisfied(solution):
                    constraint_violations += 1

            # Calculate weighted sum of normalized objective values
            weighted_sum = 0.0
            total_weight = 0.0

            for i, objective in enumerate(objectives):
                try:
                    value = objective.evaluate(solution)
                    normalized = objective.normalize(
                        value, min_values[i], max_values[i]
                    )
                    weighted_sum += normalized * objective.weight
                    total_weight += objective.weight
                except Exception as e:
                    logger.warning(f"Error evaluating objective {objective.name}: {e}")

            # Calculate fitness (penalize constraint violations)
            if total_weight > 0:
                fitness = weighted_sum / total_weight
            else:
                fitness = 0.0

            # Apply constraint penalties
            penalty = constraint_violations * sum(c.penalty for c in constraints)
            fitness = max(0.0, fitness - penalty)

            fitness_scores.append(fitness)

        return fitness_scores

    def _select_parents(
        self,
        population: List[Dict[str, Any]],
        fitness_scores: List[float],
    ) -> List[Dict[str, Any]]:
        """
        Select parents for reproduction using tournament selection.

        Args:
            population: List of solutions
            fitness_scores: List of fitness scores

        Returns:
            List of selected parents
        """
        tournament_size = max(2, int(0.1 * len(population)))
        parents = []

        for _ in range(len(population)):
            # Select tournament participants
            tournament_indices = random.sample(range(len(population)), tournament_size)

            # Find winner (highest fitness)
            winner_idx = max(tournament_indices, key=lambda i: fitness_scores[i])

            parents.append(population[winner_idx])

        return parents

    def _create_offspring(
        self,
        parents: List[Dict[str, Any]],
        solution_space: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Create offspring through crossover and mutation.

        Args:
            parents: List of parent solutions
            solution_space: List of all possible solutions

        Returns:
            List of offspring solutions
        """
        offspring = []

        # Create pairs of parents
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                parent1 = parents[i]
                parent2 = parents[i + 1]

                # Perform crossover with probability
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                # Perform mutation with probability
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1, solution_space)

                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2, solution_space)

                offspring.extend([child1, child2])
            else:
                # Odd number of parents, just add the last one
                offspring.append(parents[i].copy())

        return offspring

    def _crossover(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Perform crossover between two parent solutions.

        Args:
            parent1: First parent solution
            parent2: Second parent solution

        Returns:
            Tuple of two child solutions
        """
        # Simple crossover: randomly select keys from each parent
        child1 = {}
        child2 = {}

        all_keys = set(parent1.keys()) | set(parent2.keys())

        for key in all_keys:
            if key in parent1 and key in parent2:
                # Both parents have this key
                if random.random() < 0.5:
                    child1[key] = parent1[key]
                    child2[key] = parent2[key]
                else:
                    child1[key] = parent2[key]
                    child2[key] = parent1[key]
            elif key in parent1:
                # Only parent1 has this key
                child1[key] = parent1[key]
                child2[key] = parent1[key]
            else:
                # Only parent2 has this key
                child1[key] = parent2[key]
                child2[key] = parent2[key]

        return child1, child2

    def _mutate(
        self,
        solution: Dict[str, Any],
        solution_space: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Mutate a solution.

        Args:
            solution: Solution to mutate
            solution_space: List of all possible solutions

        Returns:
            Mutated solution
        """
        # Simple mutation: replace with random solution from solution space
        if solution_space:
            random_solution = random.choice(solution_space)

            # Select a random key to mutate
            if solution and random_solution:
                keys = list(solution.keys())
                if keys:
                    key_to_mutate = random.choice(keys)
                    if key_to_mutate in random_solution:
                        mutated = solution.copy()
                        mutated[key_to_mutate] = random_solution[key_to_mutate]
                        return mutated

        return solution

    def rank_solutions(
        self,
        solutions: List[Dict[str, Any]],
        objectives: List[Objective],
        constraints: List[Constraint],
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank solutions by their fitness scores.

        Args:
            solutions: List of solutions to rank
            objectives: List of objectives
            constraints: List of constraints

        Returns:
            List of (solution, fitness) tuples, sorted by fitness
        """
        # Evaluate solutions
        fitness_scores = self._evaluate_population(solutions, objectives, constraints)

        # Create (solution, fitness) pairs
        ranked = list(zip(solutions, fitness_scores))

        # Sort by fitness (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked
