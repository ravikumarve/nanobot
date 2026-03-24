"""TTL-based caching for expensive tool results."""

import asyncio
import hashlib
import time
from typing import Any, Optional
from dataclasses import dataclass
from collections import OrderedDict

from loguru import logger


@dataclass
class CacheEntry:
    """Cache entry with value and expiration timestamp."""

    value: Any
    expires_at: float


class ToolResultCache:
    """LRU cache with TTL for tool results."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    def _generate_key(self, tool_name: str, **kwargs) -> str:
        """Generate cache key from tool name and parameters."""
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts = [tool_name] + [f"{k}={v}" for k, v in sorted_kwargs]
        key_str = "&".join(key_parts)

        # Use hash for consistent length
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(self, tool_name: str, **kwargs) -> Optional[Any]:
        """
        Get cached result if available and not expired.

        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters

        Returns:
            Cached result or None if not found/expired
        """
        async with self._lock:
            key = self._generate_key(tool_name, **kwargs)

            if key not in self.cache:
                return None

            entry = self.cache[key]

            # Check if expired
            if time.time() > entry.expires_at:
                del self.cache[key]
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return entry.value

    async def set(self, tool_name: str, value: Any, ttl: Optional[int] = None, **kwargs) -> None:
        """
        Cache a tool result.

        Args:
            tool_name: Name of the tool
            value: Result to cache
            ttl: Time-to-live in seconds (uses default if None)
            **kwargs: Tool parameters
        """
        async with self._lock:
            key = self._generate_key(tool_name, **kwargs)
            expires_at = time.time() + (ttl or self.default_ttl)

            # Remove expired entries and enforce max size
            self._cleanup()

            self.cache[key] = CacheEntry(value=value, expires_at=expires_at)
            self.cache.move_to_end(key)

    def _cleanup(self) -> None:
        """Remove expired entries and enforce LRU eviction."""
        current_time = time.time()

        # Remove expired entries
        expired_keys = []
        for key, entry in self.cache.items():
            if current_time > entry.expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        # Enforce max size (remove oldest entries)
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    async def clear(self) -> None:
        """Clear all cached entries."""
        async with self._lock:
            self.cache.clear()

    async def stats(self) -> dict:
        """Get cache statistics."""
        async with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for entry in self.cache.values() if current_time > entry.expires_at
            )

            return {
                "total_entries": len(self.cache),
                "expired_entries": expired_count,
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
            }


# Global cache instance
tool_cache = ToolResultCache()
