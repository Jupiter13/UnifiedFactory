"""Compliance Checker Tool.

FAA/ICAO regulatory compliance checks.
"""

from typing import Optional, List, Union

from ..models import DesignParams, SimulationResult, CostEstimate, ComplianceReport, CFDSimulationResult, FEASimulationResult


class ComplianceCheckerTool:
    """Tool for checking regulatory compliance."""

    # Regulatory thresholds
    MIN_SAFETY_FACTOR = 1.5
    MAX_COST_PER_KG = 500.0  # USD/kg
    MIN_RANGE_KM = 500.0
    MIN_MAX_SPEED_MPS = 100.0
    MIN_PAYLOAD_FRACTION = 0.1  # 10% of max takeoff weight

    def __init__(self, regulatory_version: str = "2024"):
        """Initialize the compliance checker.

        Args:
            regulatory_version: Regulatory version to use.
        """
        self.regulatory_version = regulatory_version

    def invoke(
        self,
        design_params: Union[DesignParams, dict],
        simulation: Optional[Union[SimulationResult, dict]] = None,
        cost_estimate: Optional[Union[CostEstimate, dict]] = None,
    ) -> ComplianceReport:
        """Check compliance with FAA/ICAO regulations.

        Args:
            design_params: Design parameters.
            simulation: Simulation results (dict or SimulationResult).
            cost_estimate: Cost estimate (dict or CostEstimate).

        Returns:
            ComplianceReport with pass/fail status and issues.
        """
        # Convert dict inputs to proper types
        if isinstance(design_params, dict):
            design_params = DesignParams(**design_params)

        issues: List[str] = []

        # Handle simulation (may be dict or SimulationResult)
        if simulation:
            sim_cfd = None
            sim_fea = None

            if isinstance(simulation, dict):
                sim_cfd = simulation.get("cfd")
                sim_fea = simulation.get("fea")
            else:
                sim_cfd = simulation.cfd
                sim_fea = simulation.fea

            # Check safety factor
            if sim_fea and hasattr(sim_fea, "safety_factor"):
                if sim_fea.safety_factor < self.MIN_SAFETY_FACTOR:
                    issues.append(
                        f"Safety factor {sim_fea.safety_factor:.2f} below "
                        f"minimum {self.MIN_SAFETY_FACTOR}"
                    )

            # Check range
            if sim_cfd and hasattr(sim_cfd, "range"):
                if sim_cfd.range < self.MIN_RANGE_KM:
                    issues.append(
                        f"Range {sim_cfd.range:.0f} km below minimum "
                        f"{self.MIN_RANGE_KM} km"
                    )

            # Check max speed
            if sim_cfd and hasattr(sim_cfd, "max_speed"):
                if sim_cfd.max_speed < self.MIN_MAX_SPEED_MPS:
                    issues.append(
                        f"Max speed {sim_cfd.max_speed:.0f} m/s below minimum "
                        f"{self.MIN_MAX_SPEED_MPS} m/s"
                    )

        # Check cost
        if cost_estimate:
            cost_total = cost_estimate.total_cost if hasattr(cost_estimate, "total_cost") else cost_estimate.get("total_cost", 0)
            cost_per_kg = cost_total / design_params.max_takeoff_weight
            if cost_per_kg > self.MAX_COST_PER_KG:
                issues.append(
                    f"Cost per kg ${cost_per_kg:.0f} exceeds maximum "
                    f"${self.MAX_COST_PER_KG}"
                )

        # Check payload fraction
        payload_fraction = design_params.empty_weight / design_params.max_takeoff_weight
        if payload_fraction > (1 - self.MIN_PAYLOAD_FRACTION):
            issues.append(
                f"Payload fraction {payload_fraction:.2%} too low "
                f"(min {self.MIN_PAYLOAD_FRACTION:.0%})"
            )

        # Check structural parameters
        if design_params.wing_area < 5.0:
            issues.append(f"Wing area {design_params.wing_area:.1f} m² too small")

        if design_params.sweep > 40.0:
            issues.append(f"Wing sweep {design_params.sweep}° exceeds 40° limit")

        passed = len(issues) == 0

        return ComplianceReport(passed=passed, issues=issues)

    def get_regulatory_text(self, regulation: str) -> str:
        """Get regulatory text from vector store.

        Args:
            regulation: Regulation identifier.

        Returns:
            Regulatory text snippet.
        """
        # In production, this would query the FAISS vector store
        return f"FAR {regulation} ({self.regulatory_version})"