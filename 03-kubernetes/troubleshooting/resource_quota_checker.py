"""
resource_quota_checker.py

Check resource quota usage and identify namespaces nearing limits.

Interview Topics:
- ResourceQuota vs LimitRange
- Capacity planning in K8s
- Cluster resource management

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import logging
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_kube_config():
    from kubernetes import config
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def check_quota_usage(namespace: str = '') -> List[Dict[str, Any]]:
    """
    Check resource quota usage across namespaces.

    Interview Question:
        Q: ResourceQuota vs LimitRange — what's the difference?
        A: ResourceQuota: aggregate limits for a namespace
           (total CPU, memory, pod count across all pods).
           LimitRange: per-pod/container defaults and limits
           (default requests, max limits per container).
           Use together: LimitRange sets defaults, ResourceQuota
           caps the total. Without LimitRange, users must specify
           requests/limits on every pod when Quota is active.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    if namespace:
        quotas = v1.list_namespaced_resource_quota(namespace)
    else:
        quotas = v1.list_resource_quota_for_all_namespaces()

    results = []
    for quota in quotas.items:
        resources = {}
        for resource_name, hard_value in (quota.status.hard or {}).items():
            used_value = (quota.status.used or {}).get(resource_name, '0')
            resources[resource_name] = {
                'hard': hard_value,
                'used': used_value,
            }

        # Calculate usage percentage for numeric resources
        warnings = []
        for name, vals in resources.items():
            try:
                # Parse K8s quantities (simplified)
                hard = _parse_quantity(vals['hard'])
                used = _parse_quantity(vals['used'])
                if hard > 0:
                    pct = (used / hard) * 100
                    resources[name]['percent'] = round(pct, 1)
                    if pct > 80:
                        warnings.append(f"{name}: {pct:.0f}% used")
            except (ValueError, TypeError):
                pass

        results.append({
            'namespace': quota.metadata.namespace,
            'quota_name': quota.metadata.name,
            'resources': resources,
            'warnings': warnings,
        })

    return results


def _parse_quantity(value: str) -> float:
    """Parse K8s resource quantity string to a numeric value."""
    value = str(value)
    suffixes = {
        'Ki': 1024, 'Mi': 1024**2, 'Gi': 1024**3, 'Ti': 1024**4,
        'm': 0.001, 'k': 1000, 'M': 1e6, 'G': 1e9,
    }
    for suffix, multiplier in suffixes.items():
        if value.endswith(suffix):
            return float(value[:-len(suffix)]) * multiplier
    return float(value)


def find_over_committed_namespaces(threshold: float = 80.0) -> List[Dict[str, Any]]:
    """Find namespaces where quota usage exceeds a threshold."""
    all_quotas = check_quota_usage()
    over_committed = []

    for q in all_quotas:
        high_resources = [
            name for name, vals in q['resources'].items()
            if vals.get('percent', 0) > threshold
        ]
        if high_resources:
            over_committed.append({
                'namespace': q['namespace'],
                'high_usage': high_resources,
                'details': {
                    r: q['resources'][r] for r in high_resources
                },
            })

    logger.info(f"Found {len(over_committed)} namespaces over {threshold}% quota")
    return over_committed


if __name__ == "__main__":
    print("=" * 60)
    print("Resource Quota Checker — Usage Examples")
    print("=" * 60)
    print("""
    # Check all namespace quotas
    quotas = check_quota_usage()
    for q in quotas:
        print(f"  {q['namespace']}/{q['quota_name']}:")
        for name, vals in q['resources'].items():
            print(f"    {name}: {vals['used']}/{vals['hard']}")

    # Find over-committed namespaces
    for ns in find_over_committed_namespaces(threshold=80):
        print(f"  ⚠️ {ns['namespace']}: {ns['high_usage']}")
    """)
