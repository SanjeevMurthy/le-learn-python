"""
pod_management.py

Kubernetes Pod management using the official Python client.

Interview Topics:
- Pod lifecycle states (Pending, Running, Succeeded, Failed, Unknown)
- Init containers vs sidecar containers
- Pod restart policies (Always, OnFailure, Never)

Production Use Cases:
- Listing and filtering pods across namespaces
- Creating pods for ad-hoc tasks (debug, migration, testing)
- Deleting pods for remediation
- Waiting for pod readiness

Prerequisites:
- kubernetes (pip install kubernetes)
- kubectl configured (~/.kube/config)
"""

import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_kube_config():
    """
    Load Kubernetes configuration.

    Tries in-cluster config first (for pods), then kubeconfig file.
    """
    from kubernetes import config
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster K8s config")
    except config.ConfigException:
        config.load_kube_config()
        logger.info("Loaded kubeconfig from ~/.kube/config")


def list_pods(
    namespace: str = 'default',
    label_selector: Optional[str] = None,
    field_selector: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List pods in a namespace with optional filtering.

    Args:
        namespace: K8s namespace (use '' for all namespaces)
        label_selector: Label filter (e.g., 'app=nginx,env=prod')
        field_selector: Field filter (e.g., 'status.phase=Running')

    Returns:
        List of pod details

    Interview Question:
        Q: Explain the Pod lifecycle phases.
        A: Pending: scheduled but containers not running yet
           (pulling images, init containers running).
           Running: at least one container is running.
           Succeeded: all containers exited with code 0.
           Failed: at least one container exited with non-zero.
           Unknown: node communication lost.
           Key: phase != readiness. A Running pod may not be
           ready to serve traffic (readiness probe failing).
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    kwargs = {}
    if label_selector:
        kwargs['label_selector'] = label_selector
    if field_selector:
        kwargs['field_selector'] = field_selector

    if namespace:
        pods = v1.list_namespaced_pod(namespace, **kwargs)
    else:
        pods = v1.list_pod_for_all_namespaces(**kwargs)

    result = []
    for pod in pods.items:
        containers = []
        for cs in (pod.status.container_statuses or []):
            containers.append({
                'name': cs.name,
                'ready': cs.ready,
                'restarts': cs.restart_count,
                'state': (
                    'running' if cs.state.running else
                    'waiting' if cs.state.waiting else
                    'terminated' if cs.state.terminated else 'unknown'
                ),
            })

        result.append({
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'phase': pod.status.phase,
            'node': pod.spec.node_name,
            'ip': pod.status.pod_ip,
            'containers': containers,
            'labels': dict(pod.metadata.labels or {}),
            'created': pod.metadata.creation_timestamp.isoformat(),
        })

    logger.info(f"Found {len(result)} pods in namespace '{namespace}'")
    return result


def create_pod(
    name: str,
    image: str,
    namespace: str = 'default',
    command: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    cpu_request: str = '100m',
    memory_request: str = '128Mi'
) -> Dict[str, Any]:
    """
    Create a pod with resource requests.

    Interview Question:
        Q: What are resource requests vs limits?
        A: Requests: minimum guaranteed resources. Used by scheduler
           for placement decisions. Limits: maximum resources allowed.
           Exceeding CPU limit → throttling. Exceeding memory limit
           → OOMKilled. Best practice: always set both.
           requests <= limits. QoS classes:
           Guaranteed (requests == limits), Burstable (requests < limits),
           BestEffort (no requests/limits — evicted first).
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    # Build container spec
    container = client.V1Container(
        name=name,
        image=image,
        command=command,
        resources=client.V1ResourceRequirements(
            requests={'cpu': cpu_request, 'memory': memory_request}
        ),
    )

    if env_vars:
        container.env = [
            client.V1EnvVar(name=k, value=v)
            for k, v in env_vars.items()
        ]

    pod_spec = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            labels=labels or {'app': name, 'managed-by': 'devops-toolkit'},
        ),
        spec=client.V1PodSpec(
            containers=[container],
            restart_policy='Never',  # For ad-hoc tasks
        ),
    )

    try:
        result = v1.create_namespaced_pod(namespace, pod_spec)
        logger.info(f"Created pod: {name} in {namespace}")
        return {
            'name': result.metadata.name,
            'namespace': namespace,
            'status': 'created',
        }
    except Exception as e:
        logger.error(f"Failed to create pod: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def delete_pod(
    name: str,
    namespace: str = 'default',
    grace_period: int = 30
) -> Dict[str, Any]:
    """Delete a pod with grace period."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        v1.delete_namespaced_pod(
            name, namespace,
            body=client.V1DeleteOptions(grace_period_seconds=grace_period)
        )
        logger.info(f"Deleted pod: {name} (grace: {grace_period}s)")
        return {'name': name, 'status': 'deleted'}
    except Exception as e:
        logger.error(f"Failed to delete pod: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def get_pod_logs(
    name: str,
    namespace: str = 'default',
    container: Optional[str] = None,
    tail_lines: int = 100,
    previous: bool = False
) -> str:
    """
    Get logs from a pod's container.

    Args:
        previous: If True, get logs from previous container instance
                  (useful for crashed/restarted containers)
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        logs = v1.read_namespaced_pod_log(
            name, namespace,
            container=container,
            tail_lines=tail_lines,
            previous=previous,
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return f"Error: {e}"


if __name__ == "__main__":
    print("=" * 60)
    print("Pod Management — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires kubectl configured (~/.kube/config).

    # List all running pods
    pods = list_pods('default', field_selector='status.phase=Running')
    for p in pods:
        print(f"  {p['name']}: {p['phase']} on {p['node']}")

    # Create a debug pod
    create_pod('debug-pod', 'busybox', command=['sleep', '3600'])

    # Get pod logs
    logs = get_pod_logs('my-app-pod', tail_lines=50)
    """)
