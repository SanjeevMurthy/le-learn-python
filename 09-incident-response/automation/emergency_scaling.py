"""
emergency_scaling.py

Emergency horizontal/vertical scaling automation.

Prerequisites:
- subprocess, boto3 (optional)
"""

import subprocess
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scale_kubernetes_deployment(
    deployment: str,
    replicas: int,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """
    Emergency scale a Kubernetes deployment.

    Interview Question:
        Q: How do you handle emergency capacity issues?
        A: Immediate: scale replicas (HPA or manual kubectl scale).
           If node-limited: add nodes (cluster autoscaler, or manual).
           If region-limited: failover to another region.
           Non-compute: increase DB connections, cache capacity.
           Post-incident: review capacity planning, set up auto-scaling.
           Key metric: time-to-scale (how fast can you add capacity).
    """
    cmd = [
        'kubectl', 'scale', f'deployment/{deployment}',
        f'--replicas={replicas}', '-n', namespace
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode == 0:
        logger.info(f"Scaled {deployment} to {replicas} replicas")
        return {'deployment': deployment, 'replicas': replicas, 'status': 'scaled'}
    return {'status': 'error', 'error': result.stderr}


def scale_aws_asg(
    asg_name: str,
    desired: int,
    max_size: int = 0
) -> Dict[str, Any]:
    """Scale an AWS Auto Scaling Group."""
    try:
        import boto3
        client = boto3.client('autoscaling')

        params = {
            'AutoScalingGroupName': asg_name,
            'DesiredCapacity': desired,
        }
        if max_size:
            params['MaxSize'] = max_size

        client.update_auto_scaling_group(**params)
        logger.info(f"Scaled ASG {asg_name} to {desired}")
        return {'asg': asg_name, 'desired': desired, 'status': 'scaled'}
    except ImportError:
        return {'status': 'error', 'error': 'boto3 not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Emergency Scaling — Usage Examples")
    print("""
    scale_kubernetes_deployment('api-server', replicas=10, namespace='production')
    scale_aws_asg('prod-web-asg', desired=20, max_size=30)
    """)
