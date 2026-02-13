"""
cloud_storage.py

GCP Cloud Storage (GCS) operations.

Interview Topics:
- GCS storage classes (Standard, Nearline, Coldline, Archive)
- Object lifecycle management
- GCS vs S3 comparison

Production Use Cases:
- Bucket creation with lifecycle policies
- Object upload/download with metadata
- Signed URL generation for temporary access

Prerequisites:
- google-cloud-storage (pip install google-cloud-storage)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_storage_client():
    from google.cloud import storage
    return storage.Client()


def list_buckets() -> List[Dict[str, Any]]:
    """
    List all GCS buckets in the project.

    Interview Question:
        Q: Compare GCS and S3 storage classes.
        A: GCS Standard ≈ S3 Standard (frequent access)
           GCS Nearline ≈ S3 Standard-IA (30-day min)
           GCS Coldline ≈ S3 Glacier Instant (90-day min)
           GCS Archive ≈ S3 Glacier Deep Archive (365-day min)
           Key difference: GCS charges per operation + retrieval,
           S3 has more tiers. GCS has simpler lifecycle policies.
    """
    client = get_storage_client()
    buckets = []
    for bucket in client.list_buckets():
        buckets.append({
            'name': bucket.name,
            'location': bucket.location,
            'storage_class': bucket.storage_class,
            'created': str(bucket.time_created),
        })
    logger.info(f"Found {len(buckets)} GCS buckets")
    return buckets


def upload_blob(
    bucket_name: str,
    local_path: str,
    blob_name: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Upload a file to GCS."""
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob_name = blob_name or os.path.basename(local_path)
    blob = bucket.blob(blob_name)

    if metadata:
        blob.metadata = metadata

    try:
        blob.upload_from_filename(local_path)
        logger.info(f"Uploaded {local_path} → gs://{bucket_name}/{blob_name}")
        return {
            'bucket': bucket_name, 'blob': blob_name,
            'size': blob.size, 'status': 'uploaded'
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {'status': 'error', 'error': str(e)}


def generate_signed_url(
    bucket_name: str,
    blob_name: str,
    expiration_minutes: int = 60
) -> str:
    """
    Generate a signed URL for temporary access to a GCS object.

    Interview Question:
        Q: How do signed URLs work in GCS?
        A: Signed URLs use HMAC or service account key to create
           a time-limited URL. Anyone with the URL can access the
           object until expiration. Unlike S3 presigned URLs, GCS
           signed URLs can use V4 signing (recommended) and support
           both download and upload operations.
    """
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version='v4',
        expiration=timedelta(minutes=expiration_minutes),
        method='GET',
    )
    logger.info(f"Generated signed URL for gs://{bucket_name}/{blob_name}")
    return url


def set_lifecycle_policy(bucket_name: str) -> bool:
    """Set a default lifecycle policy for log retention."""
    client = get_storage_client()
    bucket = client.get_bucket(bucket_name)

    bucket.add_lifecycle_delete_rule(age=365)
    bucket.add_lifecycle_set_storage_class_rule('NEARLINE', age=30)
    bucket.add_lifecycle_set_storage_class_rule('COLDLINE', age=90)
    bucket.patch()

    logger.info(f"Applied lifecycle policy to gs://{bucket_name}")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("GCP Cloud Storage — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires GCP credentials.

    # List buckets
    for b in list_buckets():
        print(f"  {b['name']}: {b['storage_class']} in {b['location']}")

    # Upload file
    upload_blob('my-bucket', '/tmp/report.csv', 'reports/2024/report.csv')

    # Generate signed URL
    url = generate_signed_url('my-bucket', 'reports/2024/report.csv')
    """)
