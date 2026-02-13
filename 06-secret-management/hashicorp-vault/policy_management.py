"""
policy_management.py

Vault ACL policy management.

Prerequisites:
- hvac (pip install hvac)
"""

import os
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_client():
    import hvac
    return hvac.Client(
        url=os.environ.get('VAULT_ADDR', 'http://127.0.0.1:8200'),
        token=os.environ.get('VAULT_TOKEN', ''),
    )


def list_policies() -> List[str]:
    """
    List all Vault ACL policies.

    Interview Question:
        Q: How does Vault RBAC work?
        A: Policies define permissions (path-based ACL).
           Auth methods (AppRole, K8s, LDAP) map identities to policies.
           Capabilities: create, read, update, delete, list, sudo, deny.
           Best practice: least privilege. Default = deny.
           Example: myapp-policy allows read on secret/data/myapp/*
    """
    client = _get_client()
    return client.sys.list_acl_policies().get('data', {}).get('policies', [])


def create_policy(name: str, rules: str) -> Dict[str, Any]:
    """Create or update a Vault policy."""
    client = _get_client()
    try:
        client.sys.create_or_update_acl_policy(name, rules)
        logger.info(f"Created policy: {name}")
        return {'name': name, 'status': 'created'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


# Common policy templates
POLICY_TEMPLATES = {
    'app_readonly': '''
path "secret/data/{{identity.entity.name}}/*" {
  capabilities = ["read", "list"]
}
''',
    'cicd_deploy': '''
path "secret/data/deploy/*" {
  capabilities = ["read", "list"]
}
path "transit/encrypt/deploy-key" {
  capabilities = ["update"]
}
''',
}


if __name__ == "__main__":
    print("Vault Policy Management — Usage Examples")
    print("""
    policies = list_policies()
    print(f"  Policies: {policies}")

    create_policy('myapp-reader', POLICY_TEMPLATES['app_readonly'])
    """)
