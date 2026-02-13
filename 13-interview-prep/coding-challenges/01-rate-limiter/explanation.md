# Rate Limiter — Explanation

## Algorithm Comparison

| Algorithm          | Burst Handling               | Memory                       | Precision   | Use Case                            |
| ------------------ | ---------------------------- | ---------------------------- | ----------- | ----------------------------------- |
| **Token Bucket**   | Allows bursts up to capacity | O(1) per client              | Approximate | API gateways, general rate limiting |
| **Sliding Window** | Smooth, no bursts            | O(n) per client (n=requests) | Exact       | Strict compliance requirements      |
| **Fixed Window**   | Allows 2x at window boundary | O(1) per client              | Low         | Simple, when precision not critical |
| **Leaky Bucket**   | No bursts, constant rate     | O(1) per client              | High        | Traffic shaping, output smoothing   |

## Key Design Decisions

1. **Thread safety**: `threading.Lock` ensures atomic check-and-update
2. **Per-client tracking**: Dictionary keyed by client ID
3. **Lazy refill**: Tokens calculated on access, not via background thread

## Distributed Rate Limiting

For multi-server deployments, use **Redis** as shared state:

```python
# Redis-based sliding window (simplified)
def is_allowed(client_id, limit, window):
    key = f"ratelimit:{client_id}"
    now = time.time()
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)  # Remove expired
    pipe.zadd(key, {str(now): now})              # Add current
    pipe.zcard(key)                               # Count
    pipe.expire(key, window)
    _, _, count, _ = pipe.execute()
    return count <= limit
```

## HTTP Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1705334400
Retry-After: 30  (when 429 returned)
```

## Time Complexity

- Token Bucket: O(1) per request
- Sliding Window: O(n) cleanup, amortized O(1)
