"""
auto_scaling.py

AWS Auto Scaling Group management using boto3.

Interview Topics:
- Scaling policies (target tracking, step, scheduled)
- Cooldown periods and scaling behavior
- Health check types (EC2 vs ELB)

Production Use Cases:
- Dynamic scaling based on CloudWatch metrics
- Scheduled scaling for predictable load patterns
- Rolling updates with ASG update policies

Prerequisites:
- boto3 (pip install boto3)
"""

import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_asg_client(region: str = None):
    import boto3
    return boto3.client(
        'autoscaling',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def list_auto_scaling_groups(region: str = None) -> List[Dict[str, Any]]:
    """
    List all Auto Scaling Groups with key details.

    Interview Question:
        Q: Explain the different ASG scaling policy types.
        A: 1. Target Tracking: maintain a target metric value
              (e.g., keep CPU at 50%). Simplest to configure.
           2. Step Scaling: different scaling actions at different
              alarm thresholds (e.g., add 1 at 60%, add 3 at 80%).
           3. Scheduled: scale at specific times (e.g., scale up
              before business hours, down after).
           4. Predictive: ML-based, scales proactively based on
              historical patterns.
    """
    asg = get_asg_client(region)
    groups = []

    paginator = asg.get_paginator('describe_auto_scaling_groups')
    for page in paginator.paginate():
        for group in page['AutoScalingGroups']:
            groups.append({
                'name': group['AutoScalingGroupName'],
                'min_size': group['MinSize'],
                'max_size': group['MaxSize'],
                'desired_capacity': group['DesiredCapacity'],
                'instances': len(group['Instances']),
                'health_check_type': group['HealthCheckType'],
                'launch_template': group.get('LaunchTemplate', {}).get(
                    'LaunchTemplateName', 'N/A'
                ),
                'azs': group['AvailabilityZones'],
            })

    logger.info(f"Found {len(groups)} Auto Scaling Groups")
    return groups


def update_asg_capacity(
    asg_name: str,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    desired: Optional[int] = None,
    region: str = None
) -> Dict[str, Any]:
    """
    Update ASG capacity settings.

    Interview Question:
        Q: What is a cooldown period and why is it important?
        A: Cooldown prevents the ASG from launching/terminating more
           instances before previous scaling takes effect. Default 300s.
           Without it, the ASG might scale based on metrics from
           the OLD capacity, leading to over/under-provisioning.
           Set cooldown based on instance startup time + warm-up.
    """
    asg = get_asg_client(region)
    update = {'AutoScalingGroupName': asg_name}
    if min_size is not None:
        update['MinSize'] = min_size
    if max_size is not None:
        update['MaxSize'] = max_size
    if desired is not None:
        update['DesiredCapacity'] = desired

    try:
        asg.update_auto_scaling_group(**update)
        logger.info(f"Updated ASG {asg_name}: min={min_size}, max={max_size}, desired={desired}")
        return {'asg_name': asg_name, 'status': 'updated', **update}
    except Exception as e:
        logger.error(f"Failed to update ASG: {e}")
        return {'asg_name': asg_name, 'status': 'error', 'error': str(e)}


def create_scaling_policy(
    asg_name: str,
    policy_name: str,
    metric_name: str = 'CPUUtilization',
    target_value: float = 50.0,
    region: str = None
) -> Dict[str, Any]:
    """Create a target tracking scaling policy."""
    asg = get_asg_client(region)
    try:
        response = asg.put_scaling_policy(
            AutoScalingGroupName=asg_name,
            PolicyName=policy_name,
            PolicyType='TargetTrackingScaling',
            TargetTrackingConfiguration={
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    if metric_name == 'CPUUtilization' else metric_name
                },
                'TargetValue': target_value,
                'DisableScaleIn': False,
            }
        )
        logger.info(f"Created scaling policy: {policy_name} for {asg_name}")
        return {'policy_name': policy_name, 'policy_arn': response['PolicyARN'], 'status': 'created'}
    except Exception as e:
        logger.error(f"Failed to create policy: {e}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("Auto Scaling — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials.

    # List all ASGs
    groups = list_auto_scaling_groups()
    for g in groups:
        print(f"  {g['name']}: {g['instances']}/{g['desired_capacity']} instances")

    # Update capacity
    update_asg_capacity('my-asg', min_size=2, max_size=10, desired=4)

    # Create target tracking policy
    create_scaling_policy('my-asg', 'cpu-target-50', target_value=50.0)
    """)
