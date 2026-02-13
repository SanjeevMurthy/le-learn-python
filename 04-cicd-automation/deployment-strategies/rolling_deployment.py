"""
rolling_deployment.py

Rolling deployment pattern with batch-based instance updates.

Interview Topics:
- Rolling update parameters (batch size, pause)
- Health check integration
- Rollback triggers

Prerequisites:
- Standard library only
"""

import logging
import time
from typing import Dict, Any, Callable, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def rolling_deploy(
    instances: List[str],
    deploy_fn: Callable[[str, str], bool],
    health_check_fn: Callable[[str], bool],
    version: str,
    batch_size: int = 1,
    pause_between_batches: int = 30,
    max_failures: int = 1
) -> Dict[str, Any]:
    """
    Execute a rolling deployment across instances.

    Interview Question:
        Q: Compare rolling, blue-green, and canary deployments.
        A: Rolling: update instances in batches. Least resource overhead,
           but mixed versions during deploy. Rollback = re-deploy old.
           Blue-green: 2 full envs, instant switch. 2x resources.
           Canary: gradual traffic shift, best for risk reduction.
           Choose based on: infrastructure cost tolerance (BG > rolling),
           risk tolerance (canary > BG > rolling), speed requirement
           (BG > rolling > canary), observability maturity (canary needs most).
    """
    total = len(instances)
    deployed = []
    failed = []
    failure_count = 0

    # Process in batches
    for i in range(0, total, batch_size):
        batch = instances[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        logger.info(f"Batch {batch_num}: deploying to {batch}")

        for instance in batch:
            if not deploy_fn(instance, version):
                failed.append(instance)
                failure_count += 1
                logger.error(f"Deploy failed on {instance}")

                if failure_count >= max_failures:
                    logger.error(f"Max failures ({max_failures}) reached — stopping")
                    return {
                        'status': 'aborted',
                        'deployed': deployed,
                        'failed': failed,
                        'remaining': instances[i + batch_size:],
                    }
                continue

            # Health check
            if not health_check_fn(instance):
                failed.append(instance)
                failure_count += 1
                logger.error(f"Health check failed on {instance}")

                if failure_count >= max_failures:
                    return {
                        'status': 'aborted',
                        'deployed': deployed,
                        'failed': failed,
                    }
                continue

            deployed.append(instance)

        # Pause between batches
        if i + batch_size < total:
            logger.info(f"Pausing {pause_between_batches}s before next batch")
            time.sleep(pause_between_batches)

    status = 'success' if not failed else 'partial'
    logger.info(
        f"Rolling deploy complete: {len(deployed)}/{total} succeeded"
    )
    return {
        'status': status,
        'version': version,
        'deployed': deployed,
        'failed': failed,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Rolling Deployment — Usage Examples")
    print("=" * 60)
    print("""
    instances = ['web-1', 'web-2', 'web-3', 'web-4']
    result = rolling_deploy(
        instances,
        deploy_fn=lambda inst, ver: True,
        health_check_fn=lambda inst: True,
        version='2.0.0',
        batch_size=2,
        pause_between_batches=30
    )
    print(f"  Deployed: {len(result['deployed'])}/{len(instances)}")
    """)
