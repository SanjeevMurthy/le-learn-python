"""
secret_rotation.py

GitHub Actions secret management via REST API.

Interview Topics:
- Secret scoping (org, repo, environment)
- Secret masking in logs
- OIDC vs stored secrets

Prerequisites:
- requests, PyNaCl (pip install requests PyNaCl)
"""

import os
import logging
from typing import Dict, Any, List

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GITHUB_API = 'https://api.github.com'


def _get_headers():
    token = os.environ.get('GITHUB_TOKEN', '')
    return {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}


def list_repo_secrets(owner: str, repo: str) -> List[Dict[str, str]]:
    """
    List repository secrets (names only — values are never exposed).

    Interview Question:
        Q: How are secrets secured in GitHub Actions?
        A: 1. Encrypted at rest with Libsodium sealed boxes
           2. Never exposed in logs (automatically masked)
           3. Not passed to workflows triggered from forks
           4. Scoped: org-level, repo-level, environment-level
           5. Environment secrets require deployment approval
           6. OIDC preferred over stored secrets for cloud auth
    """
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/secrets'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()

    return [
        {'name': s['name'], 'updated_at': s['updated_at']}
        for s in response.json().get('secrets', [])
    ]


def update_repo_secret(owner: str, repo: str, secret_name: str, secret_value: str) -> bool:
    """
    Create or update a repository secret.

    Uses Libsodium sealed box encryption with the repo's public key.
    """
    # Get the repo's public key for encryption
    key_url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/secrets/public-key'
    key_resp = requests.get(key_url, headers=_get_headers())
    key_resp.raise_for_status()
    key_data = key_resp.json()

    # Encrypt the secret value
    try:
        from nacl.public import SealedBox, PublicKey
        import base64
        public_key = PublicKey(base64.b64decode(key_data['key']))
        sealed = SealedBox(public_key)
        encrypted = sealed.encrypt(secret_value.encode())
        encrypted_b64 = base64.b64encode(encrypted).decode()
    except ImportError:
        logger.error("PyNaCl not installed — pip install PyNaCl")
        return False

    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/secrets/{secret_name}'
    response = requests.put(url, headers=_get_headers(), json={
        'encrypted_value': encrypted_b64,
        'key_id': key_data['key_id'],
    })

    success = response.status_code in (201, 204)
    if success:
        logger.info(f"Updated secret: {secret_name}")
    return success


if __name__ == "__main__":
    print("Secret Rotation — Usage Examples")
    print("""
    # List secrets
    for s in list_repo_secrets('myorg', 'myrepo'):
        print(f"  {s['name']}: updated {s['updated_at']}")

    # Rotate a secret
    update_repo_secret('myorg', 'myrepo', 'DEPLOY_KEY', 'new-value')
    """)
