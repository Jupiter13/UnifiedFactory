"""Web search tool for external knowledge lookup."""

from typing import Any, Dict, List, Optional
from edu_centre_ai.tools.base import BaseTool, ToolResponse
from edu_centre_ai.models.schemas import WebResult


class SearchWeb(BaseTool):
    """External knowledge lookup via web search.

    Optional tool for open-domain queries when internal knowledge is insufficient.
    """

    name = "search_web"
    description = "Search the web for information on a topic"

    def __init__(self, search_api_url: Optional[str] = None):
        """Initialize the tool.

        Args:
            search_api_url: URL for the search API
        """
        self.search_api_url = search_api_url

    def call(
        self,
        query: str,
        max_results: int = 5,
    ) -> ToolResponse:
        """Search the web.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            ToolResponse with list of WebResult
        """
        try:
            # In production, this would call a search API (e.g., Tavily, SerpAPI)
            results = self._search_mock(query, max_results)
            return ToolResponse(success=True, data=results)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _search_mock(
        self,
        query: str,
        max_results: int,
    ) -> List[WebResult]:
        """Mock web search for development/testing.

        Args:
            query: Search query
            max_results: Max results

        Returns:
            List of WebResult
        """
        return [
            WebResult(
                title=f"Result 1 for: {query}",
                snippet=f"This is a relevant result for your search about {query}. "
                f"It contains useful information that may help answer your question.",
                url="https://example.com/result1",
            ),
            WebResult(
                title=f"Result 2 for: {query}",
                snippet=f"Another helpful resource related to {query}. "
                f"Contains detailed explanations and examples.",
                url="https://example.com/result2",
            ),
            WebResult(
                title=f"Result 3 for: {query}",
                snippet=f"Additional information about {query} from authoritative sources.",
                url="https://example.com/result3",
            ),
        ][:max_results]

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "query" not in params:
            return False, "query is required"
        return True, None