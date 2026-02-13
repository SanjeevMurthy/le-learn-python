"""
canary_deployment.py

Canary deployment pattern with gradual traffic shifting.

Interview Topics:
- Traffic splitting strategies
- Canary analysis and metrics
- Automated rollback criteria

Prerequisites:
- Standard library only
"""

import logging
import time
from typing import Dict, Any, Callable, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def canary_deploy(
    deploy_fn: Callable[[str], bool],
    set_traffic_fn: Callable[[int], bool],
    metrics_fn: Callable[[], Dict[str, float]],
    rollback_fn: Callable[[], bool],
    version: str,
    traffic_steps: List[int] = None,
    step_duration: int = 60,
    error_threshold: float = 5.0,
    latency_threshold: float = 500.0
) -> Dict[str, Any]:
    """
    Execute a canary deployment with automated analysis.

    Interview Question:
        Q: How does canary deployment differ from blue-green?
        A: Canary: gradually shift traffic (5% → 25% → 50% → 100%).
           Monitor error rate, latency, business metrics at each step.
           Auto-rollback if thresholds exceeded.
           Pros: lower risk, real user traffic testing, smaller blast radius.
           Cons: slower (minutes-hours), requires good observability,
           more complex routing, session affinity challenges.
           Blue-green: all-or-nothing switch, instant rollback,
           but higher infrastructure cost.
    """
    steps = traffic_steps or [5, 10, 25, 50, 75, 100]

    # Step 1: Deploy canary
    logger.info(f"Deploying canary v{version}")
    if not deploy_fn(version):
        return {'status': 'deploy_failed'}

    # Step 2: Gradually increase traffic
    for pct in steps:
        logger.info(f"Setting canary traffic to {pct}%")
        if not set_traffic_fn(pct):
            logger.error(f"Failed to set traffic to {pct}%")
            rollback_fn()
            return {'status': 'traffic_shift_failed', 'at_percent': pct}

        # Wait and collect metrics
        logger.info(f"Monitoring at {pct}% for {step_duration}s")
        time.sleep(step_duration)

        # Analyze metrics
        metrics = metrics_fn()
        error_rate = metrics.get('error_rate', 0)
        p99_latency = metrics.get('p99_latency', 0)

        logger.info(f"Metrics: error_rate={error_rate}%, p99={p99_latency}ms")

        if error_rate > error_threshold:
            logger.error(f"Error rate {error_rate}% > threshold {error_threshold}%")
            rollback_fn()
            return {
                'status': 'rolled_back',
                'reason': 'error_rate_exceeded',
                'at_percent': pct,
                'metrics': metrics,
            }

        if p99_latency > latency_threshold:
            logger.error(f"Latency {p99_latency}ms > threshold {latency_threshold}ms")
            rollback_fn()
            return {
                'status': 'rolled_back',
                'reason': 'latency_exceeded',
                'at_percent': pct,
                'metrics': metrics,
            }

        logger.info(f"Canary healthy at {pct}%")

    logger.info(f"Canary deployment complete: v{version} at 100%")
    return {'status': 'success', 'version': version, 'final_metrics': metrics}


if __name__ == "__main__":
    print("=" * 60)
    print("Canary Deployment — Usage Examples")
    print("=" * 60)
    print("""
    result = canary_deploy(
        deploy_fn=lambda v: True,
        set_traffic_fn=lambda pct: True,
        metrics_fn=lambda: {'error_rate': 0.5, 'p99_latency': 200},
        rollback_fn=lambda: True,
        version='2.0.0',
        traffic_steps=[5, 25, 50, 100],
        step_duration=30
    )
    """)
