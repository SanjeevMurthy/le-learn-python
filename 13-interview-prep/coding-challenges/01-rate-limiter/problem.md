# Rate Limiter

## Problem Statement

Design and implement a rate limiter that can be used to throttle API requests.

### Requirements

1. Support multiple rate limiting algorithms:
   - **Token Bucket**: Allows burst traffic up to bucket capacity
   - **Sliding Window**: Smooth rate limiting based on time window
2. Track requests per client (by IP or API key)
3. Return whether a request is allowed or should be rate-limited
4. Thread-safe for concurrent access

### Constraints

- Handle up to 10,000 clients
- Support configurable rate limits (e.g., 100 requests per minute)
- O(1) time complexity for the `is_allowed()` check

### Example

```python
limiter = RateLimiter(max_requests=100, window_seconds=60)
limiter.is_allowed("client_1")  # True (first request)
# ... 99 more requests ...
limiter.is_allowed("client_1")  # False (rate limited)
```

### Follow-up Questions

1. How would you implement this in a distributed system (multiple servers)?
2. How do you handle burst traffic vs sustained traffic?
3. What HTTP headers should you return for rate-limited requests?
