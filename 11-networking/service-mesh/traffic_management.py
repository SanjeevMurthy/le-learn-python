"""
traffic_management.py

Istio traffic management: canary, mirroring, fault injection.

Prerequisites:
- subprocess (for kubectl)
"""

import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_canary_routing(
    name: str, host: str,
    stable_version: str = 'v1', stable_weight: int = 90,
    canary_version: str = 'v2', canary_weight: int = 10,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """
    Generate canary traffic routing.

    Interview Question:
        Q: How does Istio enable traffic management?
        A: VirtualService: routing rules (weight, match, retry, timeout).
           DestinationRule: subsets (versions), circuit breaker, TLS.
           Gateway: ingress/egress traffic management.
           ServiceEntry: external services in the mesh.
           Traffic splitting: 90/10 canary by weight.
           Header-based routing: internal users see new version.
           Traffic mirroring: copy live traffic to new version for testing.
    """
    return {
        'apiVersion': 'networking.istio.io/v1beta1',
        'kind': 'VirtualService',
        'metadata': {'name': name, 'namespace': namespace},
        'spec': {
            'hosts': [host],
            'http': [{
                'route': [
                    {'destination': {'host': host, 'subset': stable_version}, 'weight': stable_weight},
                    {'destination': {'host': host, 'subset': canary_version}, 'weight': canary_weight},
                ]
            }]
        }
    }


def generate_fault_injection(
    name: str, host: str,
    delay_percent: int = 10, delay_seconds: int = 5,
    abort_percent: int = 5, abort_code: int = 503,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """Generate fault injection config for chaos testing."""
    return {
        'apiVersion': 'networking.istio.io/v1beta1',
        'kind': 'VirtualService',
        'metadata': {'name': name, 'namespace': namespace},
        'spec': {
            'hosts': [host],
            'http': [{
                'fault': {
                    'delay': {
                        'percentage': {'value': delay_percent},
                        'fixedDelay': f'{delay_seconds}s',
                    },
                    'abort': {
                        'percentage': {'value': abort_percent},
                        'httpStatus': abort_code,
                    }
                },
                'route': [{'destination': {'host': host}}]
            }]
        }
    }


def generate_traffic_mirror(
    name: str, host: str, mirror_host: str,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """Generate traffic mirroring config."""
    return {
        'apiVersion': 'networking.istio.io/v1beta1',
        'kind': 'VirtualService',
        'metadata': {'name': name, 'namespace': namespace},
        'spec': {
            'hosts': [host],
            'http': [{
                'route': [{'destination': {'host': host}}],
                'mirror': {'host': mirror_host},
                'mirrorPercentage': {'value': 100},
            }]
        }
    }


if __name__ == "__main__":
    print("Traffic Management — Canary 90/10:")
    print(json.dumps(generate_canary_routing('my-app', 'my-app'), indent=2))
