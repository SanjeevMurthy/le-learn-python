"""
solution.py — Rate Limiter Implementation

Two algorithms: Token Bucket and Sliding Window.
"""

import time
import threading
from typing import Dict, Any
from collections import defaultdict


class TokenBucketLimiter:
    """
    Token bucket rate limiter.

    Tokens are added at a fixed rate. Each request consumes one token.
    Allows bursts up to the bucket capacity.
    """

    def __init__(self, max_tokens: int = 100, refill_rate: float = 1.0):
        """
        Args:
            max_tokens: Maximum tokens (burst capacity).
            refill_rate: Tokens added per second.
        """
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Check if a request from client_id is allowed."""
        with self._lock:
            now = time.time()

            if client_id not in self._buckets:
                self._buckets[client_id] = {
                    'tokens': self._max_tokens - 1,
                    'last_refill': now,
                }
                return True

            bucket = self._buckets[client_id]

            # Refill tokens based on elapsed time
            elapsed = now - bucket['last_refill']
            new_tokens = elapsed * self._refill_rate
            bucket['tokens'] = min(self._max_tokens, bucket['tokens'] + new_tokens)
            bucket['last_refill'] = now

            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True
            return False

    def get_status(self, client_id: str) -> Dict[str, Any]:
        """Get current rate limit status for a client."""
        with self._lock:
            bucket = self._buckets.get(client_id)
            if not bucket:
                return {'tokens': self._max_tokens, 'limited': False}
            return {
                'tokens': int(bucket['tokens']),
                'limited': bucket['tokens'] < 1,
            }


class SlidingWindowLimiter:
    """
    Sliding window rate limiter.

    Tracks request timestamps within the window. Smoother than
    fixed window but uses more memory.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Check if a request is allowed within the sliding window."""
        with self._lock:
            now = time.time()
            window_start = now - self._window

            # Remove expired timestamps
            self._requests[client_id] = [
                ts for ts in self._requests[client_id] if ts > window_start
            ]

            if len(self._requests[client_id]) < self._max_requests:
                self._requests[client_id].append(now)
                return True
            return False

    def get_status(self, client_id: str) -> Dict[str, Any]:
        """Get current status."""
        with self._lock:
            now = time.time()
            window_start = now - self._window
            active = [ts for ts in self._requests.get(client_id, []) if ts > window_start]
            return {
                'current': len(active),
                'limit': self._max_requests,
                'remaining': max(0, self._max_requests - len(active)),
            }


if __name__ == "__main__":
    # Token Bucket demo
    tb = TokenBucketLimiter(max_tokens=5, refill_rate=1)
    for i in range(8):
        print(f"  Request {i+1}: {'✅' if tb.is_allowed('client1') else '❌'}")

    # Sliding Window demo
    sw = SlidingWindowLimiter(max_requests=3, window_seconds=10)
    for i in range(5):
        print(f"  Request {i+1}: {'✅' if sw.is_allowed('client1') else '❌'}")
