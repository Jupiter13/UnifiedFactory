"""Base tool class for EDU_CENTRE AI."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """Response from a tool execution."""

    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None

    def __repr__(self) -> str:
        if self.success:
            return f"ToolResponse(success=True, data={self.data})"
        return f"ToolResponse(success=False, error={self.error})"


class BaseTool:
    """Base class for all tools in the agent."""

    name: str = "base_tool"
    description: str = "Base tool"

    def call(self, **kwargs) -> ToolResponse:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResponse with success status and data or error
        """
        raise NotImplementedError(f"{self.name} must implement call method")

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None