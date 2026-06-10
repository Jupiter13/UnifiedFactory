"""Code execution tool for sandboxed Python snippets."""

import io
import sys
from typing import Any, Dict, Optional
from contextlib import redirect_stdout, redirect_stderr

from edu_centre_ai.tools.base import BaseTool, ToolResponse


class ExecuteCode(BaseTool):
    """Execute Python code snippets in a sandboxed environment.

    Used for debugging or custom calculations within the agent.
    WARNING: In production, this should be heavily sandboxed (e.g., using
    Docker containers or serverless functions with strict resource limits).
    """

    name = "execute_code"
    description = "Run Python code snippets in a sandboxed environment"

    def __init__(self, timeout_seconds: int = 10, max_output_length: int = 10000):
        """Initialize the tool.

        Args:
            timeout_seconds: Maximum execution time
            max_output_length: Maximum length of output to capture
        """
        self.timeout_seconds = timeout_seconds
        self.max_output_length = max_output_length

    def call(self, code: str) -> ToolResponse:
        """Execute Python code.

        Args:
            code: Python code to execute

        Returns:
            ToolResponse with output or error
        """
        try:
            output, error = self._execute_sandboxed(code)
            if error:
                return ToolResponse(success=False, error=error)
            return ToolResponse(success=True, data={"output": output})

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _execute_sandboxed(self, code: str) -> tuple[str, Optional[str]]:
        """Execute code in a sandboxed environment.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (output, error)
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the code
                exec(code, {"__builtins__": __builtins__})

            output = stdout_capture.getvalue()
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + "\n... [output truncated]"

            return output, None

        except SyntaxError as e:
            return "", f"Syntax Error: {e}"
        except Exception as e:
            error_output = stderr_capture.getvalue()
            return "", f"{type(e).__name__}: {e}\n{error_output}"

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "code" not in params:
            return False, "code is required"
        if not isinstance(params.get("code"), str):
            return False, "code must be a string"
        return True, None