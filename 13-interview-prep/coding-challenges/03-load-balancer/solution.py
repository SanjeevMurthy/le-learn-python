"""
solution.py — Load Balancer Implementation
"""

import threading
from typing import Dict, Any, List, Optional


class Backend:
    """Represents a backend server."""

    def __init__(self, address: str, weight: int = 1):
        self.address = address
        self.weight = weight
        self.healthy = True
        self.active_connections = 0


class RoundRobinBalancer:
    """Round-robin load balancer with health checking."""

    def __init__(self, backends: List[Backend]):
        self._backends = backends
        self._index = 0
        self._lock = threading.Lock()

    def next_backend(self) -> Optional[Backend]:
        """Get the next healthy backend."""
        with self._lock:
            healthy = [b for b in self._backends if b.healthy]
            if not healthy:
                return None
            backend = healthy[self._index % len(healthy)]
            self._index += 1
            return backend

    def mark_unhealthy(self, address: str) -> None:
        with self._lock:
            for b in self._backends:
                if b.address == address:
                    b.healthy = False

    def mark_healthy(self, address: str) -> None:
        with self._lock:
            for b in self._backends:
                if b.address == address:
                    b.healthy = True


class WeightedRoundRobinBalancer:
    """Weighted round-robin: backends get traffic proportional to weight."""

    def __init__(self, backends: List[Backend]):
        self._backends = backends
        self._lock = threading.Lock()
        self._current_weights = [0] * len(backends)

    def next_backend(self) -> Optional[Backend]:
        with self._lock:
            healthy = [(i, b) for i, b in enumerate(self._backends) if b.healthy]
            if not healthy:
                return None
            total_weight = sum(b.weight for _, b in healthy)
            for i, b in healthy:
                self._current_weights[i] += b.weight
            max_idx = max(healthy, key=lambda x: self._current_weights[x[0]])[0]
            self._current_weights[max_idx] -= total_weight
            return self._backends[max_idx]


class LeastConnectionsBalancer:
    """Route to backend with fewest active connections."""

    def __init__(self, backends: List[Backend]):
        self._backends = backends
        self._lock = threading.Lock()

    def next_backend(self) -> Optional[Backend]:
        with self._lock:
            healthy = [b for b in self._backends if b.healthy]
            if not healthy:
                return None
            return min(healthy, key=lambda b: b.active_connections)

    def connect(self, backend: Backend) -> None:
        with self._lock:
            backend.active_connections += 1

    def disconnect(self, backend: Backend) -> None:
        with self._lock:
            backend.active_connections = max(0, backend.active_connections - 1)


if __name__ == "__main__":
    backends = [Backend('10.0.0.1:8080'), Backend('10.0.0.2:8080'), Backend('10.0.0.3:8080')]

    rr = RoundRobinBalancer(backends)
    for i in range(6):
        b = rr.next_backend()
        print(f"  Request {i+1} → {b.address}")
