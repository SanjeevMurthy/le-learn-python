"""
ec2_management.py

AWS EC2 instance management using boto3.

Interview Topics:
- How does boto3 client vs resource model work?
- How to filter instances efficiently?
- Best practices for tagging and lifecycle management

Production Use Cases:
- Listing and filtering instances across environments
- Stopping idle instances for cost savings
- Creating AMI backups before maintenance
- Automated instance tagging and compliance checks

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials configured (IAM role, env vars, or ~/.aws/credentials)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_ec2_client(region: str = None):
    """
    Create a boto3 EC2 client for the specified region.

    Args:
        region: AWS region (defaults to AWS_DEFAULT_REGION env var)

    Returns:
        boto3 EC2 client

    Interview Question:
        Q: What is the difference between boto3 client and resource?
        A: Client is a low-level API that maps 1:1 to AWS API calls.
           Resource is a higher-level, object-oriented abstraction.
           Client gives you more control and works with all services.
           Resource is more Pythonic but doesn't cover all APIs.
           In production automation, client is preferred for consistency.
    """
    import boto3
    return boto3.client(
        'ec2',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def list_instances_by_tag(
    tag_key: str,
    tag_value: str,
    region: str = None,
    states: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List EC2 instances filtered by a specific tag.

    Tags are the primary way to organize and filter AWS resources.
    Common tags: Environment, Team, Application, CostCenter.

    Args:
        tag_key: Tag key to filter on (e.g., 'Environment')
        tag_value: Tag value to match (e.g., 'production')
        region: AWS region
        states: Instance states to include (default: all running/stopped)

    Returns:
        List of instance details

    Interview Question:
        Q: How do you organize resources across multiple AWS accounts?
        A: Use a tagging strategy with mandatory tags:
           - Environment (prod/staging/dev)
           - Team/Owner (for cost allocation)
           - Application (for grouping)
           - CostCenter (for billing)
           Enforce with AWS Config rules and tag policies.
    """
    ec2 = get_ec2_client(region)

    # Build filters — boto3 uses this format for API filtering
    filters = [
        {
            'Name': f'tag:{tag_key}',
            'Values': [tag_value]
        }
    ]

    # Optionally filter by instance state
    if states:
        filters.append({
            'Name': 'instance-state-name',
            'Values': states
        })

    instances = []

    # Use paginator for large result sets — describe_instances
    # returns max 1000 results per page
    paginator = ec2.get_paginator('describe_instances')

    for page in paginator.paginate(Filters=filters):
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                # Extract useful information from each instance
                instance_info = {
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'launch_time': instance['LaunchTime'].isoformat(),
                    'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                    'public_ip': instance.get('PublicIpAddress', 'N/A'),
                    'tags': {
                        tag['Key']: tag['Value']
                        for tag in instance.get('Tags', [])
                    },
                    'vpc_id': instance.get('VpcId', 'N/A'),
                    'subnet_id': instance.get('SubnetId', 'N/A'),
                }
                instances.append(instance_info)

    logger.info(
        f"Found {len(instances)} instances with tag {tag_key}={tag_value}"
    )
    return instances


def stop_instances_by_tag(
    tag_key: str = 'AutoStop',
    tag_value: str = 'true',
    region: str = None,
    dry_run: bool = True
) -> Dict[str, List[str]]:
    """
    Stop running EC2 instances that match a specific tag.

    Used for cost optimization — stop development/staging instances
    outside business hours. Schedule with EventBridge or cron.

    Args:
        tag_key: Tag key identifying instances to stop
        tag_value: Tag value to match
        region: AWS region
        dry_run: If True, only report what would be stopped

    Returns:
        Dictionary with lists of stopped/skipped/error instance IDs

    Interview Question:
        Q: How would you implement automated cost savings for EC2?
        A: 1. Tag instances with AutoStop/AutoStart schedules
           2. Lambda + EventBridge to stop dev/staging at night
           3. Identify idle instances (CPU < 5% for 7 days)
           4. Right-size instances using CloudWatch metrics
           5. Use Savings Plans or Reserved Instances for prod
           6. Spot instances for fault-tolerant workloads
    """
    ec2 = get_ec2_client(region)

    # Find running instances with the target tag
    running_instances = list_instances_by_tag(
        tag_key, tag_value, region, states=['running']
    )

    result = {'stopped': [], 'skipped': [], 'errors': []}

    if not running_instances:
        logger.info("No running instances found matching criteria")
        return result

    instance_ids = [i['instance_id'] for i in running_instances]

    if dry_run:
        logger.info(f"[DRY RUN] Would stop {len(instance_ids)} instances: {instance_ids}")
        result['skipped'] = instance_ids
        return result

    try:
        # Stop the instances
        response = ec2.stop_instances(InstanceIds=instance_ids)

        for change in response['StoppingInstances']:
            result['stopped'].append(change['InstanceId'])
            logger.info(
                f"Stopped {change['InstanceId']}: "
                f"{change['PreviousState']['Name']} → {change['CurrentState']['Name']}"
            )

    except Exception as e:
        logger.error(f"Error stopping instances: {e}")
        result['errors'] = instance_ids

    return result


