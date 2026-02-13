"""
graceful_degradation.py

Patterns for graceful degradation when services or resources fail.

Interview Topics:
- What is graceful degradation vs fail-fast?
- How do you keep a system partially functional during outages?
- Difference between graceful degradation and circuit breaker?

Production Use Cases:
- Serving cached data when database is down
- Returning default responses when non-critical services fail
- Feature flags for controlled degradation
- Multi-tier fallbacks (primary → secondary → cache → default)

Prerequisites:
- No external packages needed (stdlib only)
"""

import time
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

T = TypeVar('T')


def with_fallback(
    fallback_value: Any = None,
    fallback_func: Optional[Callable] = None,
    exceptions: tuple = (Exception,),
    log_level: str = "warning"
) -> Callable:
    """
    Decorator that returns a fallback value or calls a fallback function on failure.

    Instead of crashing, the decorated function returns a safe default.
    This is useful for non-critical operations where partial data is acceptable.

    Args:
        fallback_value: Static value to return on failure
        fallback_func: Function to call for dynamic fallback (overrides fallback_value)
        exceptions: Exception types to catch
        log_level: Logging level for the failure message

    Returns:
        Decorated function with fallback behavior

    Interview Question:
        Q: When is graceful degradation better than failing fast?
        A: When the failing component is non-critical and the user
           can still get value from partial results. Examples:
           - Dashboard missing one widget vs entire page failing
           - Search results without personalization vs no results
           - Cached data (possibly stale) vs no data at all
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Log the failure at the appropriate level
                log_func = getattr(logger, log_level)
                log_func(
                    f"Function '{func.__name__}' failed: {e}. "
                    f"Using fallback."
                )

                # Dynamic fallback takes priority
                if fallback_func is not None:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fb_err:
                        logger.error(
                            f"Fallback function also failed: {fb_err}. "
                            f"Returning static fallback: {fallback_value}"
                        )
                        return fallback_value

                return fallback_value

        return wrapper
    return decorator


def multi_tier_fallback(
    primary: Callable[..., T],
    fallbacks: List[Callable[..., T]],
    *args: Any,
    **kwargs: Any
) -> Optional[T]:
    """
    Try multiple data sources in order until one succeeds.

    Implements a tiered fallback strategy:
    primary → fallback1 → fallback2 → ... → None

    Args:
        primary: Primary function to try first
        fallbacks: List of fallback functions to try in order
        *args: Arguments to pass to each function
        **kwargs: Keyword arguments to pass to each function

    Returns:
        Result from the first successful call, or None

    Example:
        result = multi_tier_fallback(
            fetch_from_database,       # Try DB first
            [fetch_from_cache,         # Then cache
             fetch_from_cdn,           # Then CDN
             lambda: DEFAULT_DATA],    # Finally, default
            user_id=123
        )

    Interview Question:
        Q: Design a data retrieval system with multi-tier fallback.
        A: Primary source → local cache → distributed cache → stale replica
           → default value. Each tier has different consistency guarantees
           and you should log which tier served the request for monitoring.
    """
    # Try primary source first
    all_sources = [primary] + fallbacks
    source_names = ['primary'] + [f'fallback-{i + 1}' for i in range(len(fallbacks))]

    for source, name in zip(all_sources, source_names):
        try:
            result = source(*args, **kwargs)
            if result is not None:
                logger.info(f"Data retrieved from {name}: {source.__name__}")
                return result
            else:
                logger.warning(f"{name} ({source.__name__}) returned None, trying next...")
        except Exception as e:
            logger.warning(f"{name} ({source.__name__}) failed: {e}. Trying next...")

    logger.error("All data sources exhausted. Returning None.")
    return None


class SimpleCache:
    """
    Simple in-memory cache for fallback data.

    When the primary data source is down, the cache can serve
    the last-known-good data (potentially stale but better than nothing).

    Interview Question:
        Q: How do you decide between stale data and no data?
        A: Depends on the use case. For dashboards, stale data with
           a "last updated" timestamp is better than a blank page.
           For financial transactions, no data is better than stale data.
    """

    def __init__(self, default_ttl: float = 300.0):
        """
        Args:
            default_ttl: Default time-to-live for cache entries in seconds
        """
        self._store: Dict[str, dict] = {}
        self._default_ttl = default_ttl

    def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """
        Retrieve a cached value.

        Args:
            key: Cache key
            allow_stale: If True, return expired entries (for degradation)

        Returns:
            Cached value or None
        """
        if key not in self._store:
            return None

        entry = self._store[key]
        is_expired = time.time() > entry['expires_at']

        if is_expired and not allow_stale:
            logger.debug(f"Cache entry '{key}' expired")
            return None

        if is_expired and allow_stale:
            logger.warning(f"Serving STALE cache entry for '{key}' (degraded mode)")

        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the cache."""
        self._store[key] = {
            'value': value,
            'expires_at': time.time() + (ttl or self._default_ttl),
            'created_at': time.time()
        }

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()


