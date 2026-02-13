"""
memcached_examples.py

Memcached caching patterns.

Prerequisites:
- pymemcache (pip install pymemcache)
"""

import json
import logging
from typing import Any, Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_client():
    from pymemcache.client.base import Client
    return Client('localhost:11211', serializer=_json_serializer, deserializer=_json_deserializer)


def _json_serializer(key, value):
    if isinstance(value, str):
        return value, 1
    return json.dumps(value), 2


def _json_deserializer(key, value, flags):
    if flags == 1:
        return value.decode('utf-8')
    if flags == 2:
        return json.loads(value.decode('utf-8'))
    return value


def get_or_set(key: str, fetch_fn, ttl: int = 300) -> Any:
    """
    Get from cache or set from source.

    Interview Question:
        Q: Redis vs Memcached — when to use each?
        A: Memcached: simple key-value, multi-threaded (better for
           simple caching), no persistence, max value 1MB.
           Redis: data structures (lists, sets, hashes, streams),
           persistence (RDB/AOF), pub/sub, Lua scripting, clustering.
           Choose Memcached: simple session/page caching, multi-threaded perf.
           Choose Redis: complex data, distributed locks, rate limiting,
           queues, leaderboards, pub/sub, persistence needed.
    """
    client = _get_client()
    cached = client.get(key)
    if cached is not None:
        return cached

    value = fetch_fn()
    client.set(key, value, expire=ttl)
    return value


def multi_get(keys: list) -> Dict[str, Any]:
    """Get multiple keys in one round-trip."""
    client = _get_client()
    return client.get_many(keys)


def invalidate_pattern(prefix: str) -> int:
    """Invalidate keys by prefix (requires key tracking)."""
    # Memcached doesn't support key scanning — need application-level tracking
    logger.warning("Memcached doesn't support key scanning — use versioned keys instead")
    return 0


if __name__ == "__main__":
    print("Memcached Examples — Usage Examples")
    print("""
    result = get_or_set('user:123', lambda: {'name': 'Alice'}, ttl=300)
    results = multi_get(['user:1', 'user:2', 'user:3'])
    """)
