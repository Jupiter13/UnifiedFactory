"""Material properties fetching tool."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from aerodesign_ai.tools.base import BaseTool, ToolError, ToolResult
from aerodesign_ai.models.schemas import MaterialProps

CONFIG_DIR = Path(__file__).parent.parent / "config"


class MaterialDatabase:
    """In-memory material database loaded from JSON config."""

    _instance: Optional["MaterialDatabase"] = None
    _materials: Dict[str, Dict] = {}

    def __new__(cls) -> "MaterialDatabase":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_materials()
        return cls._instance

    def _load_materials(self) -> None:
        """Load materials from JSON configuration."""
        config_path = CONFIG_DIR / "material_library.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
                for mat in data.get("materials", []):
                    self._materials[mat["id"]] = mat
                    self._materials[mat["name"].lower().replace(" ", "_")] = mat

    def get(self, material_id: str) -> Optional[Dict]:
        """Get material by ID or name."""
        return self._materials.get(material_id)

    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get material by name (case-insensitive)."""
        normalized = name.lower().replace(" ", "_")
        for key, mat in self._materials.items():
            if mat["name"].lower() == name.lower() or key == normalized:
                return mat
        return None

    def list_all(self) -> List[Dict]:
        """List all available materials."""
        seen = set()
        materials = []
        for mat in self._materials.values():
            if mat["id"] not in seen:
                seen.add(mat["id"])
                materials.append(mat)
        return materials


class FetchMaterialProps(BaseTool[MaterialProps]):
    """Fetch material properties from the material library."""

    name = "fetch_material_props"
    description = "Retrieve material properties including density, tensile strength, cost per kg, and manufacturability score."

    def __init__(self):
        self._db = MaterialDatabase()

    def call(self, material: str, **kwargs) -> ToolResult[MaterialProps]:
        """Fetch material properties.

        Args:
            material: Material name or ID

        Returns:
            ToolResult containing MaterialProps
        """
        try:
            mat_data = self._db.get_by_name(material)
            if mat_data is None:
                return ToolResult.err(
                    f"Material '{material}' not found in library",
                    {"available_materials": [m["id"] for m in self._db.list_all()]}
                )

            props = MaterialProps(
                name=mat_data["name"],
                density_kg_m3=mat_data["density_kg_m3"],
                tensile_strength_pa=mat_data["tensile_strength_pa"],
                cost_per_kg=mat_data["cost_per_kg"],
                manufacturability_score=mat_data["manufacturability_score"],
                youngs_modulus_pa=mat_data.get("youngs_modulus pa"),
                yield_strength_pa=mat_data.get("yield_strength_pa"),
            )

            return ToolResult.ok(props, {"material_id": mat_data["id"]})

        except Exception as e:
            return ToolResult.err(f"Error fetching material: {str(e)}")

    def validate_inputs(self, material: str, **kwargs) -> bool:
        """Validate material input."""
        return isinstance(material, str) and len(material) > 0
