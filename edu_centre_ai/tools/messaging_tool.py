"""Messaging tool for sending notifications."""

from typing import Optional
from edu_centre_ai.tools.base import BaseTool, ToolResponse


class SendMessage(BaseTool):
    """Send notifications to users via Chat Service.

    Pushes messages/notifications to users on the platform.
    """

    name = "send_message"
    description = "Send a notification message to a user"

    def __init__(self, chat_service_url: Optional[str] = None):
        """Initialize the tool.

        Args:
            chat_service_url: URL for the Chat Service API
        """
        self.chat_service_url = chat_service_url or "http://chat-service:8000"

    def call(
        self,
        to_user_id: str,
        content: str,
        priority: str = "normal",
    ) -> ToolResponse:
        """Send a message to a user.

        Args:
            to_user_id: Target user identifier
            content: Message content
            priority: Message priority (normal, high, urgent)

        Returns:
            ToolResponse with sending status
        """
        try:
            # In production, this would call the Chat Service API
            status = self._send_message_mock(to_user_id, content, priority)
            return ToolResponse(success=True, data=status)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _send_message_mock(
        self,
        to_user_id: str,
        content: str,
        priority: str,
    ) -> dict:
        """Mock message sending for development/testing.

        Args:
            to_user_id: Target user ID
            content: Message content
            priority: Message priority

        Returns:
            Status dictionary
        """
        return {
            "status": "sent",
            "to_user_id": to_user_id,
            "content_preview": content[:50] + "..." if len(content) > 50 else content,
            "priority": priority,
            "sent_at": "2024-01-15T10:00:00Z",
        }

    def validate_params(self, params: dict) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "to_user_id" not in params:
            return False, "to_user_id is required"
        if "content" not in params:
            return False, "content is required"
        return True, None