"""Base tool classes for AeroDesign-AI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ToolError(Exception):
    """Base exception for tool errors."""

    def __init__(self, message: str, tool_name: str = "unknown"):
        self.message = message
        self.tool_name = tool_name
        super().__init__(f"[{tool_name}] {message}")


@dataclass
class ToolResult(Generic[T]):
    """Result container for tool execution."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: T, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult[T]":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def err(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult[T]":
        """Create an error result."""
        return cls(success=False, error=error, metadata=metadata or {})


class BaseTool(ABC, Generic[T]):
    """Abstract base class for all tools."""

    name: str = "base_tool"
    description: str = "Base tool description"

    @abstractmethod
    def call(self, **kwargs) -> ToolResult[T]:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult containing the result or error
        """
        pass

    def validate_inputs(self, **kwargs) -> bool:
        """Validate tool inputs before execution.

        Args:
            **kwargs: Input parameters

        Returns:
            True if inputs are valid
        """
        return True

    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema for LangChain/LangGraph integration."""
        return {
            "name": self.name,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(valid_inputs={self.validate_inputs()})>"
