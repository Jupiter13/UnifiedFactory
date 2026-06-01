"""Version Control Tool.

Stores design snapshots to PostgreSQL + S3.
"""

import json
from datetime import datetime
from typing import List, Optional

from ..models import DesignState, DesignParams


class VersionControlTool:
    """Tool for storing and retrieving design versions."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        s3_bucket: Optional[str] = None,
    ):
        """Initialize the version control tool.

        Args:
            db_url: PostgreSQL connection URL.
            s3_bucket: S3 bucket name for CAD files.
        """
        self.db_url = db_url
        self.s3_bucket = s3_bucket
        self._history: List[DesignState] = []

    def invoke(self, design_state: DesignState) -> None:
        """Store a design state snapshot.

        Args:
            design_state: Design state to store.
        """
        # In production, store to PostgreSQL + S3
        self._history.append(design_state)

    def get_history(self, limit: Optional[int] = None) -> List[DesignState]:
        """Retrieve design history.

        Args:
            limit: Maximum number of states to return.

        Returns:
            List of DesignState objects.
        """
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def get_by_id(self, state_id: int) -> Optional[DesignState]:
        """Get a specific design state by index.

        Args:
            state_id: State index.

        Returns:
            DesignState or None if not found.
        """
        if 0 <= state_id < len(self._history):
            return self._history[state_id]
        return None

    def export_state(self, design_state: DesignState) -> str:
        """Export design state as JSON string.

        Args:
            design_state: Design state to export.

        Returns:
            JSON string representation.
        """
        return design_state.model_dump_json()

    def import_state(self, json_str: str) -> DesignState:
        """Import design state from JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            DesignState object.
        """
        return DesignState.model_validate_json(json_str)

    def clear_history(self) -> None:
        """Clear all stored design history."""
        self._history.clear()


class VersionControlError(Exception):
    """Error in version control operations."""

    pass