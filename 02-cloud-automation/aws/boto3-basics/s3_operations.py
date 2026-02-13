"""
s3_operations.py

AWS S3 bucket and object operations using boto3.

Interview Topics:
- S3 storage classes and lifecycle policies
- Presigned URLs for secure, temporary access
- Multipart uploads for large files
- S3 event notifications for event-driven architectures

Production Use Cases:
- Automated log archival and lifecycle management
- Secure artifact distribution with presigned URLs
- Cross-region replication for disaster recovery
- S3 as a data lake for analytics

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials configured
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_s3_client(region: str = None):
    """Create a boto3 S3 client."""
    import boto3
    return boto3.client(
        's3',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def list_buckets(region: str = None) -> List[Dict[str, Any]]:
    """
    List all S3 buckets in the account.

    Returns:
        List of bucket details

    Interview Question:
        Q: How do you secure an S3 bucket?
        A: 1. Block public access (account + bucket level)
           2. Encrypt at rest (SSE-S3, SSE-KMS, or SSE-C)
           3. Encrypt in transit (enforce HTTPS via bucket policy)
           4. Enable versioning (protect against accidental deletes)
           5. Enable access logging
           6. Use IAM policies + bucket policies (least privilege)
           7. Enable MFA delete for critical buckets
    """
    s3 = get_s3_client(region)
    response = s3.list_buckets()

    buckets = []
    for bucket in response['Buckets']:
        buckets.append({
            'name': bucket['Name'],
            'creation_date': bucket['CreationDate'].isoformat()
        })

    logger.info(f"Found {len(buckets)} S3 buckets")
    return buckets


def upload_file(
    bucket: str,
    local_path: str,
    s3_key: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    storage_class: str = 'STANDARD',
    region: str = None
) -> Dict[str, Any]:
    """
    Upload a file to S3 with optional metadata and storage class.

    Args:
        bucket: S3 bucket name
        local_path: Local file path
        s3_key: S3 object key (defaults to filename)
        metadata: Custom metadata key-value pairs
        storage_class: S3 storage class (STANDARD, INTELLIGENT_TIERING, GLACIER, etc.)
        region: AWS region

    Returns:
        Upload result details

    Interview Question:
        Q: Explain S3 storage classes and when to use each.
        A: - STANDARD: Frequent access, low latency
           - INTELLIGENT_TIERING: Unknown/changing access patterns (auto-tiers)
           - STANDARD_IA: Infrequent access, per-GB retrieval fee
           - ONE_ZONE_IA: Same but single AZ (cheaper, less durable)
           - GLACIER: Archive, retrieval in minutes to hours
           - GLACIER_DEEP_ARCHIVE: Cheapest, retrieval in 12+ hours
           Use lifecycle policies to auto-transition objects.
    """
    s3 = get_s3_client(region)
    s3_key = s3_key or os.path.basename(local_path)

    extra_args = {'StorageClass': storage_class}
    if metadata:
        extra_args['Metadata'] = metadata

    try:
        file_size = os.path.getsize(local_path)
        s3.upload_file(
            local_path, bucket, s3_key,
            ExtraArgs=extra_args
        )

        logger.info(f"Uploaded {local_path} → s3://{bucket}/{s3_key} ({file_size} bytes)")
        return {
            'bucket': bucket,
            'key': s3_key,
            'size': file_size,
            'storage_class': storage_class,
            'status': 'uploaded'
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {'status': 'error', 'error': str(e)}


def generate_presigned_url(
    bucket: str,
    s3_key: str,
    expiration: int = 3600,
    region: str = None
) -> str:
    """
    Generate a presigned URL for temporary, secure access to an S3 object.

    Presigned URLs grant time-limited access without requiring
    the requester to have AWS credentials.

    Args:
        bucket: S3 bucket name
        s3_key: S3 object key
        expiration: URL validity in seconds (default: 1 hour)
        region: AWS region

    Returns:
        Presigned URL string

    Interview Question:
        Q: When would you use presigned URLs?
        A: 1. Sharing private objects with external users temporarily
           2. Allowing uploads without exposing AWS credentials
           3. Distributing build artifacts to CI/CD runners
           4. Granting customers access to their reports/invoices
           Security: always set short expiration, log access,
           consider IP restrictions via bucket policy.
    """
    s3 = get_s3_client(region)

    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': s3_key},
        ExpiresIn=expiration
    )

    logger.info(
        f"Generated presigned URL for s3://{bucket}/{s3_key} "
        f"(expires in {expiration}s)"
    )
    return url


def list_objects(
    bucket: str,
    prefix: str = '',
    max_keys: int = 1000,
    region: str = None
) -> List[Dict[str, Any]]:
    """
    List objects in an S3 bucket with optional prefix filter.

    Uses pagination to handle buckets with many objects.

    Args:
        bucket: S3 bucket name
        prefix: Key prefix for filtering (e.g., 'logs/2024/')
        max_keys: Maximum objects to return
        region: AWS region

    Returns:
        List of object details
    """
    s3 = get_s3_client(region)

    objects = []
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=prefix,
        PaginationConfig={'MaxItems': max_keys}
    ):
        for obj in page.get('Contents', []):
            objects.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
                'storage_class': obj.get('StorageClass', 'STANDARD')
            })

    logger.info(f"Found {len(objects)} objects in s3://{bucket}/{prefix}")
    return objects


def set_lifecycle_policy(
    bucket: str,
    rules: Optional[List[Dict]] = None,
    region: str = None
) -> bool:
    """
    Set a lifecycle policy on an S3 bucket.

    Lifecycle policies automate object transitions between storage
    classes and expiration (deletion) of old objects.

    Args:
        bucket: S3 bucket name
        rules: Custom lifecycle rules (uses defaults if None)
        region: AWS region

    Returns:
        True if policy was applied

    Interview Question:
        Q: Design a log retention strategy using S3 lifecycle policies.
        A: Day 0-30: STANDARD (frequent access for debugging)
           Day 30-90: STANDARD_IA (occasional access)
           Day 90-365: GLACIER (compliance requirement)
           Day 365+: DELETE or GLACIER_DEEP_ARCHIVE
           Also: enable versioning, set up cross-region replication
           for critical logs, and monitor with CloudWatch metrics.
    """
    s3 = get_s3_client(region)

    if rules is None:
        # Default rules: transition logs through storage tiers, expire after 365 days
        rules = [
            {
                'ID': 'log-lifecycle',
                'Filter': {'Prefix': 'logs/'},
                'Status': 'Enabled',
                'Transitions': [
                    {'Days': 30, 'StorageClass': 'STANDARD_IA'},
                    {'Days': 90, 'StorageClass': 'GLACIER'},
                ],
                'Expiration': {'Days': 365},
            }
        ]

    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket,
            LifecycleConfiguration={'Rules': rules}
        )
        logger.info(f"Applied lifecycle policy to bucket '{bucket}'")
        return True

    except Exception as e:
        logger.error(f"Failed to set lifecycle policy: {e}")
        return False


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("S3 Operations — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: These examples require valid AWS credentials.

    Example usage (uncomment to run):

    # List all buckets
    buckets = list_buckets()
    for b in buckets:
        print(f"  {b['name']} (created: {b['creation_date']})")

    # Upload a file
    result = upload_file(
        'my-bucket', '/tmp/report.csv',
        s3_key='reports/2024/report.csv',
        storage_class='STANDARD_IA'
    )

    # Generate presigned URL (valid for 1 hour)
    url = generate_presigned_url('my-bucket', 'reports/2024/report.csv')
    print(f"  Download URL: {url}")

    # List objects with prefix
    objects = list_objects('my-bucket', prefix='logs/2024/')
    print(f"  Found {len(objects)} log files")
    """)