def create_ami_backup(
    instance_id: str,
    name_prefix: str = 'backup',
    retention_days: int = 7,
    region: str = None,
    no_reboot: bool = True
) -> Dict[str, Any]:
    """
    Create an AMI backup of an EC2 instance.

    AMIs capture the full state of an instance including EBS volumes,
    making them ideal for backups before maintenance or deployments.

    Args:
        instance_id: EC2 instance ID to back up
        name_prefix: Prefix for the AMI name
        retention_days: How long to keep the backup (stored as tag)
        region: AWS region
        no_reboot: If True, don't reboot instance during image creation

    Returns:
        AMI creation details

    Interview Question:
        Q: What are the trade-offs of no_reboot=True for AMI creation?
        A: With no_reboot=True: no downtime, but filesystem may be
           inconsistent (dirty writes not flushed). With no_reboot=False:
           brief downtime, but ensures filesystem consistency.
           For production: use no_reboot=True + application-level quiesce
           (stop writes, flush buffers, then create AMI).
    """
    ec2 = get_ec2_client(region)

    # Create a descriptive name with timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    ami_name = f"{name_prefix}-{instance_id}-{timestamp}"

    try:
        # Create the AMI
        response = ec2.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            Description=f"Automated backup of {instance_id} on {timestamp}",
            NoReboot=no_reboot,
            TagSpecifications=[
                {
                    'ResourceType': 'image',
                    'Tags': [
                        {'Key': 'Name', 'Value': ami_name},
                        {'Key': 'BackupSource', 'Value': instance_id},
                        {'Key': 'RetentionDays', 'Value': str(retention_days)},
                        {'Key': 'CreatedBy', 'Value': 'devops-toolkit'},
                    ]
                }
            ]
        )

        ami_id = response['ImageId']
        logger.info(f"Created AMI {ami_id} for instance {instance_id}")

        return {
            'ami_id': ami_id,
            'ami_name': ami_name,
            'instance_id': instance_id,
            'retention_days': retention_days,
            'no_reboot': no_reboot,
            'status': 'creating'
        }

    except Exception as e:
        logger.error(f"Failed to create AMI for {instance_id}: {e}")
        return {
            'instance_id': instance_id,
            'status': 'error',
            'error': str(e)
        }


def get_instance_metrics(
    instance_id: str,
    metric_name: str = 'CPUUtilization',
    period_hours: int = 24,
    region: str = None
) -> Dict[str, Any]:
    """
    Get CloudWatch metrics for an EC2 instance.

    Args:
        instance_id: EC2 instance ID
        metric_name: CloudWatch metric name
        period_hours: How far back to look
        region: AWS region

    Returns:
        Metric statistics
    """
    import boto3
    from datetime import timedelta

    cw = boto3.client(
        'cloudwatch',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=period_hours)

    response = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName=metric_name,
        Dimensions=[
            {'Name': 'InstanceId', 'Value': instance_id}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,  # 1 hour granularity
        Statistics=['Average', 'Maximum']
    )

    datapoints = sorted(
        response['Datapoints'],
        key=lambda x: x['Timestamp']
    )

    return {
        'instance_id': instance_id,
        'metric': metric_name,
        'period_hours': period_hours,
        'datapoints': [
            {
                'timestamp': dp['Timestamp'].isoformat(),
                'average': round(dp['Average'], 2),
                'maximum': round(dp['Maximum'], 2),
            }
            for dp in datapoints
        ],
        'avg_overall': round(
            sum(dp['Average'] for dp in datapoints) / len(datapoints), 2
        ) if datapoints else 0
    }


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("EC2 Management — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: These examples require valid AWS credentials.
    Set up credentials using one of:
      1. AWS CLI: aws configure
      2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
      3. IAM role (when running on EC2/Lambda)

    Example usage (uncomment to run):

    # List all production instances
    instances = list_instances_by_tag('Environment', 'production')
    for inst in instances:
        print(f"  {inst['instance_id']}: {inst['instance_type']} ({inst['state']})")

    # Stop dev instances (dry run)
    result = stop_instances_by_tag('Environment', 'development', dry_run=True)
    print(f"  Would stop: {result['skipped']}")

    # Create AMI backup
    backup = create_ami_backup('i-1234567890abcdef0', retention_days=14)
    print(f"  Created AMI: {backup.get('ami_id', 'N/A')}")
    """)
