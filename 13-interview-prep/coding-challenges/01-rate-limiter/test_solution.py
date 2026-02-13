"""
test_solution.py — Tests for Rate Limiter
"""

import time
import threading
from solution import TokenBucketLimiter, SlidingWindowLimiter


def test_token_bucket_allows_up_to_max():
    limiter = TokenBucketLimiter(max_tokens=5, refill_rate=0)
    results = [limiter.is_allowed('test') for _ in range(7)]
    assert results == [True, True, True, True, True, False, False], \
        f"Expected 5 allowed then blocked, got {results}"
    print("  ✅ test_token_bucket_allows_up_to_max")


def test_token_bucket_refills():
    limiter = TokenBucketLimiter(max_tokens=2, refill_rate=10)
    limiter.is_allowed('test')
    limiter.is_allowed('test')
    assert not limiter.is_allowed('test'), "Should be blocked"
    time.sleep(0.2)  # Refill ~2 tokens
    assert limiter.is_allowed('test'), "Should be allowed after refill"
    print("  ✅ test_token_bucket_refills")


def test_sliding_window_limits():
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=1)
    assert limiter.is_allowed('test')
    assert limiter.is_allowed('test')
    assert limiter.is_allowed('test')
    assert not limiter.is_allowed('test'), "Should be blocked at limit"
    print("  ✅ test_sliding_window_limits")


def test_sliding_window_expires():
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=0.5)
    limiter.is_allowed('test')
    limiter.is_allowed('test')
    assert not limiter.is_allowed('test')
    time.sleep(0.6)
    assert limiter.is_allowed('test'), "Should be allowed after window expires"
    print("  ✅ test_sliding_window_expires")


def test_thread_safety():
    limiter = TokenBucketLimiter(max_tokens=100, refill_rate=0)
    results = []

    def make_request():
        results.append(limiter.is_allowed('test'))

    threads = [threading.Thread(target=make_request) for _ in range(150)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    allowed = sum(1 for r in results if r)
    assert allowed == 100, f"Expected exactly 100 allowed, got {allowed}"
    print("  ✅ test_thread_safety")


if __name__ == "__main__":
    print("Rate Limiter Tests")
    test_token_bucket_allows_up_to_max()
    test_token_bucket_refills()
    test_sliding_window_limits()
    test_sliding_window_expires()
    test_thread_safety()
    print("  All tests passed!")
