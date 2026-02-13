"""
pod_diagnostics.py

Kubernetes pod troubleshooting and diagnostics.

Interview Topics:
- CrashLoopBackOff debugging
- OOMKilled root cause analysis
- ImagePullBackOff troubleshooting

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


def diagnose_pod(name: str, namespace: str = 'default') -> Dict[str, Any]:
    """
    Run comprehensive diagnostics on a pod.

    Interview Question:
        Q: Walk through debugging a CrashLoopBackOff pod.
        A: 1. kubectl describe pod <name> → check Events section
           2. kubectl logs <name> → check application logs
           3. kubectl logs <name> --previous → logs from crashed container
           4. Check exit code: 137=OOMKilled, 1=app error, 126=permission
           5. Check resource limits (OOMKilled if memory exceeded)
           6. Check readiness/liveness probe config
           7. Check volume mounts and ConfigMap/Secret refs
           8. kubectl exec debug pod for live investigation
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        pod = v1.read_namespaced_pod(name, namespace)
    except Exception as e:
        return {'name': name, 'status': 'not_found', 'error': str(e)}

    diagnosis = {
        'name': name,
        'namespace': namespace,
        'phase': pod.status.phase,
        'node': pod.spec.node_name,
        'issues': [],
        'containers': [],
    }

    # Check conditions
    for cond in (pod.status.conditions or []):
        if cond.status == 'False':
            diagnosis['issues'].append({
                'type': cond.type,
                'reason': cond.reason,
                'message': cond.message,
            })

    # Check each container
    for cs in (pod.status.container_statuses or []):
        container_info = {
            'name': cs.name,
            'ready': cs.ready,
            'restarts': cs.restart_count,
        }

        if cs.state.waiting:
            container_info['state'] = 'waiting'
            container_info['reason'] = cs.state.waiting.reason
            container_info['message'] = cs.state.waiting.message

            if cs.state.waiting.reason == 'CrashLoopBackOff':
                diagnosis['issues'].append({
                    'type': 'CrashLoopBackOff',
                    'container': cs.name,
                    'restarts': cs.restart_count,
                    'fix': 'Check logs with: kubectl logs --previous',
                })
            elif cs.state.waiting.reason in ('ImagePullBackOff', 'ErrImagePull'):
                diagnosis['issues'].append({
                    'type': 'ImagePullError',
                    'container': cs.name,
                    'fix': 'Check image name, tag, and registry credentials',
                })

        elif cs.state.terminated:
            container_info['state'] = 'terminated'
            container_info['exit_code'] = cs.state.terminated.exit_code
            container_info['reason'] = cs.state.terminated.reason

            if cs.state.terminated.exit_code == 137:
                diagnosis['issues'].append({
                    'type': 'OOMKilled',
                    'container': cs.name,
                    'fix': 'Increase memory limits or optimize app memory usage',
                })
        else:
            container_info['state'] = 'running'

        diagnosis['containers'].append(container_info)

    # Get recent events
    events = v1.list_namespaced_event(
        namespace,
        field_selector=f'involvedObject.name={name}'
    )
    diagnosis['recent_events'] = [
        {
            'reason': e.reason,
            'message': e.message,
            'type': e.type,
            'count': e.count,
        }
        for e in events.items[-10:]
    ]

    return diagnosis


def find_problem_pods(namespace: str = '') -> List[Dict[str, Any]]:
    """Find all pods with issues across namespaces."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    if namespace:
        pods = v1.list_namespaced_pod(namespace)
    else:
        pods = v1.list_pod_for_all_namespaces()

    problems = []
    for pod in pods.items:
        has_issue = False
        issues = []

        if pod.status.phase in ('Failed', 'Unknown'):
            has_issue = True
            issues.append(f"Phase: {pod.status.phase}")

        for cs in (pod.status.container_statuses or []):
            if cs.restart_count > 3:
                has_issue = True
                issues.append(f"{cs.name}: {cs.restart_count} restarts")
            if cs.state.waiting and cs.state.waiting.reason:
                has_issue = True
                issues.append(f"{cs.name}: {cs.state.waiting.reason}")

        if has_issue:
            problems.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'issues': issues,
            })

    return problems


if __name__ == "__main__":
    print("=" * 60)
    print("Pod Diagnostics — Usage Examples")
    print("=" * 60)
    print("""
    # Diagnose a specific pod
    result = diagnose_pod('my-app-pod', 'production')
    for issue in result['issues']:
        print(f"  ⚠️ {issue['type']}: {issue.get('fix', '')}")

    # Find all problem pods
    problems = find_problem_pods()
    for p in problems:
        print(f"  {p['namespace']}/{p['name']}: {', '.join(p['issues'])}")
    """)
