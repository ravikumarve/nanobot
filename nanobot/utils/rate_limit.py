"""Rate limiter utility for per-channel, per-user rate limiting."""

import asyncio
import time
from collections import defaultdict
from typing import Optional

from loguru import logger

from nanobot.config.schema import RateLimitConfig


class RateLimiter:
    """Token bucket rate limiter for per-channel, per-user rate limiting."""

    def __init__(self, max_rate: int, burst_size: int):
        """
        Initialize rate limiter.

        Args:
            max_rate: Maximum requests per minute
            burst_size: Number of requests allowed in burst
        """
        self.max_rate = max_rate
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Refill tokens based on max rate (per minute -> per second)
        refill_amount = elapsed * (self.max_rate / 60)
        self.tokens = min(self.tokens + refill_amount, self.burst_size)
        self.last_refill = now

    async def acquire(self) -> bool:
        """
        Try to acquire a token for a request.

        Returns:
            True if request is allowed, False if rate limited
        """
        async with self._lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    async def wait_and_acquire(self) -> bool:
        """
        Wait until a token is available and acquire it.

        Returns:
            True when token is acquired (after waiting if necessary)
        """
        async with self._lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True

            # Calculate wait time
            tokens_needed = 1
            wait_time = (tokens_needed - self.tokens) * (60 / self.max_rate)
            await asyncio.sleep(wait_time)

            # Refill again after waiting
            self._refill()
            self.tokens -= 1
            return True


class RateLimitManager:
    """Manages rate limiting per channel and per user."""

    def __init__(self):
        self.channel_limits: dict[str, RateLimiter] = {}
        self.user_limits: dict[str, dict[str, RateLimiter]] = defaultdict(dict)
        self.global_limit: Optional[RateLimiter] = None

    def configure_channel(self, channel_name: str, max_rate: int, burst_size: int) -> None:
        """Configure rate limiting for a specific channel."""
        self.channel_limits[channel_name] = RateLimiter(max_rate, burst_size)

    def configure_global(self, max_rate: int, burst_size: int) -> None:
        """Configure global rate limiting."""
        self.global_limit = RateLimiter(max_rate, burst_size)

    async def check_rate_limit(
        self, channel_name: str, user_id: str, config: Optional[RateLimitConfig] = None
    ) -> bool:
        """
        Check if request is allowed based on rate limits.

        Args:
            channel_name: Name of the channel
            user_id: User identifier
            config: Rate limit configuration

        Returns:
            True if request is allowed, False if rate limited
        """
        # Check global limit first
        if self.global_limit:
            if not await self.global_limit.acquire():
                logger.warning("Global rate limit exceeded")
                return False

        # Check channel limit
        if channel_limiter := self.channel_limits.get(channel_name):
            if not await channel_limiter.acquire():
                logger.warning("Channel rate limit exceeded for {}", channel_name)
                return False

        # Check per-user limit if configured
        if config and config.enabled:
            user_key = f"{channel_name}:{user_id}"
            if user_key not in self.user_limits[channel_name]:
                self.user_limits[channel_name][user_key] = RateLimiter(
                    config.max_requests_per_minute, config.burst_size
                )

            user_limiter = self.user_limits[channel_name][user_key]
            if not await user_limiter.acquire():
                logger.warning("User rate limit exceeded for {}:{}", channel_name, user_id)
                return False

        return True

    async def enforce_rate_limit(
        self, channel_name: str, user_id: str, config: Optional[RateLimitConfig] = None
    ) -> bool:
        """
        Enforce rate limiting, waiting if necessary.

        Args:
            channel_name: Name of the channel
            user_id: User identifier
            config: Rate limit configuration

        Returns:
            True when request is allowed (after waiting if necessary)
        """
        # Global limit (wait if necessary)
        if self.global_limit:
            await self.global_limit.wait_and_acquire()

        # Channel limit (wait if necessary)
        if channel_limiter := self.channel_limits.get(channel_name):
            await channel_limiter.wait_and_acquire()

        # Per-user limit if configured
        if config and config.enabled:
            user_key = f"{channel_name}:{user_id}"
            if user_key not in self.user_limits[channel_name]:
                self.user_limits[channel_name][user_key] = RateLimiter(
                    config.max_requests_per_minute, config.burst_size
                )

            user_limiter = self.user_limits[channel_name][user_key]
            await user_limiter.wait_and_acquire()

        return True
