"""Rate limiting utility for API calls."""

import asyncio
import random
import time


class RateLimiter:
    """Reusable rate limiter with jitter for API calls."""

    def __init__(
        self,
        base_delay: float = 1.0,
        jitter_range: tuple[float, float] = (0.5, 2.0),
        scale_after: int = 5,
        scale_factor: float = 1.5,
    ):
        """Initialize rate limiter.

        Args:
            base_delay: Base delay between requests in seconds.
            jitter_range: Min/max multiplier for random jitter.
            scale_after: Increase delay after this many requests.
            scale_factor: Multiplier for delay scaling.
        """
        self._base_delay = base_delay
        self._jitter_range = jitter_range
        self._scale_after = scale_after
        self._scale_factor = scale_factor
        self._last_request_time: float = 0
        self._request_count: int = 0
        self._random = random.Random()

    async def wait(self) -> None:
        """Wait appropriate time before next request."""
        now = time.time()
        elapsed = now - self._last_request_time

        # Calculate delay with jitter
        jitter = self._random.uniform(*self._jitter_range)
        delay = self._base_delay * jitter

        # Scale up delay after many requests
        if self._request_count > self._scale_after:
            delay *= self._scale_factor
        if self._request_count > self._scale_after * 2:
            delay *= self._scale_factor

        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)

        self._last_request_time = time.time()
        self._request_count += 1

    async def wait_with_backoff(self, request_count: int = 0, factor: float = 1.5) -> None:
        """Wait with exponential backoff based on request count.

        Args:
            request_count: Current request count for backoff calculation.
            factor: Backoff multiplier per request threshold.
        """
        now = time.time()
        elapsed = now - self._last_request_time

        # Calculate delay with jitter
        jitter = self._random.uniform(*self._jitter_range)
        delay = self._base_delay * jitter

        # Apply exponential backoff based on request count
        if request_count > self._scale_after:
            backoff_level = (request_count - self._scale_after) // self._scale_after + 1
            delay *= factor ** backoff_level

        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)

        self._last_request_time = time.time()
        self._request_count += 1

    def reset(self) -> None:
        """Reset request count (e.g., after long idle period)."""
        self._request_count = 0
