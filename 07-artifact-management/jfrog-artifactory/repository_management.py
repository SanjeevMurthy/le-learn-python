"""
repository_management.py

Artifactory repository CRUD operations.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_auth():
    return HTTPBasicAuth(
        os.environ.get('ARTIFACTORY_USER', 'admin'),
        os.environ.get('ARTIFACTORY_TOKEN', '')
    )


def _get_base_url():
    return os.environ.get('ARTIFACTORY_URL', 'http://localhost:8082/artifactory')


def list_repositories(repo_type: str = '') -> List[Dict[str, Any]]:
    """List all repositories, optionally filtered by type."""
    url = f'{_get_base_url()}/api/repositories'
    params = {}
    if repo_type:
        params['type'] = repo_type  # local, remote, virtual, federated

    response = requests.get(url, auth=_get_auth(), params=params)
    response.raise_for_status()
    return [
        {'key': r['key'], 'type': r.get('type', ''),
         'package_type': r.get('packageType', ''), 'url': r.get('url', '')}
        for r in response.json()
    ]


def create_local_repository(
    key: str, package_type: str = 'generic', description: str = ''
) -> Dict[str, Any]:
    """Create a local repository."""
    url = f'{_get_base_url()}/api/repositories/{key}'
    payload = {
        'key': key,
        'rclass': 'local',
        'packageType': package_type,
        'description': description,
    }
    response = requests.put(url, auth=_get_auth(), json=payload)
    if response.status_code in (200, 201):
        logger.info(f"Created repo: {key}")
        return {'key': key, 'status': 'created'}
    return {'status': 'error', 'code': response.status_code}


def get_storage_summary() -> Dict[str, Any]:
    """Get overall storage summary."""
    url = f'{_get_base_url()}/api/storageinfo'
    response = requests.get(url, auth=_get_auth())
    response.raise_for_status()
    data = response.json()
    return {
        'total_space': data.get('fileStoreSummary', {}).get('totalSpace', ''),
        'used_space': data.get('fileStoreSummary', {}).get('usedSpace', ''),
        'free_space': data.get('fileStoreSummary', {}).get('freeSpace', ''),
        'total_items': data.get('binariesSummary', {}).get('artifactsCount', 0),
    }


if __name__ == "__main__":
    print("Repository Management — Usage Examples")
    print("""
    for repo in list_repositories('local'):
        print(f"  {repo['key']}: {repo['package_type']}")
    """)
