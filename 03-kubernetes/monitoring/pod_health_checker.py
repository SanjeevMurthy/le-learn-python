"""
pod_health_checker.py

Pod health monitoring — identify unhealthy, crash-looping, and pending pods.

Interview Topics:
- Readiness vs liveness vs startup probes
- CrashLoopBackOff diagnosis
- Pod eviction and OOMKilled

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


def check_pod_health(namespace: str = '') -> Dict[str, Any]:
    """
    Check health of all pods and categorize issues.

    Interview Question:
        Q: Explain readiness vs liveness vs startup probes.
        A: Liveness: is the container alive? Failure → restart.
           Use for deadlock detection.
           Readiness: is the container ready for traffic? Failure
           → remove from Service endpoints. Use for warm-up.
           Startup: has the container started? Failure → restart.
           Use for slow-starting apps (prevents liveness from
           killing during startup). Startup disables liveness/readiness
           until it succeeds.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    if namespace:
        pods = v1.list_namespaced_pod(namespace)
    else:
        pods = v1.list_pod_for_all_namespaces()

    healthy = []
    unhealthy = []
    crash_looping = []
    pending = []

    for pod in pods.items:
        pod_info = {
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'phase': pod.status.phase,
            'node': pod.spec.node_name,
        }

        if pod.status.phase == 'Pending':
            # Check why pending
            conditions = pod.status.conditions or []
            reasons = [c.reason for c in conditions if c.status == 'False']
            pod_info['reasons'] = reasons
            pending.append(pod_info)
            continue

        # Check container statuses
        containers = pod.status.container_statuses or []
        total_restarts = sum(cs.restart_count for cs in containers)
        all_ready = all(cs.ready for cs in containers)

        pod_info['restarts'] = total_restarts

        if total_restarts > 5:
            # Likely CrashLoopBackOff
            waiting_reasons = []
            for cs in containers:
                if cs.state.waiting:
                    waiting_reasons.append(cs.state.waiting.reason)
            pod_info['waiting_reasons'] = waiting_reasons
            crash_looping.append(pod_info)
        elif not all_ready or pod.status.phase != 'Running':
            unhealthy.append(pod_info)
        else:
            healthy.append(pod_info)

    report = {
        'total': len(healthy) + len(unhealthy) + len(crash_looping) + len(pending),
        'healthy': len(healthy),
        'unhealthy': len(unhealthy),
        'crash_looping': len(crash_looping),
        'pending': len(pending),
        'unhealthy_pods': unhealthy,
        'crash_looping_pods': crash_looping,
        'pending_pods': pending,
    }

    logger.info(
        f"Pod health: {report['healthy']} healthy, "
        f"{report['unhealthy']} unhealthy, "
        f"{report['crash_looping']} crash-looping, "
        f"{report['pending']} pending"
    )
    return report


if __name__ == "__main__":
    print("=" * 60)
    print("Pod Health Checker — Usage Examples")
    print("=" * 60)
    print("""
    # Check all namespaces
    report = check_pod_health()
    print(f"  Healthy: {report['healthy']}, Unhealthy: {report['unhealthy']}")
    for p in report['crash_looping_pods']:
        print(f"  ⚠️ {p['namespace']}/{p['name']}: {p['restarts']} restarts")

    # Check specific namespace
    report = check_pod_health('production')
    """)
