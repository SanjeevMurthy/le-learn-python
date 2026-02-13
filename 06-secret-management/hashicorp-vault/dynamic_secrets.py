"""
dynamic_secrets.py

Vault dynamic secret generation (database, AWS credentials).

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


def get_database_credentials(role: str, mount_point: str = 'database') -> Dict[str, Any]:
    """
    Generate dynamic database credentials.

    Interview Question:
        Q: What are dynamic secrets and why use them?
        A: Dynamic secrets are generated on-demand with a TTL (lease).
           Vault creates credentials when requested, revokes on expiry.
           Benefits:
           1. No long-lived credentials to steal
           2. Each application/pod gets unique credentials
           3. Compromised cred is automatically time-limited
           4. Full audit trail of who requested what
           Example: Vault creates a PostgreSQL user with specific
           grants, auto-drops the user when lease expires.
    """
    client = _get_client()
    try:
        response = client.secrets.database.generate_credentials(role, mount_point=mount_point)
        data = response.get('data', {})
        lease_duration = response.get('lease_duration', 0)

        logger.info(f"Generated DB credentials for role={role}, TTL={lease_duration}s")
        return {
            'username': data.get('username'),
            'password': data.get('password'),
            'lease_id': response.get('lease_id'),
            'lease_duration': lease_duration,
            'status': 'ok',
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def get_aws_credentials(role: str, mount_point: str = 'aws') -> Dict[str, Any]:
    """Generate dynamic AWS credentials via Vault."""
    client = _get_client()
    try:
        response = client.secrets.aws.generate_credentials(role, mount_point=mount_point)
        data = response.get('data', {})
        return {
            'access_key': data.get('access_key'),
            'secret_key': data.get('secret_key'),
            'security_token': data.get('security_token'),
            'lease_duration': response.get('lease_duration', 0),
            'status': 'ok',
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def revoke_lease(lease_id: str) -> Dict[str, Any]:
    """Revoke a secret lease early."""
    client = _get_client()
    try:
        client.sys.revoke_lease(lease_id)
        logger.info(f"Revoked lease: {lease_id}")
        return {'status': 'revoked'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Dynamic Secrets — Usage Examples")
    print("""
    # Get database credentials (auto-expire in 1h)
    creds = get_database_credentials('myapp-role')
    print(f"  User: {creds['username']}, TTL: {creds['lease_duration']}s")

    # Revoke early when done
    revoke_lease(creds['lease_id'])
    """)
