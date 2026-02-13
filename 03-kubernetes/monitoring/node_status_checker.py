"""
node_status_checker.py

Kubernetes node health and status monitoring.

Interview Topics:
- Node conditions (Ready, MemoryPressure, DiskPressure, PIDPressure)
- Node cordoning and draining
- Taints and tolerations

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


def check_node_status() -> Dict[str, Any]:
    """
    Check status of all cluster nodes.

    Interview Question:
        Q: What are node conditions and what do they mean?
        A: Ready: kubelet is healthy and can accept pods.
           MemoryPressure: node memory is low → eviction starts.
           DiskPressure: disk space or inodes low → eviction.
           PIDPressure: too many processes → can't create new.
           NetworkUnavailable: node network not configured.
           If Ready=False for >pod-eviction-timeout (5m default),
           controller marks pods for eviction.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    nodes = v1.list_node()
    healthy_nodes = []
    unhealthy_nodes = []

    for node in nodes.items:
        conditions = {}
        for cond in (node.status.conditions or []):
            conditions[cond.type] = {
                'status': cond.status,
                'reason': cond.reason,
                'message': cond.message,
            }

        is_ready = conditions.get('Ready', {}).get('status') == 'True'
        has_pressure = any(
            conditions.get(c, {}).get('status') == 'True'
            for c in ['MemoryPressure', 'DiskPressure', 'PIDPressure']
        )

        taints = [
            {'key': t.key, 'effect': t.effect, 'value': t.value}
            for t in (node.spec.taints or [])
        ]

        node_info = {
            'name': node.metadata.name,
            'ready': is_ready,
            'conditions': conditions,
            'taints': taints,
            'unschedulable': node.spec.unschedulable or False,
            'kubelet_version': node.status.node_info.kubelet_version,
            'os': node.status.node_info.operating_system,
            'capacity': {
                'cpu': node.status.capacity.get('cpu', '0'),
                'memory': node.status.capacity.get('memory', '0'),
                'pods': node.status.capacity.get('pods', '0'),
            },
        }

        if is_ready and not has_pressure:
            healthy_nodes.append(node_info)
        else:
            unhealthy_nodes.append(node_info)

    report = {
        'total_nodes': len(nodes.items),
        'healthy': len(healthy_nodes),
        'unhealthy': len(unhealthy_nodes),
        'unhealthy_nodes': unhealthy_nodes,
        'all_nodes': healthy_nodes + unhealthy_nodes,
    }

    logger.info(f"Node status: {report['healthy']}/{report['total_nodes']} healthy")
    return report


if __name__ == "__main__":
    print("=" * 60)
    print("Node Status Checker — Usage Examples")
    print("=" * 60)
    print("""
    report = check_node_status()
    print(f"  Healthy: {report['healthy']}/{report['total_nodes']}")
    for n in report['unhealthy_nodes']:
        print(f"  ⚠️ {n['name']}: ready={n['ready']}")
    """)
