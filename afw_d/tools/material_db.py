"""Material Database Query Tool.

Retrieves material properties from internal database/cache.
"""

from typing import Optional

from ..models import MaterialProperties


class MaterialDBQueryTool:
    """Tool for querying material properties from database."""

    # Mock material database
    _MATERIALS = {
        "Al-Mg-Si": MaterialProperties(
            family="Al-Mg-Si",
            density=2700.0,
            modulus=70.0,
            fatigue_limit=150.0,
            cost_per_kg=8.5,
        ),
        "Al-Cu-Mg": MaterialProperties(
            family="Al-Cu-Mg",
            density=2800.0,
            modulus=73.0,
            fatigue_limit=180.0,
            cost_per_kg=12.0,
        ),
        "Carbon-Epoxy": MaterialProperties(
            family="Carbon-Epoxy",
            density=1600.0,
            modulus=150.0,
            fatigue_limit=300.0,
            cost_per_kg=45.0,
        ),
        "Titanium-6Al-4V": MaterialProperties(
            family="Titanium-6Al-4V",
            density=4430.0,
            modulus=110.0,
            fatigue_limit=400.0,
            cost_per_kg=55.0,
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

    def invoke(self, family: str) -> MaterialProperties:
        """Query material properties by family.

        Args:
            family: Material family name.

        Returns:
            MaterialProperties for the given family.

        Raises:
            ValueError: If material family not found.
        """
        # Check cache first
        if self.cache_enabled and family in self._cache:
            return self._cache[family]

        # Look up in local database
        if family in self._MATERIALS:
            props = self._MATERIALS[family]
            if self.cache_enabled:
                self._cache[family] = props
            return props

        # If API is available, query it
        if self.api_url:
            props = self._query_api(family)
            if self.cache_enabled:
                self._cache[family] = props
            return props

        raise ValueError(f"Material family '{family}' not found in database")

    def _query_api(self, family: str) -> MaterialProperties:
        """Query external REST API for material properties.

        Args:
            family: Material family name.

        Returns:
            MaterialProperties from API.

        Raises:
            ValueError: If API query fails.
        """
        import httpx

        try:
            response = httpx.get(
                f"{self.api_url}/materials/{family}",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return MaterialProperties(**data)
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to query material API: {e}")

    def list_families(self) -> list[str]:
        """List all available material families."""
        return list(self._MATERIALS.keys())