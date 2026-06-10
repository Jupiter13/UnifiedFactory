"""Session cache for tool results using Redis.

Reduces API calls by caching recent tool results for 5 minutes.
"""

import json
from typing import Any, Dict, Optional

import redis


class SessionCache:
    """Redis-based session cache for tool results."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,
    ):
        """Initialize session cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None

    def connect(self) -> bool:
        """Connect to Redis.

        Returns:
            True if connection successful
        """
        try:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            self._client.ping()
            return True
        except Exception:
            return False

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self._client:
            return None

        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful
        """
        if not self._client:
            return False

        try:
            ttl = ttl or self.default_ttl
            self._client.setex(
                key,
                ttl,
                json.dumps(value),
            )
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self._client:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception:
            return False

    def clear_user_cache(self, user_id: str) -> bool:
        """Clear all cache entries for a user.

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        if not self._client:
            return False

        try:
            pattern = f"cache:user:{user_id}:*"
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            self._client.close()
            self._client = None


def cache_key(user_id: str, tool_name: str, params_hash: str) -> str:
    """Generate a cache key.

    Args:
        user_id: User identifier
        tool_name: Tool name
        params_hash: Hash of tool parameters

    Returns:
        Cache key string
    """
    return f"cache:user:{user_id}:{tool_name}:{params_hash}"