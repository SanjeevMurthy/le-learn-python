"""
cache_strategies.py

Cache invalidation and consistency strategies.

Prerequisites:
- Standard library
"""

import time
import hashlib
import logging
from typing import Any, Dict, Optional, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache implementation."""

    def __init__(self, capacity: int = 100):
        self._capacity = capacity
        self._cache: Dict[str, Any] = {}
        self._access_order: list = []

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self._capacity:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        self._cache[key] = value
        self._access_order.append(key)


def versioned_cache_key(prefix: str, version: int, *args) -> str:
    """
    Generate a versioned cache key (invalidation via version bump).

    Interview Question:
        Q: How do you handle cache invalidation?
        A: "Two hard things in CS: cache invalidation and naming things."
           Strategies:
           1. TTL: simple, eventual consistency
           2. Event-driven: invalidate on write (pub/sub)
           3. Versioned keys: bump version = instant invalidation
           4. Write-through: update cache on every write
           5. Stampede prevention: lock on miss, others wait
           Choose based on consistency requirements vs performance.
    """
    parts = ':'.join(str(a) for a in args)
    return f'{prefix}:v{version}:{parts}'


def cache_stampede_protection(
    key: str,
    fetch_fn: Callable,
    cache: Dict[str, Any],
    ttl: int = 300,
    lock_timeout: int = 5
) -> Any:
    """Prevent cache stampede with probabilistic early expiration."""
    entry = cache.get(key)
    now = time.time()

    if entry and entry['expires_at'] > now:
        return entry['value']

    # Simulate lock (in production, use Redis SETNX)
    value = fetch_fn()
    cache[key] = {'value': value, 'expires_at': now + ttl}
    return value


def content_hash_key(content: str) -> str:
    """Generate a content-based cache key (content-addressable)."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


if __name__ == "__main__":
    # LRU Cache demo
    cache = LRUCache(capacity=3)
    cache.put('a', 1)
    cache.put('b', 2)
    cache.put('c', 3)
    cache.put('d', 4)  # Evicts 'a'
    print(f"  LRU: a={cache.get('a')}, b={cache.get('b')}, d={cache.get('d')}")

    # Versioned keys
    key = versioned_cache_key('user', 3, 'profile', 123)
    print(f"  Versioned key: {key}")
