"""
automated_backups.py

Automated AWS backup operations for EC2, RDS, and EBS.

Interview Topics:
- Backup strategies (full, incremental, snapshot)
- RPO vs RTO requirements
- Cross-region backups for disaster recovery

Production Use Cases:
- Scheduled EBS snapshot creation with retention
- RDS automated backup management
- Cross-region snapshot copying for DR

Prerequisites:
- boto3 (pip install boto3)
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
    import boto3
    return boto3.client(
        'ec2',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def create_ebs_snapshots_by_tag(
    tag_key: str = 'Backup',
    tag_value: str = 'true',
    region: str = None
) -> List[Dict[str, Any]]:
    """
    Create EBS snapshots for all volumes with a specific tag.

    Interview Question:
        Q: Explain RPO vs RTO in disaster recovery.
        A: RPO (Recovery Point Objective): max acceptable data loss
           measured in time. E.g., RPO of 1 hour means you can lose
           at most 1 hour of data → need hourly backups.
           RTO (Recovery Time Objective): max acceptable downtime.
           E.g., RTO of 15 mins means system must be back in 15 mins.
           Lower RPO/RTO = higher cost (more frequent backups,
           faster recovery infrastructure).
    """
    ec2 = get_ec2_client(region)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')

    # Find volumes tagged for backup
    volumes = ec2.describe_volumes(
        Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
    )

    snapshots = []
    for vol in volumes['Volumes']:
        vol_id = vol['VolumeId']
        vol_name = next(
            (t['Value'] for t in vol.get('Tags', []) if t['Key'] == 'Name'), vol_id
        )

        try:
            snap = ec2.create_snapshot(
                VolumeId=vol_id,
                Description=f"Automated backup of {vol_name} on {timestamp}",
                TagSpecifications=[{
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'Name', 'Value': f"backup-{vol_name}-{timestamp}"},
                        {'Key': 'BackupSource', 'Value': vol_id},
                        {'Key': 'CreatedBy', 'Value': 'devops-toolkit'},
                    ]
                }]
            )
            snapshots.append({
                'volume_id': vol_id, 'snapshot_id': snap['SnapshotId'],
                'status': 'creating'
            })
            logger.info(f"Created snapshot {snap['SnapshotId']} for {vol_id}")
        except Exception as e:
            logger.error(f"Failed to snapshot {vol_id}: {e}")
            snapshots.append({'volume_id': vol_id, 'status': 'error', 'error': str(e)})

    return snapshots


def cleanup_old_snapshots(
    retention_days: int = 30,
    tag_key: str = 'CreatedBy',
    tag_value: str = 'devops-toolkit',
    dry_run: bool = True,
    region: str = None
) -> Dict[str, Any]:
    """
    Delete snapshots older than retention period.

    Only deletes snapshots managed by this toolkit (identified by tag).
    Always supports dry_run for safety.
    """
    ec2 = get_ec2_client(region)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    old_snapshots = []
    paginator = ec2.get_paginator('describe_snapshots')
    for page in paginator.paginate(
        OwnerIds=['self'],
        Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
    ):
        for snap in page['Snapshots']:
            if snap['StartTime'] < cutoff:
                old_snapshots.append(snap)

    deleted = []
    errors = []
    for snap in old_snapshots:
        if dry_run:
            logger.info(f"[DRY RUN] Would delete {snap['SnapshotId']}")
            deleted.append(snap['SnapshotId'])
        else:
            try:
                ec2.delete_snapshot(SnapshotId=snap['SnapshotId'])
                deleted.append(snap['SnapshotId'])
            except Exception as e:
                errors.append({'snapshot_id': snap['SnapshotId'], 'error': str(e)})

    return {
        'retention_days': retention_days,
        'dry_run': dry_run,
        'deleted': deleted,
        'errors': errors,
        'total_deleted': len(deleted),
    }


def copy_snapshot_cross_region(
    snapshot_id: str,
    source_region: str,
    dest_region: str,
    description: str = ''
) -> Dict[str, Any]:
    """
    Copy an EBS snapshot to another region for disaster recovery.

    Interview Question:
        Q: Design a cross-region DR strategy for AWS.
        A: 1. Identify critical resources (RDS, EBS, S3)
           2. Set RPO/RTO targets per service
           3. Automate cross-region snapshot copies (EBS, RDS)
           4. Enable S3 cross-region replication
           5. Maintain infrastructure-as-code for DR region
           6. Regular DR drills (failover and failback testing)
    """
    import boto3
    dest_ec2 = boto3.client('ec2', region_name=dest_region)

    try:
        response = dest_ec2.copy_snapshot(
            SourceSnapshotId=snapshot_id,
            SourceRegion=source_region,
            Description=description or f"DR copy of {snapshot_id} from {source_region}",
        )
        logger.info(
            f"Copying {snapshot_id}: {source_region} → {dest_region} "
            f"(new: {response['SnapshotId']})"
        )
        return {
            'source_snapshot_id': snapshot_id,
            'dest_snapshot_id': response['SnapshotId'],
            'source_region': source_region,
            'dest_region': dest_region,
            'status': 'copying',
        }
    except Exception as e:
        logger.error(f"Cross-region copy failed: {e}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("Automated Backups — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials.

    # Create snapshots for tagged volumes
    snapshots = create_ebs_snapshots_by_tag(tag_key='Backup', tag_value='true')

    # Cleanup old snapshots (dry run first)
    result = cleanup_old_snapshots(retention_days=30, dry_run=True)
    print(f"  Would delete: {result['total_deleted']} snapshots")

    # Cross-region copy for DR
    copy_snapshot_cross_region('snap-abc123', 'us-east-1', 'us-west-2')
    """)
