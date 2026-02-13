"""
service_restart.py

Safe service restart automation.

Prerequisites:
- subprocess
"""

import subprocess
import logging
import time
from typing import Dict, Any, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def safe_restart(
    service: str,
    restart_cmd: str,
    health_check: Callable[[], bool],
    pre_check: Callable[[], bool] = lambda: True,
    drain_seconds: int = 10,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Safely restart a service with health verification.

    Interview Question:
        Q: How do you restart a service without downtime?
        A: 1. Rolling restart: restart instances one at a time
           2. Drain: stop sending traffic, wait for in-flight to complete
           3. Health check: verify new instance healthy before continuing
           4. K8s: `kubectl rollout restart` (respects PDB, strategy)
           5. Systemd: graceful stop (SIGTERM → wait → SIGKILL)
           Key: never restart all instances at once. Use PodDisruptionBudget.
    """
    # Pre-check
    if not pre_check():
        return {'service': service, 'status': 'skipped', 'reason': 'pre-check failed'}

    logger.info(f"Draining {service} for {drain_seconds}s")
    time.sleep(drain_seconds)

    logger.info(f"Restarting {service}")
    result = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        return {'service': service, 'status': 'restart_failed', 'error': result.stderr}

    # Wait for health
    for _ in range(20):
        time.sleep(3)
        if health_check():
            logger.info(f"{service} restarted and healthy")
            return {'service': service, 'status': 'restarted', 'healthy': True}

    return {'service': service, 'status': 'restarted', 'healthy': False}


def restart_kubernetes_pod(pod: str, namespace: str = 'default') -> Dict[str, Any]:
    """Delete a pod to trigger restart (controlled by deployment)."""
    cmd = ['kubectl', 'delete', 'pod', pod, '-n', namespace, '--grace-period=30']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return {'pod': pod, 'status': 'deleted' if result.returncode == 0 else 'error'}


if __name__ == "__main__":
    print("Service Restart — Usage Examples")
    print("""
    safe_restart(
        service='nginx',
        restart_cmd='systemctl restart nginx',
        health_check=lambda: True,
        drain_seconds=5
    )
    """)
