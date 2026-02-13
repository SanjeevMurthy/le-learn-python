"""
blue_green_deployment.py

Blue-green deployment pattern implementation.

Interview Topics:
- Blue-green vs canary vs rolling
- DNS-based vs load balancer-based switching
- Rollback strategies

Prerequisites:
- requests (pip install requests)
"""

import logging
import time
from typing import Dict, Any, Optional, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def blue_green_deploy(
    deploy_fn: Callable[[str, str], bool],
    switch_fn: Callable[[str], bool],
    health_check_fn: Callable[[str], bool],
    version: str,
    active_env: str = 'blue',
    max_health_retries: int = 10,
    health_interval: int = 10
) -> Dict[str, Any]:
    """
    Execute a blue-green deployment.

    Interview Question:
        Q: Explain the blue-green deployment pattern.
        A: Two identical environments: Blue (current) and Green (new).
           1. Deploy new version to idle environment (Green)
           2. Run smoke tests on Green
           3. Switch traffic from Blue to Green (DNS/LB)
           4. Blue becomes the rollback target
           5. If issues, switch back to Blue instantly
           Pros: instant rollback, zero downtime.
           Cons: 2x infrastructure cost, database migration complexity.

        Q: How do you handle database changes in blue-green?
        A: Use expand-contract pattern:
           1. Add new columns/tables (backward compatible)
           2. Deploy new app version (writes to both old and new)
           3. Migrate data
           4. Remove old columns in next release
           Never make breaking DB changes in a single deploy.
    """
    inactive_env = 'green' if active_env == 'blue' else 'blue'

    # Step 1: Deploy to inactive environment
    logger.info(f"Deploying v{version} to {inactive_env} environment")
    if not deploy_fn(inactive_env, version):
        return {'status': 'deploy_failed', 'environment': inactive_env}

    # Step 2: Health check on new environment
    logger.info(f"Running health checks on {inactive_env}")
    healthy = False
    for attempt in range(max_health_retries):
        if health_check_fn(inactive_env):
            healthy = True
            break
        logger.info(f"Health check attempt {attempt + 1}/{max_health_retries}")
        time.sleep(health_interval)

    if not healthy:
        logger.error(f"Health checks failed on {inactive_env}")
        return {'status': 'health_check_failed', 'environment': inactive_env}

    # Step 3: Switch traffic
    logger.info(f"Switching traffic: {active_env} → {inactive_env}")
    if not switch_fn(inactive_env):
        return {'status': 'switch_failed', 'environment': inactive_env}

    logger.info(f"Blue-green deployment complete: {inactive_env} is now active")
    return {
        'status': 'success',
        'active_environment': inactive_env,
        'previous_environment': active_env,
        'version': version,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Blue-Green Deployment — Usage Examples")
    print("=" * 60)
    print("""
    # Define callbacks for your infrastructure
    def deploy(env, version):
        # Deploy to target env (e.g., update K8s, ASG, etc.)
        return True

    def switch_traffic(env):
        # Update DNS/LB to point to new env
        return True

    def health_check(env):
        # Check if new env is healthy
        return True

    result = blue_green_deploy(deploy, switch_traffic, health_check, '2.0.0')
    """)
