"""CFD Solver Tool.

Reduced-order lift/drag estimation using XFOIL + surrogate model.
"""

import hashlib
import math
from typing import Optional

from ..models import DesignParams, EngineSpecs, CFDSimulationResult


class CFDSolverTool:
    """Tool for CFD simulation using reduced-order methods."""

    def __init__(self, enable_cache: bool = True):
        """Initialize the CFD solver.

        Args:
            enable_cache: Whether to cache simulation results.
        """
        self.enable_cache = enable_cache
        self._cache = {}

    def invoke(
        self,
        design_params: DesignParams,
        engine_specs: Optional[EngineSpecs] = None,
    ) -> CFDSimulationResult:
        """Run CFD simulation.

        Args:
            design_params: Design parameters.
            engine_specs: Optional engine specifications.

        Returns:
            CFDSimulationResult with aerodynamic data.
        """
        cache_key = self._generate_cache_key(design_params, engine_specs)
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        result = self._run_simulation(design_params, engine_specs)

        if self.enable_cache:
            self._cache[cache_key] = result

        return result

    def _generate_cache_key(
        self,
        design_params: DesignParams,
        engine_specs: Optional[EngineSpecs],
    ) -> str:
        """Generate cache key for simulation results."""
        key_data = (
            f"{design_params.wing_area}_{design_params.aspect_ratio}_"
            f"{design_params.sweep}_{design_params.fuselage_length}_"
            f"{engine_specs.family if engine_specs else 'none'}"
        )
        return hashlib.md5(key_data.encode()).hexdigest()

    def _run_simulation(
        self,
        design_params: DesignParams,
        engine_specs: Optional[EngineSpecs],
    ) -> CFDSimulationResult:
        """Run reduced-order CFD simulation.

        Uses simplified aerodynamic calculations based on design parameters.
        In production, this would call XFOIL or a higher-fidelity solver.
        """
        # Simplified aerodynamic calculations
        wing_area = design_params.wing_area
        aspect_ratio = design_params.aspect_ratio
        sweep = design_params.sweep
        empty_weight = design_params.empty_weight

        # Air density at cruise altitude (10km)
        rho = 0.4125  # kg/m³

        # Compute lift coefficient (simplified)
        # Cl = 2 * pi * alpha for thin airfoil, modified by sweep
        sweep_rad = math.radians(sweep)
        cl_max = 1.5 * math.cos(sweep_rad)  # Maximum CL adjusted for sweep

        # Compute drag coefficient (simplified)
        # Cd = Cd0 + Cl² / (pi * AR * e)
        cd0 = 0.02  # Zero-lift drag coefficient
        oswald_efficiency = 0.85
        cl = 0.5 * cl_max  # Design lift coefficient
        cd = cd0 + cl**2 / (math.pi * aspect_ratio * oswald_efficiency)

        # Dynamic pressure at cruise
        v_cruise = 150.0  # m/s (~540 km/h)
        q = 0.5 * rho * v_cruise**2

        # Lift and drag forces
        lift = cl * q * wing_area
        drag = cd * q * wing_area

        # Maximum speed (simplified)
        max_speed = v_cruise * 1.3

        # Range calculation (Breguet formula, simplified)
        # In production, use proper fuel consumption model
        if engine_specs:
            thrust = engine_specs.thrust * 1000  # Convert to N
            sfc = engine_specs.fuel_consumption / 3600  # kg/Ns
            l_d_ratio = lift / drag if drag > 0 else 10.0
            max_range = l_d_ratio * math.log(1 + (thrust / (empty_weight * 9.81)) / sfc) * 1000
        else:
            # Default range calculation
            max_range = (lift / drag) * 500  # km

        return CFDSimulationResult(
            lift=lift,
            drag=drag,
            max_speed=max_speed,
            range=max_range if max_range > 0 else 1000.0,
            weight=empty_weight,
        )

    def clear_cache(self) -> None:
        """Clear the simulation cache."""
        self._cache.clear()