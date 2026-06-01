"""FEA Solver Tool.

Structural stress and weight analysis using Calculix wrapper.
"""

import hashlib
from typing import Optional

from ..models import DesignParams, MaterialProperties, FEASimulationResult


class FEASolverTool:
    """Tool for FEA simulation."""

    def __init__(self, enable_cache: bool = True):
        """Initialize the FEA solver.

        Args:
            enable_cache: Whether to cache simulation results.
        """
        self.enable_cache = enable_cache
        self._cache = {}

    def invoke(
        self,
        design_params: DesignParams,
        material_props: Optional[MaterialProperties] = None,
    ) -> FEASimulationResult:
        """Run FEA simulation.

        Args:
            design_params: Design parameters.
            material_props: Optional material properties.

        Returns:
            FEASimulationResult with structural analysis data.
        """
        cache_key = self._generate_cache_key(design_params, material_props)
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        result = self._run_analysis(design_params, material_props)

        if self.enable_cache:
            self._cache[cache_key] = result

        return result

    def _generate_cache_key(
        self,
        design_params: DesignParams,
        material_props: Optional[MaterialProperties],
    ) -> str:
        """Generate cache key for analysis results."""
        key_data = (
            f"{design_params.wing_area}_{design_params.max_takeoff_weight}_"
            f"{design_params.fuselage_length}_{design_params.empty_weight}_"
            f"{material_props.family if material_props else 'default'}"
        )
        return hashlib.md5(key_data.encode()).hexdigest()

    def _run_analysis(
        self,
        design_params: DesignParams,
        material_props: Optional[MaterialProperties],
    ) -> FEASimulationResult:
        """Run simplified FEA analysis.

        Uses simplified structural calculations based on design parameters.
        In production, this would call Calculix or a higher-fidelity solver.
        """
        # Get material properties or use defaults
        if material_props:
            modulus = material_props.modulus * 1e9  # GPa to Pa
            density = material_props.density
            fatigue_limit = material_props.fatigue_limit * 1e6  # MPa to Pa
        else:
            # Default aluminum properties
            modulus = 70e9
            density = 2700
            fatigue_limit = 150e6

        # Structural analysis
        wing_area = design_params.wing_area
        max_weight = design_params.max_takeoff_weight
        empty_weight = design_params.empty_weight

        # Compute wing loading
        wing_loading = max_weight * 9.81 / wing_area  # N/m²

        # Simplified stress calculation
        # Assuming wing as a cantilever beam
        wing_span = (wing_area * design_params.aspect_ratio) ** 0.5
        root_moment = wing_loading * wing_area * wing_span / 6  # N·m
        section_modulus = wing_area * wing_span / 20  # m³ (simplified)

        if section_modulus > 0:
            max_stress = root_moment / section_modulus  # Pa
        else:
            max_stress = wing_loading * 1e3  # Fallback

        # Safety factor
        safety_factor = fatigue_limit / max_stress if max_stress > 0 else 1.0

        # Weight estimation (simplified)
        # Based on wing area and material density
        structural_weight = wing_area * 20 * (density / 2700)  # kg
        fea_weight = max(empty_weight, structural_weight)

        return FEASimulationResult(
            max_stress=max_stress / 1e6,  # Convert to MPa
            safety_factor=safety_factor,
            weight=fea_weight,
        )

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()