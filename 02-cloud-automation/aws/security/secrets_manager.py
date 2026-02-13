"""
secrets_manager.py

AWS Secrets Manager operations for secure credential management.

Interview Topics:
- Why use Secrets Manager vs environment variables?
- Secret rotation strategies
- Cost comparison with SSM Parameter Store

Production Use Cases:
- Storing and retrieving database credentials
- Automatic secret rotation
- Cross-account secret sharing
- API key management for third-party services

Prerequisites:
- boto3 (pip install boto3)
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_sm_client(region: str = None):
    import boto3
    return boto3.client(
        'secretsmanager',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def create_secret(
    name: str,
    secret_value: Dict[str, str],
    description: str = '',
    region: str = None
) -> Dict[str, Any]:
    """
    Create a new secret in Secrets Manager.

    Interview Question:
        Q: Secrets Manager vs SSM Parameter Store — when to use which?
        A: Secrets Manager: automatic rotation, cross-account sharing,
           built-in RDS/Redshift rotation, $0.40/secret/month.
           Parameter Store: free tier (standard), simpler, good for
           config values, no built-in rotation. Use SM for credentials
           that need rotation; use SSM for config that rarely changes.
    """
    sm = get_sm_client(region)
    try:
        response = sm.create_secret(
            Name=name,
            Description=description,
            SecretString=json.dumps(secret_value),
            Tags=[
                {'Key': 'ManagedBy', 'Value': 'devops-toolkit'},
            ]
        )
        logger.info(f"Created secret: {name}")
        return {'name': name, 'arn': response['ARN'], 'status': 'created'}
    except Exception as e:
        logger.error(f"Failed to create secret: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def get_secret(name: str, region: str = None) -> Dict[str, Any]:
    """
    Retrieve a secret value from Secrets Manager.

    Always cache secrets locally and refresh periodically rather
    than calling GetSecretValue on every request (cost + latency).

    Interview Question:
        Q: How do you handle secret rotation without downtime?
        A: 1. Secrets Manager supports multi-user rotation (alternating)
           2. Lambda rotation function creates new credentials
           3. Both old and new credentials remain valid during transition
           4. Applications should handle credential refresh gracefully
           5. Use version stages: AWSCURRENT and AWSPREVIOUS
    """
    sm = get_sm_client(region)
    try:
        response = sm.get_secret_value(SecretId=name)
        secret_data = json.loads(response['SecretString'])
        logger.info(f"Retrieved secret: {name}")
        return {
            'name': name,
            'value': secret_data,
            'version_id': response['VersionId'],
            'created_date': response.get('CreatedDate', '').isoformat()
            if response.get('CreatedDate') else 'N/A'
        }
    except Exception as e:
        logger.error(f"Failed to retrieve secret {name}: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def rotate_secret(name: str, region: str = None) -> Dict[str, Any]:
    """Trigger immediate rotation of a secret."""
    sm = get_sm_client(region)
    try:
        response = sm.rotate_secret(SecretId=name)
        logger.info(f"Rotation triggered for: {name}")
        return {
            'name': name,
            'version_id': response['VersionId'],
            'status': 'rotation_initiated'
        }
    except Exception as e:
        logger.error(f"Rotation failed: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def list_secrets(region: str = None) -> list:
    """List all secrets in the account/region."""
    sm = get_sm_client(region)
    secrets = []
    paginator = sm.get_paginator('list_secrets')
    for page in paginator.paginate():
        for s in page['SecretList']:
            secrets.append({
                'name': s['Name'],
                'description': s.get('Description', ''),
                'last_rotated': s.get('LastRotatedDate', 'Never'),
                'rotation_enabled': s.get('RotationEnabled', False),
            })
    logger.info(f"Found {len(secrets)} secrets")
    return secrets


if __name__ == "__main__":
    print("=" * 60)
    print("Secrets Manager — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials with Secrets Manager access.

    # Create a secret
    create_secret('myapp/db-credentials', {
        'username': 'admin', 'password': 'supersecret', 'host': 'db.example.com'
    })

    # Retrieve a secret
    secret = get_secret('myapp/db-credentials')
    db_password = secret['value']['password']

    # List all secrets
    for s in list_secrets():
        print(f"  {s['name']}: rotation={s['rotation_enabled']}")
    """)
