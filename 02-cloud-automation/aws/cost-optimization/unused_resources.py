"""
unused_resources.py

Find unused AWS resources for cost optimization.

Interview Topics:
- How to identify idle/unused cloud resources
- Automated cost cleanup strategies
- Implementing safe resource cleanup with dry-run

Production Use Cases:
- Finding unattached EBS volumes (costing money with zero utilization)
- Identifying unused Elastic IPs (charged when not associated)
- Detecting idle load balancers with no targets
- Reporting on old snapshots consuming storage

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials with read access to EC2, ELB, EBS
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_ec2_client(region: str = None):
    """Create a boto3 EC2 client."""
    import boto3
    return boto3.client(
        'ec2',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def find_unattached_volumes(region: str = None) -> List[Dict[str, Any]]:
    """
    Find EBS volumes that are not attached to any instance.

    Unattached volumes continue to incur charges. Common causes:
    instance termination without deleting volumes, or snapshots
    restored for debugging and never cleaned up.

    Args:
        region: AWS region

    Returns:
        List of unattached volume details with cost estimates

    Interview Question:
        Q: How would you design an automated cost cleanup system?
        A: 1. Discovery: scan for unused resources daily (Lambda + EventBridge)
           2. Tagging: tag candidates with 'cleanup-candidate' + date
           3. Notification: alert resource owners (Slack/email) with TTL
           4. Grace period: wait 7 days for objections
           5. Action: delete/stop resources after grace period
           6. Reporting: monthly cost savings report
           Key: always have a dry-run mode and manual override.
    """
    ec2 = get_ec2_client(region)

    # Filter for volumes in 'available' state (not attached)
    response = ec2.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )

    volumes = []
    for vol in response['Volumes']:
        # Estimate monthly cost (rough: $0.10/GB for gp2)
        volume_type = vol['VolumeType']
        size_gb = vol['Size']
        cost_per_gb = {
            'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125,
            'io2': 0.125, 'st1': 0.045, 'sc1': 0.015,
            'standard': 0.05
        }.get(volume_type, 0.10)

        monthly_cost = round(size_gb * cost_per_gb, 2)

        volumes.append({
            'volume_id': vol['VolumeId'],
            'size_gb': size_gb,
            'volume_type': volume_type,
            'state': vol['State'],
            'created': vol['CreateTime'].isoformat(),
            'az': vol['AvailabilityZone'],
            'estimated_monthly_cost': monthly_cost,
            'tags': {
                tag['Key']: tag['Value']
                for tag in vol.get('Tags', [])
            }
        })

    total_cost = sum(v['estimated_monthly_cost'] for v in volumes)
    logger.info(
        f"Found {len(volumes)} unattached volumes "
        f"(estimated monthly cost: ${total_cost:.2f})"
    )
    return volumes


def find_unused_elastic_ips(region: str = None) -> List[Dict[str, Any]]:
    """
    Find Elastic IPs not associated with any instance.

    AWS charges $0.005/hour for unassociated EIPs (~$3.60/month).

    Args:
        region: AWS region

    Returns:
        List of unused EIP details
    """
    ec2 = get_ec2_client(region)
    response = ec2.describe_addresses()

    unused = []
    for addr in response['Addresses']:
        # An EIP is unused if it has no association
        if 'AssociationId' not in addr:
            unused.append({
                'public_ip': addr['PublicIp'],
                'allocation_id': addr['AllocationId'],
                'domain': addr.get('Domain', 'vpc'),
                'estimated_monthly_cost': 3.60,
                'tags': {
                    tag['Key']: tag['Value']
                    for tag in addr.get('Tags', [])
                }
            })

    logger.info(f"Found {len(unused)} unused Elastic IPs")
    return unused


def find_old_snapshots(
    days_old: int = 90,
    region: str = None,
    owner_id: str = 'self'
) -> List[Dict[str, Any]]:
    """
    Find EBS snapshots older than a specified age.

    Old snapshots from terminated instances or previous backups
    accumulate silently and can represent significant costs.

    Args:
        days_old: Consider snapshots older than this many days
        region: AWS region
        owner_id: Snapshot owner ('self' for current account)

    Returns:
        List of old snapshot details
    """
    ec2 = get_ec2_client(region)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

    snapshots = []
    paginator = ec2.get_paginator('describe_snapshots')

    for page in paginator.paginate(OwnerIds=[owner_id]):
        for snap in page['Snapshots']:
            if snap['StartTime'] < cutoff_date:
                # Snapshot storage cost: ~$0.05/GB/month
                monthly_cost = round(snap['VolumeSize'] * 0.05, 2)
                snapshots.append({
                    'snapshot_id': snap['SnapshotId'],
                    'volume_id': snap.get('VolumeId', 'N/A'),
                    'size_gb': snap['VolumeSize'],
                    'start_time': snap['StartTime'].isoformat(),
                    'age_days': (datetime.now(timezone.utc) - snap['StartTime']).days,
                    'description': snap.get('Description', ''),
                    'estimated_monthly_cost': monthly_cost,
                })

    total_cost = sum(s['estimated_monthly_cost'] for s in snapshots)
    logger.info(
        f"Found {len(snapshots)} snapshots older than {days_old} days "
        f"(estimated monthly cost: ${total_cost:.2f})"
    )
    return snapshots


def generate_cost_report(region: str = None) -> Dict[str, Any]:
    """
    Generate a combined report of all unused resources.

    Returns:
        Summary report with total estimated savings
    """
    volumes = find_unattached_volumes(region)
    eips = find_unused_elastic_ips(region)
    snapshots = find_old_snapshots(90, region)

    total_monthly = (
        sum(v['estimated_monthly_cost'] for v in volumes)
        + sum(e['estimated_monthly_cost'] for e in eips)
        + sum(s['estimated_monthly_cost'] for s in snapshots)
    )

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat() + 'Z',
        'region': region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
        'summary': {
            'unattached_volumes': len(volumes),
            'unused_eips': len(eips),
            'old_snapshots': len(snapshots),
            'total_estimated_monthly_savings': round(total_monthly, 2),
            'total_estimated_annual_savings': round(total_monthly * 12, 2),
        },
        'details': {
            'volumes': volumes,
            'eips': eips,
            'snapshots': snapshots,
        }
    }

    logger.info(
        f"Cost report: ${total_monthly:.2f}/month potential savings "
        f"(${total_monthly * 12:.2f}/year)"
    )
    return report


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Unused Resources Finder — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires valid AWS credentials.

    Example usage:

    # Generate full cost report
    report = generate_cost_report()
    print(f"  Potential savings: ${report['summary']['total_estimated_monthly_savings']}/month")
    print(f"  Unattached volumes: {report['summary']['unattached_volumes']}")
    print(f"  Unused EIPs: {report['summary']['unused_eips']}")
    print(f"  Old snapshots: {report['summary']['old_snapshots']}")
    """)
