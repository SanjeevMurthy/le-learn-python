"""
optimization_techniques.py

Performance optimization techniques for interviews.
"""

import time
import hashlib
import logging
from typing import Any, Callable, Dict
from functools import lru_cache, wraps

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def memoize(func: Callable) -> Callable:
    """
    Simple memoization decorator.

    Interview Question:
        Q: What optimization techniques do you apply most often?
        A: 1. Caching/memoization: avoid repeated computation
           2. Batch operations: reduce I/O round-trips
           3. Connection pooling: reuse expensive connections
           4. Async I/O: overlap wait times
           5. Indexing: database query optimization
           6. Compression: reduce network payload
           7. Lazy loading: defer work until needed
    """
    cache: Dict = {}

    @wraps(func)
    def wrapper(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    wrapper.cache = cache
    return wrapper


def batch_processor(
    items: list,
    process_fn: Callable,
    batch_size: int = 100
) -> list:
    """Process items in batches to reduce overhead."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        results.extend(process_fn(batch))
    return results


class ConnectionPool:
    """
    Simple connection pool skeleton.

    Interview Question:
        Q: Why use connection pooling?
        A: Creating connections is expensive (TCP handshake, TLS,
           authentication). Pool reuses connections.
           Sizing: too small = queuing, too large = resource waste.
           Types: fixed pool (predictable), elastic (scale with load).
           Examples: PgBouncer (Postgres), HikariCP (Java/JDBC).
    """

    def __init__(self, max_size: int = 10):
        self._max_size = max_size
        self._available: list = []
        self._in_use: int = 0

    def acquire(self):
        if self._available:
            self._in_use += 1
            return self._available.pop()
        if self._in_use < self._max_size:
            self._in_use += 1
            return self._create_connection()
        raise RuntimeError("Pool exhausted")

    def release(self, conn):
        self._in_use -= 1
        self._available.append(conn)

    def _create_connection(self):
        return {'id': self._in_use, 'created': time.time()}


if __name__ == "__main__":
    @memoize
    def expensive_compute(n):
        time.sleep(0.01)  # Simulate work
        return n * n

    start = time.perf_counter()
    for i in range(100):
        expensive_compute(i % 10)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  100 calls (10 unique): {elapsed:.1f}ms")
