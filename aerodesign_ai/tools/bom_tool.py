"""Bill of Materials generation tool."""

from typing import Any, Dict, List, Optional
import math

from aerodesign_ai.tools.base import BaseTool, ToolResult
from aerodesign_ai.models.schemas import BOMItem


class BOMGenerator:
    """Generate bill of materials from aircraft geometry and specifications."""

    PART_PRICES = {
        "wing_panel": 1500,
        "fuselage_section": 2000,
        "empennage_panel": 800,
        "engine_mount": 1200,
        "landing_gear": 3500,
        "avionics_package": 5000,
        "fuel_system": 2500,
        "control_system": 1800,
        "electrical_system": 1500,
        "interior": 2000,
    }

    def generate(
        self,
        geometry: Dict[str, Any],
        material_cost: float,
        material_density: float,
        engine_cost: float,
    ) -> List[BOMItem]:
        """Generate BOM items.

        Args:
            geometry: Aircraft geometry dictionary
            material_cost: Cost per kg of material
            material_density: Material density in kg/m³
            engine_cost: Engine cost

        Returns:
            List of BOMItem objects
        """
        items = []

        # Wing assembly
        wing_area = geometry.get("wing_area_m2", 20)
        wing_span = geometry.get("wing_span_m", 10)
        wing_volume = wing_area * 0.15  # Approximate volume
        wing_weight = wing_volume * material_density
        items.append(BOMItem(
            part_name="Wing Assembly",
            quantity=2,
            unit_cost_usd=wing_weight * material_cost + self.PART_PRICES["wing_panel"],
            material=geometry.get("material", "Aluminum"),
            dimensions={"span_m": wing_span / 2, "area_m2": wing_area / 2, "thickness_m": 0.15},
            weight_kg=wing_weight,
            description="Main wing panels with embedded systems",
        ))

        # Fuselage sections
        fuselage_length = geometry.get("fuselage_length_m", 10)
        fuselage_diameter = geometry.get("fuselage_diameter_m", 1.5)
        fuselage_surface = math.pi * fuselage_diameter * fuselage_length
        fuselage_volume = fuselage_surface * 0.02
        fuselage_weight = fuselage_volume * material_density
        num_sections = max(3, int(fuselage_length / 2))
        items.append(BOMItem(
            part_name="Fuselage Sections",
            quantity=num_sections,
            unit_cost_usd=fuselage_weight / num_sections * material_cost + self.PART_PRICES["fuselage_section"],
            material=geometry.get("material", "Aluminum"),
            dimensions={"length_m": fuselage_length / num_sections, "diameter_m": fuselage_diameter},
            weight_kg=fuselage_weight,
            description=f"Fuselage sections (Qty: {num_sections})",
        ))

        # Tail assembly
        tail_span = geometry.get("tail_span_m", 3)
        tail_area = geometry.get("tail_area_m2", 5)
        tail_volume = tail_area * 0.1
        tail_weight = tail_volume * material_density
        items.append(BOMItem(
            part_name="Tail Assembly",
            quantity=1,
            unit_cost_usd=tail_weight * material_cost + self.PART_PRICES["empennage_panel"],
            material=geometry.get("material", "Aluminum"),
            dimensions={"span_m": tail_span, "area_m2": tail_area},
            weight_kg=tail_weight,
            description="Horizontal and vertical stabilizer assembly",
        ))

        # Engine nacelle
        items.append(BOMItem(
            part_name="Engine Nacelle",
            quantity=2,
            unit_cost_usd=500 + self.PART_PRICES["engine_mount"],
            material="Aluminum",
            dimensions={"length_m": 1.5, "diameter_m": 0.8},
            weight_kg=50,
            description="Engine nacelle with cooling system",
        ))

        # Engine
        items.append(BOMItem(
            part_name=" Propulsion Engine",
            quantity=1,
            unit_cost_usd=engine_cost,
            description="Main propulsion engine as specified",
        ))

        # Landing gear
        items.append(BOMItem(
            part_name="Landing Gear Assembly",
            quantity=1,
            unit_cost_usd=self.PART_PRICES["landing_gear"],
            material="Steel 4130",
            weight_kg=80,
            description="Retractable tricycle landing gear",
        ))

        # Avionics
        items.append(BOMItem(
            part_name="Avionics Package",
            quantity=1,
            unit_cost_usd=self.PART_PRICES["avionics_package"],
            description="Complete avionics suite including autopilot",
        ))

        # Fuel system
        items.append(BOMItem(
            part_name="Fuel System",
            quantity=1,
            unit_cost_usd=self.PART_PRICES["fuel_system"],
            weight_kg=geometry.get("estimated_fuel_weight_kg", 500),
            description="Fuel tanks, lines, and management system",
        ))

        # Control system
        items.append(BOMItem(
            part_name="Flight Control System",
            quantity=1,
            unit_cost_usd=self.PART_PRICES["control_system"],
            description="Hydraulic and mechanical flight controls",
        ))

        # Electrical system
        items.append(BOMItem(
            part_name="Electrical System",
            quantity=1,
            unit_cost_usd=self.PART_PRICES["electrical_system"],
            description="Power generation, distribution, and lighting",
        ))

        return items


class GenerateBOM(BaseTool[List[BOMItem]]):
    """Generate bill of materials for aircraft design."""

    name = "generate_bom"
    description = "Generate cost and component list (BOM) from aircraft geometry and specifications."

    def __init__(self):
        self._generator = BOMGenerator()

    def call(
        self,
        geometry: Dict[str, Any],
        material_cost: float,
        material_density: float,
        engine_cost: float,
        **kwargs
    ) -> ToolResult[List[BOMItem]]:
        """Generate BOM.

        Args:
            geometry: Aircraft geometry dictionary
            material_cost: Material cost per kg
            material_density: Material density in kg/m³
            engine_cost: Engine cost in USD

        Returns:
            ToolResult containing list of BOMItem
        """
        try:
            items = self._generator.generate(
                geometry=geometry,
                material_cost=material_cost,
                material_density=material_density,
                engine_cost=engine_cost,
            )

            total_cost = sum(item.total_cost_usd for item in items)

            return ToolResult.ok(
                items,
                {
                    "item_count": len(items),
                    "total_cost_usd": total_cost,
                    "unit_count": sum(item.quantity for item in items),
                }
            )

        except Exception as e:
            return ToolResult.err(f"BOM generation error: {str(e)}")

    def validate_inputs(self, geometry: Dict[str, Any], **kwargs) -> bool:
        """Validate geometry input."""
        return isinstance(geometry, dict)
