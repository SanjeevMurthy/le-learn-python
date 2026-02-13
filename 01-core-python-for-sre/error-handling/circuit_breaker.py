"""
circuit_breaker.py

Circuit breaker pattern for fault-tolerant service communication.

Interview Topics:
- What is the circuit breaker pattern and why is it needed?
- Difference between circuit breaker states (CLOSED, OPEN, HALF-OPEN)?
- How does this differ from retries?

Production Use Cases:
- Protecting downstream services from cascading failures
- Graceful degradation when dependencies are unavailable
- Fast-failing instead of slow timeouts
- Monitoring service health through failure rates

Prerequisites:
- No external packages needed (stdlib only)
"""

import time
import logging
import functools
import threading
from typing import Callable, Any, Optional, Tuple, Type
from enum import Enum
from dataclasses import dataclass, field

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """
    Circuit breaker has three states:

    CLOSED:    Normal operation — requests flow through. Failures are counted.
    OPEN:      Too many failures — requests are immediately rejected (fast-fail).
    HALF_OPEN: After timeout, allow ONE request through to test if service recovered.
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """
    Circuit breaker that wraps function calls for fault tolerance.

    Interview Question:
        Q: When would you use a circuit breaker vs retries?
        A: Retries are for transient failures (network blips).
           Circuit breakers are for sustained outages — they prevent
           wasting resources on a service that's definitely down,
           and they prevent cascading failures to upstream services.

    Args:
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Seconds to wait before trying again (half-open)
        success_threshold: Successful calls needed in half-open to close circuit
        exceptions: Exception types that count as failures
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 2
    exceptions: Tuple[Type[Exception], ...] = (Exception,)

    # Internal state tracking (not part of constructor)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking if recovery timeout has elapsed."""
        # If circuit is OPEN, check if enough time has passed to try again
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                # Transition to HALF_OPEN — allow one test request through
                logger.info(
                    f"Circuit breaker transitioning from OPEN to HALF_OPEN "
                    f"(waited {elapsed:.1f}s)"
                )
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        return self._state

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through the circuit breaker.

        Args:
            func: The function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func(*args, **kwargs)

        Raises:
            CircuitBreakerOpenError: If circuit is open (fast-fail)
            Exception: Whatever func raises (if circuit is closed/half-open)
        """
        with self._lock:
            current_state = self.state  # property checks timeout

            # OPEN state — reject immediately (fast-fail)
            if current_state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Will retry after {self.recovery_timeout}s."
                )

        # CLOSED or HALF_OPEN — try the call
        try:
            result = func(*args, **kwargs)
            # Call succeeded — record success
            self._on_success()
            return result

        except self.exceptions as e:
            # Call failed — record failure
            self._on_failure(e)
            raise

    def _on_success(self) -> None:
        """Handle a successful call — potentially close the circuit."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                # Count consecutive successes in half-open state
                self._success_count += 1
                logger.info(
                    f"Circuit breaker HALF_OPEN: success "
                    f"{self._success_count}/{self.success_threshold}"
                )

                # If we've had enough successes, close the circuit
                if self._success_count >= self.success_threshold:
                    logger.info("Circuit breaker transitioning to CLOSED")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                self._failure_count = 0

    def _on_failure(self, error: Exception) -> None:
        """Handle a failed call — potentially open the circuit."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                logger.warning(
                    f"Circuit breaker HALF_OPEN failed: {error}. "
                    f"Returning to OPEN state."
                )
                self._state = CircuitState.OPEN

            elif self._state == CircuitState.CLOSED:
                # Check if we've exceeded the failure threshold
                if self._failure_count >= self.failure_threshold:
                    logger.error(
                        f"Circuit breaker OPEN: {self._failure_count} failures "
                        f"exceeded threshold of {self.failure_threshold}"
                    )
                    self._state = CircuitState.OPEN
                else:
                    logger.warning(
                        f"Circuit breaker failure "
                        f"{self._failure_count}/{self.failure_threshold}: {error}"
                    )

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            logger.info("Circuit breaker manually reset to CLOSED")

    def get_stats(self) -> dict:
        """Get current circuit breaker statistics."""
        return {
            'state': self._state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout
        }


class CircuitBreakerOpenError(Exception):
    """Raised when a call is attempted while the circuit is open."""
    pass


def circuit_breaker_decorator(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    success_threshold: int = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator version of circuit breaker for easy function wrapping.

    Args:
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again
        success_threshold: Successes needed to close circuit
        exceptions: Exception types that count as failures

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @circuit_breaker_decorator(failure_threshold=3, recovery_timeout=10)
        def call_payment_service(order_id):
            return requests.post(f'http://payments/charge/{order_id}')
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
        exceptions=exceptions
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        # Attach breaker instance for inspection/reset
        wrapper.circuit_breaker = breaker
        return wrapper
    return decorator


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Circuit Breaker Pattern — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Using CircuitBreaker directly ----
    print("\n--- Example 1: Direct Usage ---")

    # Create a circuit breaker with low thresholds for demo
    cb = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2.0,
        success_threshold=1
    )

    call_count = [0]  # Use mutable container for closure access

    def unreliable_service() -> str:
        call_count[0] += 1
        # Fail first 4 times, then succeed
        if call_count[0] <= 4:
            raise ConnectionError(f"Service down (call #{call_count[0]})")
        return "Service is back!"

    # Make calls through the circuit breaker
    for i in range(6):
        try:
            result = cb.call(unreliable_service)
            print(f"  Call {i + 1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"  Call {i + 1}: FAST-FAIL — {e}")
        except ConnectionError as e:
            print(f"  Call {i + 1}: ERROR — {e}")
        print(f"          State: {cb.get_stats()}")
        time.sleep(0.5)

    # ---- Example 2: Using decorator ----
    print("\n--- Example 2: Decorator Usage ---")

    attempt = [0]  # Use mutable container for closure access

    @circuit_breaker_decorator(
        failure_threshold=2,
        recovery_timeout=1.0,
        exceptions=(TimeoutError,)
    )
    def check_service_health() -> dict:
        attempt[0] += 1
        if attempt[0] <= 3:
            raise TimeoutError("Health check timed out")
        return {"status": "healthy", "latency_ms": 42}

    for i in range(5):
        try:
            health = check_service_health()
            print(f"  Check {i + 1}: {health}")
        except (CircuitBreakerOpenError, TimeoutError) as e:
            print(f"  Check {i + 1}: {type(e).__name__} — {e}")
        time.sleep(0.5)

    # Show final stats
    print(f"\n  Final stats: {check_service_health.circuit_breaker.get_stats()}")
