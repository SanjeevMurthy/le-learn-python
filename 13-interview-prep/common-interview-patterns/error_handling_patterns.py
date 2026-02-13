"""
error_handling_patterns.py

Common error handling patterns for DevOps/SRE interviews.
"""

import time
import random
import logging
from typing import Any, Callable, Dict, TypeVar
from functools import wraps

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Interview Question:
        Q: Explain retry strategies and their trade-offs.
        A: Fixed delay: simple but can cause thundering herd.
           Exponential backoff: delay doubles each retry (1s, 2s, 4s, 8s).
           Jitter: add randomness to prevent synchronized retries.
           Circuit breaker: stop retrying after threshold (fail fast).
           Key: only retry idempotent operations, set max retries,
           use exponential backoff + jitter in production.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    delay = base_delay * (2 ** attempt if exponential else 1)
                    delay = min(delay, max_delay)
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def graceful_degradation(
    primary_fn: Callable,
    fallback_fn: Callable,
    timeout: float = 5.0
) -> Any:
    """
    Try primary, fall back to secondary on failure.

    Interview Question:
        Q: What is graceful degradation?
        A: When a dependency fails, serve reduced functionality
           instead of a complete failure.
           Examples: serve cached data on DB failure, show static
           page on API failure, disable non-critical features.
    """
    try:
        return primary_fn()
    except Exception as e:
        logger.warning(f"Primary failed ({e}), using fallback")
        return fallback_fn()


def bulkhead(max_concurrent: int = 10):
    """
    Bulkhead pattern: limit concurrent calls to isolate failures.
    """
    import threading
    semaphore = threading.Semaphore(max_concurrent)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not semaphore.acquire(timeout=5):
                raise RuntimeError("Bulkhead: max concurrent calls reached")
            try:
                return func(*args, **kwargs)
            finally:
                semaphore.release()
        return wrapper
    return decorator


if __name__ == "__main__":
    @retry_with_backoff(max_retries=2, base_delay=0.1)
    def flaky_operation():
        if random.random() < 0.7:
            raise ConnectionError("Connection refused")
        return "success"

    try:
        result = flaky_operation()
        print(f"  Result: {result}")
    except ConnectionError:
        print("  Failed after retries")
