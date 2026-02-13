"""
rolling_restart.py

Perform rolling restarts of K8s Deployments/StatefulSets.

Interview Topics:
- Why rolling restart instead of delete pods?
- PodDisruptionBudget and voluntary evictions
- Zero-downtime restart strategies

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

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


def rolling_restart_deployment(
    name: str,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """
    Trigger a rolling restart by patching the pod template annotation.

    This is equivalent to: kubectl rollout restart deployment/<name>

    Interview Question:
        Q: Why use rolling restart instead of deleting pods?
        A: Deleting pods causes immediate downtime until replacements
           are ready. Rolling restart respects: maxSurge/maxUnavailable
           (controlled rollout), PodDisruptionBudgets (minimum available),
           readiness probes (only route when ready), and creates a new
           ReplicaSet for rollback capability.
    """
    from kubernetes import client
    load_kube_config()
    apps_v1 = client.AppsV1Api()

    now = datetime.now(timezone.utc).isoformat()
    body = {
        'spec': {
            'template': {
                'metadata': {
                    'annotations': {
                        'kubectl.kubernetes.io/restartedAt': now
                    }
                }
            }
        }
    }

    try:
        apps_v1.patch_namespaced_deployment(name, namespace, body)
        logger.info(f"Rolling restart initiated: {namespace}/{name}")
        return {'name': name, 'namespace': namespace, 'status': 'restarting'}
    except Exception as e:
        logger.error(f"Rolling restart failed: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def rolling_restart_by_label(
    label_selector: str,
    namespace: str = 'default'
) -> List[Dict[str, Any]]:
    """Restart all deployments matching a label selector."""
    from kubernetes import client
    load_kube_config()
    apps_v1 = client.AppsV1Api()

    deployments = apps_v1.list_namespaced_deployment(
        namespace, label_selector=label_selector
    )

    results = []
    for dep in deployments.items:
        result = rolling_restart_deployment(dep.metadata.name, namespace)
        results.append(result)

    logger.info(f"Restarted {len(results)} deployments matching '{label_selector}'")
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Rolling Restart — Usage Examples")
    print("=" * 60)
    print("""
    # Restart a single deployment
    rolling_restart_deployment('web-app', 'production')

    # Restart all deployments with a label
    rolling_restart_by_label('app.kubernetes.io/part-of=myapp', 'production')
    """)
