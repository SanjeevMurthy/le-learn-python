"""
scale_deployments.py

Programmatic scaling of K8s Deployments and StatefulSets.

Interview Topics:
- Horizontal Pod Autoscaler (HPA) vs manual scaling
- Vertical Pod Autoscaler (VPA)
- Scaling strategies for different workload types

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


def scale_deployment(
    name: str,
    replicas: int,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """
    Scale a deployment to a target replica count.

    Interview Question:
        Q: How does HPA work?
        A: HPA controller loop (every 15s default):
           1. Queries metrics (CPU, memory, or custom)
           2. Calculates desired replicas:
              desired = ceil(current * (currentMetric / targetMetric))
           3. Scales deployment if outside tolerance (10%)
           Key settings: minReplicas, maxReplicas, stabilization
           window (prevents flapping). HPA cannot scale to 0 —
           use KEDA for scale-to-zero.
    """
    from kubernetes import client
    load_kube_config()
    apps_v1 = client.AppsV1Api()

    try:
        current = apps_v1.read_namespaced_deployment(name, namespace)
        old_replicas = current.spec.replicas

        body = {'spec': {'replicas': replicas}}
        apps_v1.patch_namespaced_deployment_scale(name, namespace, body)

        logger.info(f"Scaled {name}: {old_replicas} → {replicas}")
        return {
            'name': name, 'old_replicas': old_replicas,
            'new_replicas': replicas, 'status': 'scaled'
        }
    except Exception as e:
        logger.error(f"Scale failed: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def scale_by_label(
    label_selector: str,
    replicas: int,
    namespace: str = 'default'
) -> List[Dict[str, Any]]:
    """Scale all deployments matching a label selector."""
    from kubernetes import client
    load_kube_config()
    apps_v1 = client.AppsV1Api()

    deployments = apps_v1.list_namespaced_deployment(
        namespace, label_selector=label_selector
    )

    results = []
    for dep in deployments.items:
        result = scale_deployment(dep.metadata.name, replicas, namespace)
        results.append(result)

    return results


def scale_down_non_prod(
    prod_namespaces: Optional[List[str]] = None,
    min_replicas: int = 0
) -> List[Dict[str, Any]]:
    """
    Scale down all deployments in non-production namespaces.
    Useful for cost savings during off-hours.

    Interview Question:
        Q: How would you reduce K8s costs during off-hours?
        A: 1. Scale deployments to 0 in dev/staging (scheduled)
           2. Use Cluster Autoscaler to scale down empty nodes
           3. Use Spot/preemptible nodes for non-critical workloads
           4. VPA to right-size pod resource requests
           5. Karpenter (AWS) for just-in-time node provisioning
    """
    from kubernetes import client
    load_kube_config()
    apps_v1 = client.AppsV1Api()
    v1 = client.CoreV1Api()

    prod = prod_namespaces or ['production', 'kube-system', 'kube-public']
    system_ns = {'kube-system', 'kube-public', 'kube-node-lease'}

    results = []
    namespaces = v1.list_namespace()
    for ns in namespaces.items:
        ns_name = ns.metadata.name
        if ns_name in prod or ns_name in system_ns:
            continue

        deployments = apps_v1.list_namespaced_deployment(ns_name)
        for dep in deployments.items:
            if dep.spec.replicas > min_replicas:
                result = scale_deployment(dep.metadata.name, min_replicas, ns_name)
                results.append(result)

    logger.info(f"Scaled down {len(results)} deployments in non-prod namespaces")
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Scale Deployments — Usage Examples")
    print("=" * 60)
    print("""
    # Scale single deployment
    scale_deployment('web-app', 5, 'production')

    # Scale by label
    scale_by_label('tier=frontend', 3, 'staging')

    # Off-hours cost savings
    scale_down_non_prod(prod_namespaces=['production'])
    """)
