"""
pipeline_api.py

GitLab CI/CD Pipeline API integration.

Interview Topics:
- GitLab CI vs GitHub Actions architecture
- Pipeline stages, jobs, and runners
- Auto DevOps and CI templates

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return os.environ.get('GITLAB_URL', 'https://gitlab.com') + '/api/v4'


def _get_headers() -> Dict[str, str]:
    return {'PRIVATE-TOKEN': os.environ.get('GITLAB_TOKEN', '')}


def list_pipelines(
    project_id: int,
    status: Optional[str] = None,
    ref: Optional[str] = None,
    per_page: int = 20
) -> List[Dict[str, Any]]:
    """
    List pipelines for a GitLab project.

    Interview Question:
        Q: How does GitLab CI differ from GitHub Actions?
        A: GitLab: .gitlab-ci.yml, stages-based (sequential stages,
           parallel jobs within stages), shared/group/project runners,
           built-in Docker registry, environments with deploy boards,
           Auto DevOps for zero-config CI/CD.
           GitHub: event-driven workflows, matrix strategy for parallel,
           marketplace actions, reusable workflows, OIDC integration.
           GitLab advantage: tighter integration (MR → pipeline → deploy).
    """
    url = f'{_get_base_url()}/projects/{project_id}/pipelines'
    params = {'per_page': per_page}
    if status:
        params['status'] = status
    if ref:
        params['ref'] = ref

    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()

    pipelines = []
    for p in response.json():
        pipelines.append({
            'id': p['id'],
            'status': p['status'],
            'ref': p['ref'],
            'sha': p['sha'][:7],
            'source': p.get('source', 'N/A'),
            'created_at': p['created_at'],
            'web_url': p['web_url'],
        })

    logger.info(f"Found {len(pipelines)} pipelines for project {project_id}")
    return pipelines


def trigger_pipeline(
    project_id: int,
    ref: str = 'main',
    variables: Optional[Dict[str, str]] = None,
    trigger_token: Optional[str] = None
) -> Dict[str, Any]:
    """Trigger a new pipeline on a branch or tag."""
    url = f'{_get_base_url()}/projects/{project_id}/trigger/pipeline'
    payload = {
        'ref': ref,
        'token': trigger_token or os.environ.get('GITLAB_TRIGGER_TOKEN', ''),
    }
    if variables:
        for k, v in variables.items():
            payload[f'variables[{k}]'] = v

    response = requests.post(url, data=payload)
    if response.status_code == 201:
        data = response.json()
        logger.info(f"Triggered pipeline {data['id']} on {ref}")
        return {'id': data['id'], 'status': data['status'], 'web_url': data['web_url']}
    return {'status': 'error', 'code': response.status_code}


def retry_pipeline(project_id: int, pipeline_id: int) -> Dict[str, Any]:
    """Retry a failed pipeline."""
    url = f'{_get_base_url()}/projects/{project_id}/pipelines/{pipeline_id}/retry'
    response = requests.post(url, headers=_get_headers())
    if response.status_code == 201:
        logger.info(f"Retried pipeline {pipeline_id}")
        return response.json()
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("GitLab Pipeline API — Usage Examples")
    print("""
    pipelines = list_pipelines(12345, status='failed')
    trigger_pipeline(12345, ref='release/v1.2')
    """)
