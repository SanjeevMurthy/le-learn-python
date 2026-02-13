"""
istio_config.py

Istio service mesh configuration management.

Prerequisites:
- subprocess (for kubectl)
"""

import subprocess
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_virtual_services(namespace: str = 'default') -> List[Dict[str, Any]]:
    """
    List Istio VirtualServices.

    Interview Question:
        Q: What is a service mesh and why use it?
        A: Service mesh: infrastructure layer for service-to-service communication.
           Components: data plane (sidecar proxies, e.g., Envoy) +
           control plane (Istio, Linkerd).
           Features: mTLS (zero-trust), traffic management (canary, retry),
           observability (traces, metrics without code changes),
           circuit breaking, rate limiting.
           When to use: many microservices, need for mTLS/observability,
           complex traffic routing. Adds latency and operational complexity.
    """
    result = subprocess.run(
        ['kubectl', 'get', 'virtualservices', '-n', namespace, '-o', 'json'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return []

    data = json.loads(result.stdout)
    return [
        {
            'name': item['metadata']['name'],
            'hosts': item['spec'].get('hosts', []),
            'gateways': item['spec'].get('gateways', []),
        }
        for item in data.get('items', [])
    ]


def generate_virtual_service(
    name: str,
    host: str,
    routes: List[Dict[str, Any]],
    namespace: str = 'default'
) -> Dict[str, Any]:
    """Generate a VirtualService YAML manifest."""
    http_routes = []
    for route in routes:
        http_route = {
            'route': [{
                'destination': {
                    'host': host,
                    'subset': route.get('subset', 'v1'),
                },
                'weight': route.get('weight', 100),
            }]
        }
        if route.get('match'):
            http_route['match'] = route['match']
        http_routes.append(http_route)

    return {
        'apiVersion': 'networking.istio.io/v1beta1',
        'kind': 'VirtualService',
        'metadata': {'name': name, 'namespace': namespace},
        'spec': {
            'hosts': [host],
            'http': http_routes,
        }
    }


if __name__ == "__main__":
    print("Istio Config — Usage Examples")
    vs = generate_virtual_service(
        'my-app-vs', 'my-app',
        routes=[
            {'subset': 'v1', 'weight': 90},
            {'subset': 'v2', 'weight': 10},
        ]
    )
    print(json.dumps(vs, indent=2))
