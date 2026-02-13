"""
namespace_operations.py

Kubernetes Namespace management.

Interview Topics:
- Namespace isolation and multi-tenancy
- Resource quotas per namespace
- Network policies for namespace isolation

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import logging
from typing import List, Dict, Any, Optional

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


def list_namespaces(label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all namespaces.

    Interview Question:
        Q: How do you implement multi-tenancy in K8s?
        A: 1. Namespace per tenant/team/environment
           2. ResourceQuotas to limit CPU/memory/object counts
           3. LimitRanges for default container limits
           4. NetworkPolicies to isolate namespace traffic
           5. RBAC RoleBindings scoped to namespaces
           6. Consider namespace-level Pod Security Standards
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    kwargs = {}
    if label_selector:
        kwargs['label_selector'] = label_selector

    namespaces = v1.list_namespace(**kwargs)

    result = []
    for ns in namespaces.items:
        result.append({
            'name': ns.metadata.name,
            'status': ns.status.phase,
            'labels': dict(ns.metadata.labels or {}),
            'created': ns.metadata.creation_timestamp.isoformat(),
        })

    logger.info(f"Found {len(result)} namespaces")
    return result


def create_namespace(
    name: str,
    labels: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a namespace with optional labels."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    ns = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name=name,
            labels=labels or {'managed-by': 'devops-toolkit'},
        ),
    )

    try:
        v1.create_namespace(ns)
        logger.info(f"Created namespace: {name}")
        return {'name': name, 'status': 'created'}
    except Exception as e:
        logger.error(f"Failed to create namespace: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def set_resource_quota(
    namespace: str,
    cpu_limit: str = '4',
    memory_limit: str = '8Gi',
    pod_limit: int = 20
) -> Dict[str, Any]:
    """
    Set a ResourceQuota on a namespace.

    Interview Question:
        Q: What happens when a ResourceQuota is exceeded?
        A: New pod/resource creation is rejected by the API server
           with a 403 Forbidden. Existing pods are NOT affected.
           Quotas cover: compute (cpu, memory), object counts
           (pods, services, configmaps), storage (PVCs).
           Always pair with LimitRange for default container limits.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    quota = client.V1ResourceQuota(
        metadata=client.V1ObjectMeta(name=f'{namespace}-quota'),
        spec=client.V1ResourceQuotaSpec(
            hard={
                'requests.cpu': cpu_limit,
                'requests.memory': memory_limit,
                'limits.cpu': str(int(cpu_limit) * 2) if cpu_limit.isdigit() else cpu_limit,
                'limits.memory': memory_limit.replace('Gi', '') + 'Gi',
                'pods': str(pod_limit),
            }
        ),
    )

    try:
        v1.create_namespaced_resource_quota(namespace, quota)
        logger.info(f"Set quota for {namespace}: {cpu_limit} CPU, {memory_limit} mem, {pod_limit} pods")
        return {'namespace': namespace, 'status': 'quota_set'}
    except Exception as e:
        logger.error(f"Quota creation failed: {e}")
        return {'namespace': namespace, 'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("Namespace Operations — Usage Examples")
    print("=" * 60)
    print("""
    # List namespaces
    for ns in list_namespaces():
        print(f"  {ns['name']}: {ns['status']}")

    # Create namespace with quota
    create_namespace('dev-team-a', labels={'team': 'a', 'env': 'dev'})
    set_resource_quota('dev-team-a', cpu_limit='4', memory_limit='8Gi')
    """)
