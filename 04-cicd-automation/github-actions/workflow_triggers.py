"""
workflow_triggers.py

GitHub Actions workflow trigger management and event handling.

Interview Topics:
- Event types (push, pull_request, schedule, workflow_dispatch)
- Reusable workflows and composite actions
- Concurrency control

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GITHUB_API = 'https://api.github.com'


def _get_headers():
    token = os.environ.get('GITHUB_TOKEN', '')
    return {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}


def list_workflows(owner: str, repo: str) -> List[Dict[str, Any]]:
    """
    List all workflows in a repository.

    Interview Question:
        Q: What are reusable workflows and when to use them?
        A: Reusable workflows are called from other workflows using
           `uses: org/repo/.github/workflows/reusable.yml@main`.
           Benefits: DRY, centralized pipeline definitions, consistent
           across repos. Limitations: max 4 levels of nesting,
           caller/called share secrets explicitly. Use for common
           patterns: build, test, deploy, security scanning.
    """
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/workflows'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()

    workflows = []
    for wf in response.json().get('workflows', []):
        workflows.append({
            'id': wf['id'],
            'name': wf['name'],
            'path': wf['path'],
            'state': wf['state'],
        })
    return workflows


def create_repository_dispatch(
    owner: str, repo: str, event_type: str,
    client_payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Trigger a repository_dispatch event for cross-repo workflows."""
    url = f'{GITHUB_API}/repos/{owner}/{repo}/dispatches'
    payload = {'event_type': event_type}
    if client_payload:
        payload['client_payload'] = client_payload

    response = requests.post(url, headers=_get_headers(), json=payload)
    if response.status_code == 204:
        logger.info(f"Dispatched '{event_type}' to {owner}/{repo}")
        return {'status': 'dispatched', 'event_type': event_type}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("=" * 60)
    print("Workflow Triggers — Usage Examples")
    print("=" * 60)
    print("""
    # List workflows
    for wf in list_workflows('myorg', 'myrepo'):
        print(f"  {wf['name']}: {wf['state']}")

    # Cross-repo trigger
    create_repository_dispatch('myorg', 'deploy-repo', 'deploy',
                               client_payload={'version': '1.2.3'})
    """)
