"""
solution.py — Circuit Breaker Implementation
"""

import time
import threading
from typing import Callable, Any, Dict
from enum import Enum


class State(Enum):
    CLOSED = 'closed'       # Normal — requests pass through
    OPEN = 'open'           # Failing — requests rejected immediately
    HALF_OPEN = 'half_open' # Testing — one request allowed through


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    CLOSED: requests pass. After `failure_threshold` consecutive failures → OPEN.
    OPEN: requests fail immediately. After `reset_timeout` → HALF_OPEN.
    HALF_OPEN: one test request. If success → CLOSED. If fail → OPEN.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_max: int = 1
    ):
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._half_open_max = half_open_max
        self._state = State.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> State:
        with self._lock:
            if self._state == State.OPEN:
                if time.time() - self._last_failure_time >= self._reset_timeout:
                    self._state = State.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function through the circuit breaker."""
        current_state = self.state

        if current_state == State.OPEN:
            raise CircuitOpenError("Circuit breaker is OPEN — request rejected")

        if current_state == State.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self._half_open_max:
                    raise CircuitOpenError("Circuit HALF_OPEN — max test requests reached")
                self._half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = State.CLOSED

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self._failure_threshold:
                self._state = State.OPEN

    def get_status(self) -> Dict[str, Any]:
        return {
            'state': self.state.value,
            'failure_count': self._failure_count,
            'threshold': self._failure_threshold,
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


if __name__ == "__main__":
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=5)

    def unreliable_service():
        raise ConnectionError("Service unavailable")

    for i in range(5):
        try:
            cb.call(unreliable_service)
        except CircuitOpenError:
            print(f"  Request {i+1}: ⚡ Circuit OPEN — rejected immediately")
        except ConnectionError:
            print(f"  Request {i+1}: ❌ Failed (circuit: {cb.state.value})")

    print(f"  Final state: {cb.get_status()}")
