"""Optimization Tool.

Multi-objective evolutionary optimization.
"""

import random
from typing import Optional

from ..models import DesignParams, SimulationResult, CostEstimate


class OptimizationTool:
    """Tool for multi-objective design optimization."""

    DEFAULT_BOUNDS = {
        "wing_area": (5.0, 100.0),
        "aspect_ratio": (5.0, 30.0),
        "sweep": (0.0, 40.0),
        "fuselage_length": (5.0, 30.0),
        "tail_area": (2.0, 20.0),
        "max_takeoff_weight": (500.0, 50000.0),
        "empty_weight": (200.0, 20000.0),
        "wing_thickness_ratio": (0.05, 0.3),
        "taper_ratio": (0.3, 1.5),
    }

    def __init__(
        self,
        max_iterations: int = 50,
        population_size: int = 20,
        mutation_rate: float = 0.1,
    ):
        """Initialize the optimizer.

        Args:
            max_iterations: Maximum optimization iterations.
            population_size: GA population size.
            mutation_rate: Mutation probability.
        """
        self.max_iterations = max_iterations
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.bounds = self.DEFAULT_BOUNDS.copy()

    def invoke(
        self,
        design_params: DesignParams,
        simulation: Optional[SimulationResult] = None,
        cost_estimate: Optional[CostEstimate] = None,
    ) -> DesignParams:
        """Optimize design parameters.

        Args:
            design_params: Current design parameters.
            simulation: Simulation results.
            cost_estimate: Cost estimate.

        Returns:
            Optimized DesignParams.
        """
        # Run simplified evolutionary optimization
        best_params = design_params
        best_score = self._evaluate(design_params, simulation, cost_estimate)

        for _ in range(self.max_iterations):
            # Generate mutant
            mutant = self._mutate(best_params)
            mutant_score = self._evaluate(mutant, simulation, cost_estimate)

            if mutant_score > best_score:
                best_params = mutant
                best_score = mutant_score

        return best_params

    def _mutate(self, design_params: DesignParams) -> DesignParams:
        """Create a mutant design by applying random changes.

        Args:
            design_params: Original design parameters.

        Returns:
            Mutated DesignParams.
        """
        params = design_params.model_dump()

        for key, bounds in self.bounds.items():
            if random.random() < self.mutation_rate:
                min_val, max_val = bounds
                params[key] = random.uniform(min_val, max_val)

        return DesignParams(**params)

    def _evaluate(
        self,
        design_params: DesignParams,
        simulation: Optional[SimulationResult],
        cost_estimate: Optional[CostEstimate],
    ) -> float:
        """Evaluate design fitness.

        Args:
            design_params: Design parameters.
            simulation: Simulation results.
            cost_estimate: Cost estimate.

        Returns:
            Fitness score (higher is better).
        """
        score = 1.0

        if simulation:
            # Reward high safety factor
            score *= simulation.fea.safety_factor / 2.0
            # Reward good range
            score *= min(simulation.cfd.range / 2000.0, 2.0)
            # Reward reasonable max speed
            score *= min(simulation.cfd.max_speed / 200.0, 1.5)

        if cost_estimate:
            # Reward lower cost
            score /= max(cost_estimate.total_cost / 100000.0, 0.1)

        # Penalize invalid designs
        if design_params.is_invalid():
            score *= 0.1

        return score

    def set_bounds(self, param_name: str, min_val: float, max_val: float) -> None:
        """Set optimization bounds for a parameter.

        Args:
            param_name: Parameter name.
            min_val: Minimum value.
            max_val: Maximum value.
        """
        if param_name in self.bounds:
            self.bounds[param_name] = (min_val, max_val)