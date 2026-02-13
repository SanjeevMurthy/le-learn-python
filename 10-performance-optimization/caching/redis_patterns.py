"""
redis_patterns.py

Redis caching patterns for production use.

Interview Topics:
- Redis data structures
- Cache eviction policies
- Redis clustering and sentinel

Prerequisites:
- redis (pip install redis)
"""

import json
import time
import logging
from typing import Any, Optional, Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_client():
    import redis
    return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def cache_aside(key: str, fetch_fn, ttl: int = 300) -> Any:
    """
    Cache-aside (lazy loading) pattern.

    Interview Question:
        Q: Explain the main caching strategies.
        A: Cache-aside: app checks cache → miss → fetch from DB → populate cache.
           Write-through: write to cache + DB simultaneously (strong consistency).
           Write-behind: write to cache → async write to DB (better perf, risk of loss).
           Read-through: cache itself fetches from DB on miss.
           Refresh-ahead: proactively refresh before TTL expires.
           Cache-aside is most common. TTL prevents stale data.
    """
    client = _get_client()
    cached = client.get(key)
    if cached:
        logger.debug(f"Cache HIT: {key}")
        return json.loads(cached)

    logger.debug(f"Cache MISS: {key}")
    value = fetch_fn()
    client.setex(key, ttl, json.dumps(value))
    return value


def rate_limiter(key: str, limit: int = 100, window: int = 60) -> Dict[str, Any]:
    """
    Sliding window rate limiter using Redis.

    Interview Question:
        Q: How do you implement rate limiting?
        A: Algorithms: token bucket, sliding window, fixed window.
           Redis: INCR + EXPIRE (fixed window) or sorted sets (sliding).
           Distributed: Redis is shared state across all instances.
           Response: 429 Too Many Requests + Retry-After header.
    """
    client = _get_client()
    current = client.incr(key)
    if current == 1:
        client.expire(key, window)

    remaining = max(0, limit - current)
    return {
        'allowed': current <= limit,
        'current': current,
        'limit': limit,
        'remaining': remaining,
    }


def distributed_lock(key: str, ttl: int = 10) -> Optional[str]:
    """Acquire a distributed lock using Redis SET NX."""
    import uuid
    client = _get_client()

    lock_value = str(uuid.uuid4())
    acquired = client.set(f'lock:{key}', lock_value, nx=True, ex=ttl)
    return lock_value if acquired else None


def release_lock(key: str, lock_value: str) -> bool:
    """Release a distributed lock (only if we own it)."""
    client = _get_client()
    script = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    end
    return 0
    """
    result = client.eval(script, 1, f'lock:{key}', lock_value)
    return result == 1


if __name__ == "__main__":
    print("Redis Patterns — Usage Examples")
    print("""
    # Cache-aside
    user = cache_aside('user:123', lambda: {'name': 'Alice'}, ttl=300)

    # Rate limiting
    result = rate_limiter('api:user:123', limit=100, window=60)
    if not result['allowed']:
        print('Rate limited!')

    # Distributed lock
    lock = distributed_lock('process-payments')
    if lock:
        try:
            pass  # critical section
        finally:
            release_lock('process-payments', lock)
    """)
