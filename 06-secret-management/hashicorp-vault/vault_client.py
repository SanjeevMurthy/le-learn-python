"""
vault_client.py

HashiCorp Vault client for KV secret management.

Interview Topics:
- Vault architecture (storage backends, seal/unseal)
- Authentication methods (token, AppRole, K8s, OIDC)
- Secret engines (KV, database, PKI, transit)

Prerequisites:
- hvac (pip install hvac)
"""

import os
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_client():
    """Create an authenticated Vault client."""
    import hvac
    client = hvac.Client(
        url=os.environ.get('VAULT_ADDR', 'http://127.0.0.1:8200'),
        token=os.environ.get('VAULT_TOKEN', ''),
    )
    return client


def read_secret(path: str, mount_point: str = 'secret') -> Dict[str, Any]:
    """
    Read a KV v2 secret from Vault.

    Interview Question:
        Q: Explain Vault's seal/unseal mechanism.
        A: Vault encrypts data at rest. The master key is split
           using Shamir's Secret Sharing into N key shares.
           Unsealing requires a threshold (e.g., 3 of 5 shares).
           No single person can unseal alone (separation of duties).
           Auto-unseal available via cloud KMS (AWS KMS, GCP KMS).
           When sealed, Vault can't read or write ANY data.
    """
    client = _get_client()
    try:
        response = client.secrets.kv.v2.read_secret_version(path, mount_point=mount_point)
        data = response.get('data', {}).get('data', {})
        metadata = response.get('data', {}).get('metadata', {})
        logger.info(f"Read secret: {path} (version {metadata.get('version')})")
        return {'data': data, 'version': metadata.get('version'), 'status': 'ok'}
    except Exception as e:
        logger.error(f"Failed to read secret: {e}")
        return {'status': 'error', 'error': str(e)}


def write_secret(path: str, data: Dict[str, str], mount_point: str = 'secret') -> Dict[str, Any]:
    """Write a KV v2 secret to Vault."""
    client = _get_client()
    try:
        response = client.secrets.kv.v2.create_or_update_secret(
            path, secret=data, mount_point=mount_point
        )
        version = response.get('data', {}).get('version')
        logger.info(f"Wrote secret: {path} (version {version})")
        return {'path': path, 'version': version, 'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def list_secrets(path: str = '', mount_point: str = 'secret') -> List[str]:
    """List secrets under a path."""
    client = _get_client()
    try:
        response = client.secrets.kv.v2.list_secrets(path, mount_point=mount_point)
        keys = response.get('data', {}).get('keys', [])
        logger.info(f"Listed {len(keys)} secrets under {path}")
        return keys
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        return []


def delete_secret(path: str, mount_point: str = 'secret') -> Dict[str, Any]:
    """Delete a secret (soft delete in KV v2)."""
    client = _get_client()
    try:
        client.secrets.kv.v2.delete_metadata_and_all_versions(path, mount_point=mount_point)
        logger.info(f"Deleted secret: {path}")
        return {'path': path, 'status': 'deleted'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Vault Client — Usage Examples")
    print("""
    # Read a secret
    secret = read_secret('myapp/config')
    print(f"  DB password: {secret['data'].get('db_password')}")

    # Write a secret
    write_secret('myapp/config', {'db_password': 'new_pass', 'api_key': 'xyz'})

    # List secrets
    for key in list_secrets('myapp'):
        print(f"  {key}")
    """)
