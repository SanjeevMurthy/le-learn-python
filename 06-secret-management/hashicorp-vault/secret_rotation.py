"""
secret_rotation.py

Vault secret rotation automation.

Prerequisites:
- hvac (pip install hvac)
"""

import os
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_client():
    import hvac
    return hvac.Client(
        url=os.environ.get('VAULT_ADDR', 'http://127.0.0.1:8200'),
        token=os.environ.get('VAULT_TOKEN', ''),
    )


def rotate_kv_secret(
    path: str, new_data: Dict[str, str], mount_point: str = 'secret'
) -> Dict[str, Any]:
    """
    Rotate a KV secret (creates new version).

    Interview Question:
        Q: How do you handle secret rotation without downtime?
        A: 1. Dual-credential pattern: write new secret, keep old valid
           2. Application reads latest version on each use
           3. After propagation, disable old credential
           4. Use Vault leases for automatic expiry
           5. K8s: use Vault Agent sidecar for auto-rotation
    """
    client = _get_client()
    try:
        response = client.secrets.kv.v2.create_or_update_secret(
            path, secret=new_data, mount_point=mount_point
        )
        version = response.get('data', {}).get('version')
        logger.info(f"Rotated secret {path} to version {version}")
        return {'path': path, 'version': version, 'status': 'rotated'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Secret Rotation — Usage Examples")
    print("""
    rotate_kv_secret('myapp/db', {'password': 'new_secure_pass_2024'})
    """)
