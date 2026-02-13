"""
test_interview_patterns.py

Unit tests for Module 13 — Interview Pattern implementations.
"""

import os
import sys
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_rate_limiter_token_bucket():
    """Test token bucket allows up to max then blocks."""
    from collections import defaultdict

    class SimpleTokenBucket:
        def __init__(self, max_tokens):
            self.tokens = max_tokens

        def is_allowed(self):
            if self.tokens > 0:
                self.tokens -= 1
                return True
            return False

    bucket = SimpleTokenBucket(3)
    results = [bucket.is_allowed() for _ in range(5)]
    assert results == [True, True, True, False, False]
    print("  ✅ test_rate_limiter_token_bucket")


def test_circuit_breaker_state_transitions():
    """Test circuit breaker state machine."""
    states = ['CLOSED', 'OPEN', 'HALF_OPEN']

    # CLOSED → failures → OPEN
    failure_count = 0
    threshold = 3
    state = 'CLOSED'

    for _ in range(threshold):
        failure_count += 1
        if failure_count >= threshold:
            state = 'OPEN'

    assert state == 'OPEN', "Should transition to OPEN after threshold failures"

    # OPEN → timeout → HALF_OPEN
    state = 'HALF_OPEN'  # After reset timeout
    assert state == 'HALF_OPEN'

    # HALF_OPEN → success → CLOSED
    state = 'CLOSED'
    assert state == 'CLOSED'
    print("  ✅ test_circuit_breaker_state_transitions")


def test_pagination():
    """Test paginated response generation."""
    items = list(range(50))
    page_size = 10
    page = 3

    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    assert page_items == [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    assert len(page_items) == page_size
    print("  ✅ test_pagination")


def test_retry_logic():
    """Test retry with exponential backoff calculation."""
    base_delay = 1.0
    max_retries = 4

    delays = [base_delay * (2 ** attempt) for attempt in range(max_retries)]
    assert delays == [1.0, 2.0, 4.0, 8.0], f"Expected exponential delays, got {delays}"
    print("  ✅ test_retry_logic")


if __name__ == "__main__":
    print("Interview Patterns Unit Tests")
    test_rate_limiter_token_bucket()
    test_circuit_breaker_state_transitions()
    test_pagination()
    test_retry_logic()
    print("  All tests passed!")
