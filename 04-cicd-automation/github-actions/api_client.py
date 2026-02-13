"""
api_client.py

GitHub Actions REST API client for workflow management.

Interview Topics:
- GitHub Actions architecture (runners, events, contexts)
- Self-hosted vs GitHub-hosted runners
- OIDC for cloud provider authentication

Production Use Cases:
- Triggering workflows programmatically
- Monitoring workflow runs across repositories
- Managing workflow dispatch events

Prerequisites:
- requests (pip install requests)
- GitHub Personal Access Token
"""

import os
import logging
from typing import List, Dict, Any, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

GITHUB_API = 'https://api.github.com'


def _get_headers() -> Dict[str, str]:
    """Get auth headers from environment."""
    token = os.environ.get('GITHUB_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }


def list_workflow_runs(
    owner: str,
    repo: str,
    status: Optional[str] = None,
    per_page: int = 30
) -> List[Dict[str, Any]]:
    """
    List recent workflow runs for a repository.

    Interview Question:
        Q: Explain GitHub Actions architecture.
        A: Events (push, PR, schedule, workflow_dispatch) trigger
           workflows (.github/workflows/*.yml). Workflows contain jobs.
           Jobs run on runners (GitHub-hosted or self-hosted). Jobs
           contain steps (actions or shell commands). Contexts provide
           runtime data (${{ github.sha }}, ${{ secrets.KEY }}).
           Artifacts persist data between jobs. Caching speeds builds.
    """
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/runs'
    params = {'per_page': per_page}
    if status:
        params['status'] = status  # queued, in_progress, completed

    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()
    data = response.json()

    runs = []
    for run in data.get('workflow_runs', []):
        runs.append({
            'id': run['id'],
            'name': run['name'],
            'status': run['status'],
            'conclusion': run.get('conclusion'),
            'branch': run['head_branch'],
            'sha': run['head_sha'][:7],
            'created_at': run['created_at'],
            'url': run['html_url'],
        })

    logger.info(f"Found {len(runs)} workflow runs for {owner}/{repo}")
    return runs


def trigger_workflow(
    owner: str,
    repo: str,
    workflow_id: str,
    ref: str = 'main',
    inputs: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Trigger a workflow_dispatch event.

    Interview Question:
        Q: How does OIDC authentication work with GitHub Actions?
        A: Instead of storing long-lived cloud credentials as secrets:
           1. Configure cloud provider to trust GitHub's OIDC provider
           2. Workflow requests a short-lived JWT from GitHub
           3. JWT is exchanged for temporary cloud credentials
           4. No secrets to rotate, least privilege per workflow
           Supported: AWS (assume-role-with-oidc), GCP, Azure
    """
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches'
    payload = {'ref': ref}
    if inputs:
        payload['inputs'] = inputs

    response = requests.post(url, headers=_get_headers(), json=payload)
    if response.status_code == 204:
        logger.info(f"Triggered workflow {workflow_id} on {ref}")
        return {'status': 'triggered', 'ref': ref}
    else:
        logger.error(f"Trigger failed: {response.status_code}")
        return {'status': 'error', 'code': response.status_code, 'body': response.text}


def get_workflow_run_logs(owner: str, repo: str, run_id: int) -> str:
    """Download logs for a workflow run."""
    url = f'{GITHUB_API}/repos/{owner}/{repo}/actions/runs/{run_id}/logs'
    response = requests.get(url, headers=_get_headers(), allow_redirects=True)
    if response.status_code == 200:
        return f"Logs downloaded ({len(response.content)} bytes)"
    return f"Failed to download logs: {response.status_code}"


if __name__ == "__main__":
    print("=" * 60)
    print("GitHub Actions API — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Set GITHUB_TOKEN env var.

    # List recent runs
    runs = list_workflow_runs('myorg', 'myrepo', status='completed')
    for r in runs:
        print(f"  {r['name']}: {r['conclusion']} ({r['branch']})")

    # Trigger a workflow
    trigger_workflow('myorg', 'myrepo', 'deploy.yml', ref='main',
                     inputs={'environment': 'staging'})
    """)
