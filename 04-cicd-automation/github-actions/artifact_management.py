"""
artifact_management.py

GitHub Actions artifact upload/download via REST API.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GITHUB_API = 'https://api.github.com'


def _get_headers():
    token = os.environ.get('GITHUB_TOKEN', '')
    return {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}


def list_artifacts(owner: str, repo: str, per_page: int = 30) -> List[Dict[str, Any]]:
    """
    List workflow artifacts for a repository.

    Interview Question:
        Q: How do you pass data between jobs in GitHub Actions?
        A: 1. Artifacts: upload/download files between jobs
           2. Outputs: pass small values via step/job outputs
           3. Cache: restore dependencies between runs (not jobs)
           4. Matrix strategy: fan-out/fan-in patterns
           Artifacts expire after 90 days (default). Cache has
           10GB limit per repo.
    """
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/artifacts'
    response = requests.get(url, headers=_get_headers(), params={'per_page': per_page})
    response.raise_for_status()

    artifacts = []
    for a in response.json().get('artifacts', []):
        artifacts.append({
            'id': a['id'],
            'name': a['name'],
            'size_mb': round(a['size_in_bytes'] / (1024 * 1024), 2),
            'expired': a['expired'],
            'created_at': a['created_at'],
        })
    return artifacts


def delete_artifact(owner: str, repo: str, artifact_id: int) -> bool:
    """Delete a workflow artifact."""
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/artifacts/{artifact_id}'
    response = requests.delete(url, headers=_get_headers())
    return response.status_code == 204


if __name__ == "__main__":
    print("Artifact Management — Usage Examples")
    print("""
    artifacts = list_artifacts('myorg', 'myrepo')
    for a in artifacts:
        print(f"  {a['name']}: {a['size_mb']}MB (expired={a['expired']})")
    """)
