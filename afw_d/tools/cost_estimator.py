"""Cost Estimator Tool.

Preliminary cost estimation using cost databases.
"""

from typing import Optional

from ..models import DesignParams, MaterialProperties, EngineSpecs, CostEstimate


class CostEstimatorTool:
    """Tool for estimating aircraft design costs."""

    # Default cost factors
    MANUFACTURING_COST_PER_KG = 50.0  # USD/kg
    OVERHEAD_FACTOR = 1.3

    def __init__(self, cost_factor_multiplier: float = 1.0):
        """Initialize the cost estimator.

        Args:
            cost_factor_multiplier: Multiplier for all cost factors.
        """
        self.cost_factor_multiplier = cost_factor_multiplier

    def invoke(
        self,
        design_params: DesignParams,
        material_props: Optional[MaterialProperties] = None,
        engine_specs: Optional[EngineSpecs] = None,
    ) -> CostEstimate:
        """Estimate design costs.

        Args:
            design_params: Design parameters.
            material_props: Material properties.
            engine_specs: Engine specifications.

        Returns:
            CostEstimate with cost breakdown.
        """
        # Calculate material cost
        if material_props:
            empty_weight = design_params.empty_weight
            material_cost = empty_weight * material_props.cost_per_kg
        else:
            # Default cost for unknown material
            material_cost = design_params.empty_weight * 10.0

        # Add engine cost
        if engine_specs:
            material_cost += engine_specs.cost

        # Manufacturing cost (simplified)
        manufacturing_cost = (
            design_params.empty_weight
            * self.MANUFACTURING_COST_PER_KG
            * self.cost_factor_multiplier
        )

        # Total cost with overhead
        total_cost = (material_cost + manufacturing_cost) * self.OVERHEAD_FACTOR

        return CostEstimate(
            material_cost=round(material_cost, 2),
            manufacturing_cost=round(manufacturing_cost, 2),
            total_cost=round(total_cost, 2),
        )

    def set_cost_factor(self, multiplier: float) -> None:
        """Set the cost factor multiplier.

        Args:
            multiplier: New cost factor multiplier.
        """
        if multiplier <= 0:
            raise ValueError("Cost factor multiplier must be positive")
        self.cost_factor_multiplier = multiplier