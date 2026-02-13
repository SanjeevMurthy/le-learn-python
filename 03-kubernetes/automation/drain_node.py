"""
drain_node.py

Safely drain a Kubernetes node for maintenance.

Interview Topics:
- Cordon vs Drain vs Delete node
- PodDisruptionBudgets (PDB) during drain
- Node maintenance procedures

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import time
import logging
from typing import Dict, Any, List

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


def cordon_node(node_name: str) -> Dict[str, Any]:
    """
    Mark a node as unschedulable (cordon).

    Interview Question:
        Q: Cordon vs Drain — what's the difference?
        A: Cordon: marks node unschedulable. Existing pods keep running.
           No new pods will be scheduled on this node.
           Drain: cordons PLUS evicts all pods (respecting PDBs).
           Pods are rescheduled to other nodes.
           Use cordon when you want to stop new scheduling but
           keep existing workloads running temporarily.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        body = {'spec': {'unschedulable': True}}
        v1.patch_node(node_name, body)
        logger.info(f"Cordoned node: {node_name}")
        return {'node': node_name, 'status': 'cordoned'}
    except Exception as e:
        logger.error(f"Cordon failed: {e}")
        return {'node': node_name, 'status': 'error', 'error': str(e)}


def uncordon_node(node_name: str) -> Dict[str, Any]:
    """Mark a node as schedulable again."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        body = {'spec': {'unschedulable': False}}
        v1.patch_node(node_name, body)
        logger.info(f"Uncordoned node: {node_name}")
        return {'node': node_name, 'status': 'uncordoned'}
    except Exception as e:
        logger.error(f"Uncordon failed: {e}")
        return {'node': node_name, 'status': 'error', 'error': str(e)}


def drain_node(
    node_name: str,
    grace_period: int = 30,
    ignore_daemonsets: bool = True,
    delete_local_data: bool = False,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Safely drain a node by evicting all pods.

    Interview Question:
        Q: What happens when a pod can't be evicted during drain?
        A: If a PDB prevents eviction (would violate minAvailable),
           drain blocks until PDB allows it or timeout. DaemonSet
           pods are skipped (--ignore-daemonsets). Pods with local
           storage need --delete-emptydir-data flag. Static pods
           (mirror pods) can't be evicted — they're managed by
           kubelet directly.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    # Step 1: Cordon the node
    cordon_result = cordon_node(node_name)
    if cordon_result.get('status') == 'error':
        return cordon_result

    # Step 2: Get pods on the node
    pods = v1.list_pod_for_all_namespaces(
        field_selector=f'spec.nodeName={node_name}'
    )

    evicted = []
    skipped = []
    errors = []

    for pod in pods.items:
        # Skip DaemonSet pods if configured
        if ignore_daemonsets:
            owner_refs = pod.metadata.owner_references or []
            if any(ref.kind == 'DaemonSet' for ref in owner_refs):
                skipped.append(f"{pod.metadata.namespace}/{pod.metadata.name}")
                continue

        # Skip mirror pods (static pods)
        annotations = pod.metadata.annotations or {}
        if 'kubernetes.io/config.mirror' in annotations:
            skipped.append(f"{pod.metadata.namespace}/{pod.metadata.name}")
            continue

        # Evict the pod
        try:
            eviction = client.V1Eviction(
                metadata=client.V1ObjectMeta(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                ),
                delete_options=client.V1DeleteOptions(
                    grace_period_seconds=grace_period
                ),
            )
            v1.create_namespaced_pod_eviction(
                pod.metadata.name, pod.metadata.namespace, eviction
            )
            evicted.append(f"{pod.metadata.namespace}/{pod.metadata.name}")
        except Exception as e:
            errors.append({
                'pod': f"{pod.metadata.namespace}/{pod.metadata.name}",
                'error': str(e)
            })

    logger.info(
        f"Drain {node_name}: evicted={len(evicted)}, "
        f"skipped={len(skipped)}, errors={len(errors)}"
    )

    return {
        'node': node_name,
        'evicted': len(evicted),
        'skipped': len(skipped),
        'errors': errors,
        'status': 'drained' if not errors else 'partial',
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Drain Node — Usage Examples")
    print("=" * 60)
    print("""
    # Cordon a node (stop scheduling)
    cordon_node('worker-node-01')

    # Drain a node (evict all pods)
    result = drain_node('worker-node-01', grace_period=30)
    print(f"  Evicted: {result['evicted']}, Errors: {len(result['errors'])}")

    # After maintenance, uncordon
    uncordon_node('worker-node-01')
    """)
