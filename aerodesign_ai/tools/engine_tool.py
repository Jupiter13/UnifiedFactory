"""Engine specifications fetching tool."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from aerodesign_ai.tools.base import BaseTool, ToolError, ToolResult
from aerodesign_ai.models.schemas import EngineSpecs

CONFIG_DIR = Path(__file__).parent.parent / "config"


class EngineDatabase:
    """In-memory engine database loaded from JSON config."""

    _instance: Optional["EngineDatabase"] = None
    _engines: Dict[str, Dict] = {}

    def __new__(cls) -> "EngineDatabase":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_engines()
        return cls._instance

    def _load_engines(self) -> None:
        """Load engines from JSON configuration."""
        config_path = CONFIG_DIR / "engine_library.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
                for eng in data.get("engines", []):
                    self._engines[eng["id"]] = eng
                    self._engines[eng["name"].lower().replace(" ", "_")] = eng

    def get(self, engine_id: str) -> Optional[Dict]:
        """Get engine by ID or name."""
        return self._engines.get(engine_id)

    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get engine by name (case-insensitive)."""
        normalized = name.lower().replace(" ", "_")
        for key, eng in self._engines.items():
            if eng["name"].lower() == name.lower() or key == normalized:
                return eng
        return None

    def list_all(self) -> List[Dict]:
        """List all available engines."""
        seen = set()
        engines = []
        for eng in self._engines.values():
            if eng["id"] not in seen:
                seen.add(eng["id"])
                engines.append(eng)
        return engines


class FetchEngineSpecs(BaseTool[EngineSpecs]):
    """Fetch engine performance specifications."""

    name = "fetch_engine_specs"
    description = "Retrieve engine performance data including thrust, fuel flow, weight, and cost."

    def __init__(self):
        self._db = EngineDatabase()

    def call(self, engine: str, **kwargs) -> ToolResult[EngineSpecs]:
        """Fetch engine specifications.

        Args:
            engine: Engine name or ID

        Returns:
            ToolResult containing EngineSpecs
        """
        try:
            eng_data = self._db.get_by_name(engine)
            if eng_data is None:
                return ToolResult.err(
                    f"Engine '{engine}' not found in library",
                    {"available_engines": [e["id"] for e in self._db.list_all()]}
                )

            specs = EngineSpecs(
                name=eng_data["name"],
                thrust_newtons=eng_data["thrust_newtons"],
                fuel_flow_kg_s=eng_data["fuel_flow_kg_s"],
                weight_kg=eng_data["weight_kg"],
                cost_usd=eng_data["cost_usd"],
                specific_fuel_consumption=eng_data.get("specific_fuel_consumption"),
                max_altitude_m=eng_data.get("max_altitude_m"),
            )

            return ToolResult.ok(specs, {"engine_id": eng_data["id"]})

        except Exception as e:
            return ToolResult.err(f"Error fetching engine: {str(e)}")

    def validate_inputs(self, engine: str, **kwargs) -> bool:
        """Validate engine input."""
        return isinstance(engine, str) and len(engine) > 0
