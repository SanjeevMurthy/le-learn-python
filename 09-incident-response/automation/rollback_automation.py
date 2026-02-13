"""
rollback_automation.py

Automated deployment rollback.

Prerequisites:
- subprocess
"""

import subprocess
import logging
import time
from typing import Dict, Any, Callable, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def rollback_deployment(
    service: str,
    health_check: Callable[[], bool],
    rollback_command: str,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Automated rollback with health check verification.

    Interview Question:
        Q: When should you automate rollbacks vs manual?
        A: Automate: clear failure modes (crash loops, health check fail,
           error rate spike above threshold).
           Manual: subtle performance degradation, data correctness issues,
           partial failures, unclear root cause.
           Key: rollbacks should be faster than fixes.
           Strategies: K8s `kubectl rollout undo`, blue-green switch,
           feature flags disable, database migration rollback (if possible).
    """
    logger.info(f"Starting rollback for {service}")

    result = subprocess.run(
        rollback_command, shell=True, capture_output=True, text=True, timeout=timeout
    )

    if result.returncode != 0:
        return {'service': service, 'status': 'rollback_failed', 'error': result.stderr}

    # Verify health after rollback
    logger.info(f"Rollback executed — verifying health of {service}")
    for attempt in range(10):
        if health_check():
            return {'service': service, 'status': 'rolled_back', 'verified': True}
        time.sleep(5)

    return {'service': service, 'status': 'rolled_back', 'verified': False}


def kubernetes_rollback(deployment: str, namespace: str = 'default') -> Dict[str, Any]:
    """Rollback a Kubernetes deployment to previous revision."""
    cmd = ['kubectl', 'rollout', 'undo', f'deployment/{deployment}', '-n', namespace]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode == 0:
        # Wait for rollout to complete
        wait_cmd = ['kubectl', 'rollout', 'status', f'deployment/{deployment}',
                     '-n', namespace, '--timeout=120s']
        wait_result = subprocess.run(wait_cmd, capture_output=True, text=True, timeout=150)
        return {
            'deployment': deployment,
            'status': 'rolled_back' if wait_result.returncode == 0 else 'rollback_pending',
        }
    return {'deployment': deployment, 'status': 'failed', 'error': result.stderr}


if __name__ == "__main__":
    print("Rollback Automation — Usage Examples")
    print("""
    kubernetes_rollback('my-service', namespace='production')

    rollback_deployment(
        service='my-app',
        health_check=lambda: True,
        rollback_command='kubectl rollout undo deployment/my-app'
    )
    """)
