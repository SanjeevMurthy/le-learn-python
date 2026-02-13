"""
resource_usage_monitor.py

Monitor CPU and memory usage across pods and nodes.

Interview Topics:
- Metrics Server vs Prometheus
- Resource requests vs actual usage
- Vertical Pod Autoscaler recommendations

Prerequisites:
- kubernetes (pip install kubernetes)
- Metrics Server or Prometheus installed in cluster
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


def get_node_resource_usage() -> List[Dict[str, Any]]:
    """
    Get resource usage per node (requires Metrics Server).

    Interview Question:
        Q: How does the Metrics Server work?
        A: Metrics Server collects resource metrics from kubelets
           (via Summary API). Stores in memory (not persistent).
           Used by HPA, VPA, and kubectl top. NOT for monitoring —
           use Prometheus for that. Metrics Server is a cluster addon,
           scrapes every 15s, lightweight (<100MB memory).
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()
    custom = client.CustomObjectsApi()

    # Get node capacity
    nodes = v1.list_node()
    node_capacity = {}
    for node in nodes.items:
        node_capacity[node.metadata.name] = {
            'cpu_capacity': node.status.capacity.get('cpu', '0'),
            'memory_capacity': node.status.capacity.get('memory', '0'),
        }

    # Get node metrics from metrics.k8s.io
    try:
        metrics = custom.list_cluster_custom_object(
            'metrics.k8s.io', 'v1beta1', 'nodes'
        )
    except Exception as e:
        logger.warning(f"Metrics Server not available: {e}")
        return []

    result = []
    for item in metrics.get('items', []):
        name = item['metadata']['name']
        cpu_usage = item['usage'].get('cpu', '0')
        mem_usage = item['usage'].get('memory', '0')

        result.append({
            'node': name,
            'cpu_usage': cpu_usage,
            'cpu_capacity': node_capacity.get(name, {}).get('cpu_capacity', '?'),
            'memory_usage': mem_usage,
            'memory_capacity': node_capacity.get(name, {}).get('memory_capacity', '?'),
        })

    logger.info(f"Got resource usage for {len(result)} nodes")
    return result


def get_pod_resource_usage(namespace: str = 'default') -> List[Dict[str, Any]]:
    """Get resource usage per pod (requires Metrics Server)."""
    from kubernetes import client
    load_kube_config()
    custom = client.CustomObjectsApi()

    try:
        metrics = custom.list_namespaced_custom_object(
            'metrics.k8s.io', 'v1beta1', namespace, 'pods'
        )
    except Exception as e:
        logger.warning(f"Metrics Server not available: {e}")
        return []

    result = []
    for item in metrics.get('items', []):
        containers = []
        for c in item.get('containers', []):
            containers.append({
                'name': c['name'],
                'cpu': c['usage'].get('cpu', '0'),
                'memory': c['usage'].get('memory', '0'),
            })

        result.append({
            'pod': item['metadata']['name'],
            'namespace': namespace,
            'containers': containers,
        })

    logger.info(f"Got resource usage for {len(result)} pods in {namespace}")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Resource Usage Monitor — Usage Examples")
    print("=" * 60)
    print("""
    # Node resource usage
    for node in get_node_resource_usage():
        print(f"  {node['node']}: CPU={node['cpu_usage']}, Mem={node['memory_usage']}")

    # Pod resource usage
    for pod in get_pod_resource_usage('kube-system'):
        print(f"  {pod['pod']}:")
        for c in pod['containers']:
            print(f"    {c['name']}: cpu={c['cpu']}, mem={c['memory']}")
    """)
