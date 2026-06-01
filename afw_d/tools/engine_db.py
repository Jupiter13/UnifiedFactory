"""Engine Database Query Tool.

Retrieves engine specifications from internal database/cache.
"""

from typing import Optional

from ..models import EngineSpecs


class EngineDBQueryTool:
    """Tool for querying engine specifications from database."""

    # Mock engine database
    _ENGINES = {
        "Turboprop-A": EngineSpecs(
            family="Turboprop-A",
            thrust=850.0,  # kN equivalent for turboprop
            weight=180.0,
            fuel_consumption=120.0,
            cost=85000.0,
        ),
        "Turboprop-B": EngineSpecs(
            family="Turboprop-B",
            thrust=1200.0,
            weight=220.0,
            fuel_consumption=150.0,
            cost=120000.0,
        ),
        "Turbofan-A": EngineSpecs(
            family="Turbofan-A",
            thrust=2500.0,
            weight=350.0,
            fuel_consumption=200.0,
            cost=250000.0,
        ),
        "Turbofan-B": EngineSpecs(
            family="Turbofan-B",
            thrust=4000.0,
            weight=450.0,
            fuel_consumption=280.0,
            cost=380000.0,
        ),
        "Piston-360": EngineSpecs(
            family="Piston-360",
            thrust=180.0,
            weight=140.0,
            fuel_consumption=45.0,
            cost=35000.0,
        ),
    }

    def __init__(self, api_url: Optional[str] = None, cache_enabled: bool = True):
        """Initialize the tool.

        Args:
            api_url: Optional REST API URL for database.
            cache_enabled: Whether to use local cache.
        """
        self.api_url = api_url
        self.cache_enabled = cache_enabled
        self._cache = {}

    def invoke(self, family: str) -> EngineSpecs:
        """Query engine specifications by family.

        Args:
            family: Engine family name.

        Returns:
            EngineSpecs for the given family.

        Raises:
            ValueError: If engine family not found.
        """
        # Check cache first
        if self.cache_enabled and family in self._cache:
            return self._cache[family]

        # Look up in local database
        if family in self._ENGINES:
            specs = self._ENGINES[family]
            if self.cache_enabled:
                self._cache[family] = specs
            return specs

        # If API is available, query it
        if self.api_url:
            specs = self._query_api(family)
            if self.cache_enabled:
                self._cache[family] = specs
            return specs

        raise ValueError(f"Engine family '{family}' not found in database")

    def _query_api(self, family: str) -> EngineSpecs:
        """Query external REST API for engine specifications.

        Args:
            family: Engine family name.

        Returns:
            EngineSpecs from API.

        Raises:
            ValueError: If API query fails.
        """
        import httpx

        try:
            response = httpx.get(
                f"{self.api_url}/engines/{family}",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return EngineSpecs(**data)
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to query engine API: {e}")

    def list_families(self) -> list[str]:
        """List all available engine families."""
        return list(self._ENGINES.keys())