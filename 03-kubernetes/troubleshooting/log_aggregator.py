"""
log_aggregator.py

Aggregate logs from multiple pods/containers for troubleshooting.

Interview Topics:
- Centralized logging architectures (EFK, Loki)
- Log aggregation strategies
- Structured logging in K8s

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def aggregate_logs(
    label_selector: str,
    namespace: str = 'default',
    tail_lines: int = 50,
    since_seconds: Optional[int] = None,
    grep_pattern: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Aggregate logs from all pods matching a label selector.

    Interview Question:
        Q: Design a logging architecture for K8s.
        A: Common patterns:
           1. Node-level agent (DaemonSet): Fluentd/Fluent Bit
              on each node, reads /var/log/containers/*
           2. Sidecar: logging container per pod (resource-heavy)
           3. Direct push: app sends to logging backend
           Best practice: structured JSON logs → Fluent Bit DaemonSet
           → Elasticsearch/Loki → Kibana/Grafana for visualization.
           Always include: timestamp, level, request ID, service name.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod(namespace, label_selector=label_selector)

    def get_pod_logs(pod):
        """Fetch logs from a single pod (all containers)."""
        results = []
        for container in pod.spec.containers:
            try:
                kwargs = {
                    'container': container.name,
                    'tail_lines': tail_lines,
                }
                if since_seconds:
                    kwargs['since_seconds'] = since_seconds

                logs = v1.read_namespaced_pod_log(
                    pod.metadata.name, namespace, **kwargs
                )

                lines = logs.split('\n') if logs else []
                if grep_pattern:
                    lines = [l for l in lines if grep_pattern in l]

                results.append({
                    'pod': pod.metadata.name,
                    'container': container.name,
                    'lines': lines,
                    'line_count': len(lines),
                })
            except Exception as e:
                results.append({
                    'pod': pod.metadata.name,
                    'container': container.name,
                    'error': str(e),
                    'lines': [],
                    'line_count': 0,
                })
        return results

    # Fetch logs in parallel
    all_logs = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_pod_logs, pod): pod for pod in pods.items}
        for future in as_completed(futures):
            all_logs.extend(future.result())

    logger.info(
        f"Aggregated logs from {len(all_logs)} containers "
        f"({sum(l['line_count'] for l in all_logs)} total lines)"
    )
    return all_logs


def search_logs(
    pattern: str,
    namespace: str = '',
    label_selector: Optional[str] = None,
    tail_lines: int = 100
) -> List[Dict[str, Any]]:
    """Search for a pattern across all pod logs."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    if namespace:
        pods = v1.list_namespaced_pod(
            namespace, label_selector=label_selector or ''
        )
    else:
        pods = v1.list_pod_for_all_namespaces(
            label_selector=label_selector or ''
        )

    matches = []
    for pod in pods.items:
        for container in pod.spec.containers:
            try:
                logs = v1.read_namespaced_pod_log(
                    pod.metadata.name, pod.metadata.namespace,
                    container=container.name, tail_lines=tail_lines,
                )
                matching_lines = [
                    line for line in (logs or '').split('\n')
                    if pattern in line
                ]
                if matching_lines:
                    matches.append({
                        'pod': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'container': container.name,
                        'matching_lines': matching_lines,
                    })
            except Exception:
                pass

    return matches


if __name__ == "__main__":
    print("=" * 60)
    print("Log Aggregator — Usage Examples")
    print("=" * 60)
    print("""
    # Aggregate logs from all pods with a label
    logs = aggregate_logs('app=web', 'production', tail_lines=50)
    for l in logs:
        print(f"  {l['pod']}/{l['container']}: {l['line_count']} lines")

    # Search for errors across all pods
    matches = search_logs('ERROR', namespace='production')
    for m in matches:
        print(f"  {m['pod']}: {len(m['matching_lines'])} matches")
    """)
