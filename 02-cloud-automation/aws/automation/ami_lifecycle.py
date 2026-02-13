"""
ami_lifecycle.py

AMI lifecycle management — creation, deregistration, and cleanup.

Interview Topics:
- AMI vs snapshot differences
- Golden AMI pipeline
- AMI sharing and security

Production Use Cases:
- Automated golden AMI creation with Packer
- AMI retention and deregistration policies
- Cross-account AMI sharing
- AMI vulnerability scanning integration

Prerequisites:
- boto3 (pip install boto3)
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_ec2_client(region: str = None):
    import boto3
    return boto3.client(
        'ec2',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def list_amis(
    owner: str = 'self',
    name_filter: str = '*',
    region: str = None
) -> List[Dict[str, Any]]:
    """
    List AMIs owned by the account.

    Interview Question:
        Q: What is a golden AMI pipeline?
        A: An automated process that creates hardened, pre-configured
           AMIs: 1. Start with base OS AMI
           2. Apply security patches and hardening
           3. Install common tools/agents (monitoring, logging)
           4. Run vulnerability scan (Inspector, Trivy)
           5. Tag with version + compliance status
           6. Share to application accounts
           7. Deregister old AMIs after retention period
    """
    ec2 = get_ec2_client(region)
    response = ec2.describe_images(
        Owners=[owner],
        Filters=[{'Name': 'name', 'Values': [name_filter]}]
    )

    amis = []
    for img in response['Images']:
        amis.append({
            'ami_id': img['ImageId'],
            'name': img.get('Name', 'N/A'),
            'state': img['State'],
            'creation_date': img.get('CreationDate', 'N/A'),
            'description': img.get('Description', ''),
            'tags': {t['Key']: t['Value'] for t in img.get('Tags', [])},
            'block_devices': len(img.get('BlockDeviceMappings', [])),
        })

    amis.sort(key=lambda a: a['creation_date'], reverse=True)
    logger.info(f"Found {len(amis)} AMIs matching '{name_filter}'")
    return amis


def deregister_old_amis(
    retention_days: int = 90,
    name_prefix: str = 'backup-',
    dry_run: bool = True,
    region: str = None
) -> Dict[str, Any]:
    """
    Deregister AMIs older than retention period and delete associated snapshots.

    Always run with dry_run=True first to review what will be deleted.
    """
    ec2 = get_ec2_client(region)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    amis = list_amis(name_filter=f"{name_prefix}*", region=region)
    old_amis = [
        a for a in amis
        if a['creation_date'] != 'N/A' and
        datetime.fromisoformat(a['creation_date'].replace('Z', '+00:00')) < cutoff
    ]

    result = {'dry_run': dry_run, 'deregistered': [], 'errors': []}

    for ami in old_amis:
        if dry_run:
            logger.info(f"[DRY RUN] Would deregister {ami['ami_id']} ({ami['name']})")
            result['deregistered'].append(ami['ami_id'])
        else:
            try:
                # Get associated snapshots before deregistering
                img = ec2.describe_images(ImageIds=[ami['ami_id']])['Images'][0]
                snap_ids = [
                    bd['Ebs']['SnapshotId']
                    for bd in img.get('BlockDeviceMappings', [])
                    if 'Ebs' in bd and 'SnapshotId' in bd['Ebs']
                ]

                ec2.deregister_image(ImageId=ami['ami_id'])
                # Delete associated snapshots
                for snap_id in snap_ids:
                    ec2.delete_snapshot(SnapshotId=snap_id)

                result['deregistered'].append(ami['ami_id'])
                logger.info(f"Deregistered {ami['ami_id']} + {len(snap_ids)} snapshots")
            except Exception as e:
                result['errors'].append({'ami_id': ami['ami_id'], 'error': str(e)})

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("AMI Lifecycle — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials.

    # List all AMIs
    amis = list_amis()
    for a in amis:
        print(f"  {a['ami_id']}: {a['name']} ({a['creation_date']})")

    # Deregister old backup AMIs (dry run)
    result = deregister_old_amis(retention_days=90, dry_run=True)
    print(f"  Would deregister: {len(result['deregistered'])} AMIs")
    """)