def cached_degradation(
    cache: SimpleCache,
    cache_key: str,
    primary_func: Callable[..., T],
    *args: Any,
    ttl: float = 300.0,
    **kwargs: Any
) -> Optional[T]:
    """
    Fetch from primary, cache the result, serve stale cache on failure.

    This is a common pattern: always try the primary source first,
    cache successful results, and fall back to stale cache when primary fails.

    Args:
        cache: SimpleCache instance
        cache_key: Key to use in the cache
        primary_func: Primary data source function
        *args: Arguments for primary_func
        ttl: Cache time-to-live in seconds
        **kwargs: Keyword arguments for primary_func

    Returns:
        Data from primary source or stale cache

    Example:
        cache = SimpleCache(default_ttl=60)
        data = cached_degradation(
            cache, 'user_preferences',
            fetch_user_preferences, user_id=123
        )
    """
    try:
        # Try primary source
        result = primary_func(*args, **kwargs)

        # Cache the fresh result for future fallback
        cache.set(cache_key, result, ttl=ttl)
        logger.info(f"Fetched fresh data and cached as '{cache_key}'")
        return result

    except Exception as e:
        logger.warning(
            f"Primary source failed: {e}. "
            f"Falling back to cached data for '{cache_key}'"
        )

        # Return stale cached data — better than nothing
        stale_data = cache.get(cache_key, allow_stale=True)
        if stale_data is not None:
            return stale_data

        logger.error(f"No cached data available for '{cache_key}'")
        return None


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Graceful Degradation — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Simple fallback ----
    print("\n--- Example 1: Simple Fallback Decorator ---")

    @with_fallback(fallback_value={"status": "unknown", "healthy": True})
    def check_service_health(service_url: str) -> dict:
        """Simulate a health check that fails."""
        raise ConnectionError(f"Cannot reach {service_url}")

    result = check_service_health("http://api.example.com/health")
    print(f"  Health check result: {result}")

    # ---- Example 2: Multi-tier fallback ----
    print("\n--- Example 2: Multi-Tier Fallback ---")

    def fetch_from_database(user_id: int) -> Optional[dict]:
        raise ConnectionError("Database is down!")

    def fetch_from_cache(user_id: int) -> Optional[dict]:
        raise TimeoutError("Cache server timed out!")

    def fetch_default(user_id: int) -> dict:
        return {"user_id": user_id, "name": "Unknown", "source": "default"}

    user_data = multi_tier_fallback(
        fetch_from_database,
        [fetch_from_cache, fetch_default],
        user_id=42
    )
    print(f"  User data: {user_data}")

    # ---- Example 3: Cached degradation ----
    print("\n--- Example 3: Cached Degradation ---")

    cache = SimpleCache(default_ttl=60)

    # Pre-populate cache (simulating a previous successful call)
    cache.set("server_metrics", {
        "cpu": 45.2, "memory": 72.1, "load": 1.5, "source": "cached"
    })

    def fetch_live_metrics() -> dict:
        raise ConnectionError("Metrics server unreachable")

    metrics = cached_degradation(
        cache, "server_metrics", fetch_live_metrics
    )
    print(f"  Metrics (from stale cache): {metrics}")
