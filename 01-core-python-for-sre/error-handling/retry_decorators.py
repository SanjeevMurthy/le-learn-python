"""
retry_decorators.py

Robust retry logic with exponential backoff and jitter for resilient operations.

Interview Topics:
- Why exponential backoff instead of fixed-interval retries?
- How does jitter prevent thundering herd problems?
- When should you NOT retry?

Production Use Cases:
- API calls to rate-limited services (AWS, GCP)
- Database connections during failover
- Network operations across unreliable links
- Webhook delivery with guaranteed delivery

Prerequisites:
- No external packages needed (stdlib only)
"""

import time
import random
import logging
import functools
from typing import Tuple, Type, Callable, Any, Optional

# Set up logging — always configure at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator that retries a function with exponential backoff.

    Exponential backoff progressively increases the wait time between retries,
    preventing thundering herd problems and reducing load on failing services.

    Args:
        max_retries: Maximum number of retry attempts (not including the first call)
        initial_delay: Seconds to wait before the first retry
        backoff_factor: Multiplier applied to delay after each retry
                       (e.g., 2.0 means delays of 1, 2, 4, 8, ...)
        max_delay: Maximum delay in seconds (caps the exponential growth)
        jitter: If True, adds random variation to delay to avoid synchronized retries
        exceptions: Tuple of exception types that trigger a retry

    Returns:
        Decorated function with retry behavior

    Example:
        @retry_with_backoff(max_retries=5, initial_delay=2.0)
        def call_external_api():
            return requests.get('https://api.example.com/data')

    Interview Question:
        Q: Why use exponential backoff instead of fixed-interval retries?
        A: Fixed-interval retries can overwhelm a recovering service.
           Exponential backoff gradually reduces pressure, giving the
           service time to recover. Combined with jitter, it prevents
           multiple clients from retrying simultaneously (thundering herd).
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Track the current delay — starts at initial_delay
            delay = initial_delay

            # Attempt the function call up to max_retries + 1 times
            for attempt in range(max_retries + 1):
                try:
                    # Try to execute the wrapped function
                    result = func(*args, **kwargs)
                    # If we get here, the call succeeded
                    if attempt > 0:
                        logger.info(
                            f"Function '{func.__name__}' succeeded on attempt "
                            f"{attempt + 1} after {attempt} retries"
                        )
                    return result

                except exceptions as e:
                    # Check if we've exhausted all retries
                    if attempt == max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after "
                            f"{max_retries + 1} attempts. Last error: {e}"
                        )
                        # Re-raise the last exception — caller needs to handle it
                        raise

                    # Calculate the next delay with exponential backoff
                    # Formula: delay = initial_delay * (backoff_factor ^ attempt)
                    current_delay = min(delay, max_delay)

                    # Add jitter to prevent thundering herd
                    # Jitter randomizes the delay so multiple clients don't
                    # all retry at exactly the same time
                    if jitter:
                        current_delay = current_delay * (0.5 + random.random())

                    logger.warning(
                        f"Function '{func.__name__}' failed (attempt {attempt + 1}/"
                        f"{max_retries + 1}): {e}. Retrying in {current_delay:.2f}s..."
                    )

                    # Wait before retrying
                    time.sleep(current_delay)

                    # Increase delay for next retry (exponential growth)
                    delay *= backoff_factor

        return wrapper
    return decorator


def retry_with_custom_condition(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_condition: Optional[Callable[[Any], bool]] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Retry decorator with a custom condition to check if retry is needed.

    Unlike retry_with_backoff, this also retries when the function returns
    a value that indicates failure (e.g., empty result, HTTP 500).

    Args:
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Delay multiplier per attempt
        retry_condition: A function that takes the result and returns True
                        if a retry should be attempted
        exceptions: Exception types that trigger a retry

    Returns:
        Decorated function

    Example:
        # Retry if API returns empty list
        @retry_with_custom_condition(
            retry_condition=lambda result: len(result) == 0
        )
        def fetch_instances():
            return ec2_client.describe_instances()

    Interview Question:
        Q: When should you NOT retry an operation?
        A: Don't retry non-idempotent operations (e.g., payment processing),
           operations that fail due to invalid input (4xx errors),
           or operations where retrying could cause data duplication.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    # Execute the function
                    result = func(*args, **kwargs)

                    # Check custom retry condition if provided
                    # This allows retrying based on the return value,
                    # not just exceptions
                    if retry_condition and retry_condition(result):
                        if attempt == max_retries:
                            logger.warning(
                                f"'{func.__name__}' retry condition still met "
                                f"after {max_retries + 1} attempts. Returning last result."
                            )
                            return result

                        logger.info(
                            f"'{func.__name__}' returned unsatisfactory result "
                            f"(attempt {attempt + 1}). Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                        continue

                    return result

                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"'{func.__name__}' failed after {max_retries + 1} "
                            f"attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"'{func.__name__}' raised {type(e).__name__} "
                        f"(attempt {attempt + 1}): {e}. Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper
    return decorator


def simple_retry(func: Callable, max_attempts: int = 3, delay: float = 1.0) -> Any:
    """
    Simple procedural retry — no decorator, just wrap any call.

    Useful when you don't want to modify the function definition
    or when retrying a one-off call.

    Args:
        func: Callable (no arguments) to retry
        max_attempts: Number of attempts
        delay: Fixed delay between attempts in seconds

    Returns:
        Result of the function call

    Raises:
        Exception: The last exception if all attempts fail

    Example:
        result = simple_retry(
            lambda: requests.get('https://api.example.com/status'),
            max_attempts=3,
            delay=2.0
        )
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}"
            )
            if attempt < max_attempts - 1:
                time.sleep(delay)

    # If we get here, all attempts failed
    raise last_exception


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Retry Decorators — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Basic retry with backoff ----
    print("\n--- Example 1: Basic Retry with Backoff ---")

    call_count = [0]  # Use mutable container for closure access

    @retry_with_backoff(
        max_retries=3,
        initial_delay=0.5,
        backoff_factor=2.0,
        exceptions=(ConnectionError, TimeoutError)
    )
    def unreliable_api_call() -> str:
        """Simulates an API that fails twice then succeeds."""
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionError(f"Connection refused (attempt {call_count[0]})")
        return "Success! Data retrieved."

    try:
        result = unreliable_api_call()
        print(f"Result: {result}")
    except ConnectionError as e:
        print(f"All retries exhausted: {e}")

    # ---- Example 2: Retry with custom condition ----
    print("\n--- Example 2: Retry with Custom Condition ---")

    attempt_num = [0]  # Use mutable container for closure access

    @retry_with_custom_condition(
        max_retries=3,
        initial_delay=0.5,
        retry_condition=lambda result: len(result) == 0
    )
    def fetch_data() -> list:
        """Returns empty list first 2 times, then returns data."""
        attempt_num[0] += 1
        if attempt_num[0] < 3:
            return []  # Empty — triggers retry
        return [{"id": 1, "name": "instance-1"}, {"id": 2, "name": "instance-2"}]

    data = fetch_data()
    print(f"Fetched {len(data)} items: {data}")

    # ---- Example 3: Simple procedural retry ----
    print("\n--- Example 3: Simple Procedural Retry ---")

    counter = [0]  # Use mutable container for closure access

    def flaky_operation():
        counter[0] += 1
        if counter[0] < 2:
            raise TimeoutError("Operation timed out")
        return "Operation completed"

    try:
        result = simple_retry(flaky_operation, max_attempts=3, delay=0.5)
        print(f"Result: {result}")
    except TimeoutError:
        print("All attempts failed")
