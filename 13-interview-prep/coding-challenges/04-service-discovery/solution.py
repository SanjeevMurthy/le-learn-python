"""
solution.py — Service Discovery Implementation
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import defaultdict


class ServiceRegistry:
    """
    In-memory service registry with TTL-based health.

    Services register with a TTL. If not renewed, they expire.
    Consumers discover services by name and get healthy instances.
    """

    def __init__(self):
        self._services: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self._lock = threading.Lock()

    def register(self, service_name: str, instance_id: str,
                 address: str, port: int, ttl: int = 30,
                 metadata: Dict[str, str] = None) -> None:
        """Register a service instance."""
        with self._lock:
            self._services[service_name][instance_id] = {
                'address': address,
                'port': port,
                'registered_at': time.time(),
                'last_heartbeat': time.time(),
                'ttl': ttl,
                'metadata': metadata or {},
            }

    def deregister(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        with self._lock:
            if service_name in self._services and instance_id in self._services[service_name]:
                del self._services[service_name][instance_id]
                return True
            return False

    def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """Renew a service's TTL."""
        with self._lock:
            if service_name in self._services and instance_id in self._services[service_name]:
                self._services[service_name][instance_id]['last_heartbeat'] = time.time()
                return True
            return False

    def discover(self, service_name: str) -> List[Dict[str, Any]]:
        """Discover healthy instances of a service."""
        with self._lock:
            now = time.time()
            healthy = []
            for iid, info in self._services.get(service_name, {}).items():
                if now - info['last_heartbeat'] <= info['ttl']:
                    healthy.append({
                        'instance_id': iid,
                        'address': info['address'],
                        'port': info['port'],
                        'metadata': info['metadata'],
                    })
            return healthy

    def list_services(self) -> List[str]:
        """List all registered service names."""
        with self._lock:
            return list(self._services.keys())


if __name__ == "__main__":
    registry = ServiceRegistry()

    registry.register('api', 'api-1', '10.0.0.1', 8080, ttl=30)
    registry.register('api', 'api-2', '10.0.0.2', 8080, ttl=30)
    registry.register('db', 'db-1', '10.0.1.1', 5432, ttl=60)

    instances = registry.discover('api')
    print(f"API instances: {len(instances)}")
    for inst in instances:
        print(f"  {inst['instance_id']}: {inst['address']}:{inst['port']}")
