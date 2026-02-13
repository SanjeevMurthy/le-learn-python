"""
api_integration.py

CircleCI API v2 integration for pipeline and workflow management.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CIRCLECI_API = 'https://circleci.com/api/v2'


def _get_headers():
    return {'Circle-Token': os.environ.get('CIRCLECI_TOKEN', '')}


def list_pipelines(
    project_slug: str,
    branch: Optional[str] = None,
    per_page: int = 20
) -> List[Dict[str, Any]]:
    """
    List recent pipelines for a project.

    project_slug format: gh/org/repo (GitHub) or bb/org/repo (Bitbucket)

    Interview Question:
        Q: What are CircleCI orbs?
        A: Reusable, shareable YAML config packages. Like GitHub Actions
           or Jenkins shared libraries. Types: commands (reusable steps),
           jobs (reusable job definitions), executors (reusable environments).
           Certified orbs: aws-cli, docker, kubernetes, slack.
           Custom orbs: published to CircleCI registry.
    """
    url = f'{CIRCLECI_API}/project/{project_slug}/pipeline'
    params = {'page-token': None}
    if branch:
        params['branch'] = branch

    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()

    pipelines = []
    for p in response.json().get('items', [])[:per_page]:
        pipelines.append({
            'id': p['id'],
            'number': p['number'],
            'state': p['state'],
            'created_at': p['created_at'],
            'trigger_type': p.get('trigger', {}).get('type', 'N/A'),
        })
    return pipelines


def get_pipeline_workflows(pipeline_id: str) -> List[Dict[str, Any]]:
    """Get workflows for a pipeline."""
    url = f'{CIRCLECI_API}/pipeline/{pipeline_id}/workflow'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()

    return [
        {
            'id': w['id'],
            'name': w['name'],
            'status': w['status'],
            'created_at': w['created_at'],
        }
        for w in response.json().get('items', [])
    ]


def trigger_pipeline(
    project_slug: str,
    branch: str = 'main',
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Trigger a new pipeline."""
    url = f'{CIRCLECI_API}/project/{project_slug}/pipeline'
    payload = {'branch': branch}
    if parameters:
        payload['parameters'] = parameters

    response = requests.post(url, headers=_get_headers(), json=payload)
    if response.status_code == 201:
        data = response.json()
        return {'id': data['id'], 'number': data['number'], 'state': data['state']}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("CircleCI API Integration — Usage Examples")
    print("""
    pipelines = list_pipelines('gh/myorg/myrepo')
    trigger_pipeline('gh/myorg/myrepo', branch='develop')
    """)
