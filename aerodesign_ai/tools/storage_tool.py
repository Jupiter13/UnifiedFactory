"""Design storage and retrieval tools."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import json

from aerodesign_ai.tools.base import BaseTool, ToolResult
from aerodesign_ai.models.schemas import DesignState, DesignOutput, BOMItem, ComplianceReport


class DesignStorage:
    """In-memory design storage (stub for database)."""

    _instance: Optional["DesignStorage"] = None
    _designs: Dict[str, Dict] = {}

    def __new__(cls) -> "DesignStorage":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def store(self, state: DesignState, design_id: Optional[str] = None) -> str:
        """Store a design state.

        Args:
            state: DesignState to store
            design_id: Optional design ID (generates if not provided)

        Returns:
            Design ID
        """
        if design_id is None:
            design_id = f"DESIGN-{uuid.uuid4().hex[:8].upper()}"

        state.version_id = design_id
        state.timestamp = datetime.utcnow()

        self._designs[design_id] = {
            "id": design_id,
            "state": state.model_dump(),
            "created_at": state.timestamp.isoformat(),
        }

        return design_id

    def retrieve(self, design_id: str) -> Optional[DesignState]:
        """Retrieve a design by ID.

        Args:
            design_id: Design identifier

        Returns:
            DesignState or None if not found
        """
        design = self._designs.get(design_id)
        if design is None:
            return None

        state_data = design["state"]
        return DesignState(**state_data)

    def list_all(self) -> List[str]:
        """List all design IDs."""
        return list(self._designs.keys())

    def delete(self, design_id: str) -> bool:
        """Delete a design."""
        if design_id in self._designs:
            del self._designs[design_id]
            return True
        return False


class StoreDesign(BaseTool[str]):
    """Store completed design to database."""

    name = "store_design"
    description = "Persist design state and metadata to storage."

    def __init__(self):
        self._storage = DesignStorage()

    def call(
        self,
        payload_tons: float,
        material: str,
        engine: str,
        geometry: Dict[str, Any],
        optimization_metrics: Dict[str, float],
        compliance_report: ComplianceReport,
        bom: List[BOMItem],
        cad_file_path: str,
        user_id: str = "anonymous",
        design_id: Optional[str] = None,
        optional_constraints: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult[str]:
        """Store a design.

        Args:
            payload_tons: Payload capacity in tonnes
            material: Material type
            engine: Engine type
            geometry: Aircraft geometry
            optimization_metrics: Performance metrics
            compliance_report: Compliance evaluation
            bom: Bill of materials
            cad_file_path: CAD file path
            user_id: User identifier
            design_id: Optional design ID
            optional_constraints: Optional constraints

        Returns:
            ToolResult containing design_id
        """
        try:
            state = DesignState(
                payload_tons=payload_tons,
                material=material,
                engine=engine,
                geometry=geometry,
                optimization_metrics=optimization_metrics,
                compliance_report=compliance_report,
                bom=bom,
                cad_file_path=cad_file_path,
                optional_constraints=optional_constraints,
                user_id=user_id,
            )

            stored_id = self._storage.store(state, design_id)

            return ToolResult.ok(
                stored_id,
                {
                    "user_id": user_id,
                    "compliance_passed": compliance_report.passed,
                    "total_bom_items": len(bom),
                }
            )

        except Exception as e:
            return ToolResult.err(f"Storage error: {str(e)}")

    def validate_inputs(self, geometry: Dict[str, Any], **kwargs) -> bool:
        """Validate required inputs."""
        return isinstance(geometry, dict) and len(geometry) > 0


class RetrieveDesign(BaseTool[DesignState]):
    """Retrieve stored design."""

    name = "retrieve_design"
    description = "Load a previous design from storage."

    def __init__(self):
        self._storage = DesignStorage()

    def call(self, design_id: str, **kwargs) -> ToolResult[DesignState]:
        """Retrieve a design.

        Args:
            design_id: Design identifier

        Returns:
            ToolResult containing DesignState
        """
        try:
            state = self._storage.retrieve(design_id)
            if state is None:
                return ToolResult.err(
                    f"Design '{design_id}' not found",
                    {"available_designs": self._storage.list_all()}
                )

            return ToolResult.ok(state)

        except Exception as e:
            return ToolResult.err(f"Retrieval error: {str(e)}")

    def validate_inputs(self, design_id: str, **kwargs) -> bool:
        """Validate design_id."""
        return isinstance(design_id, str) and len(design_id) > 0
