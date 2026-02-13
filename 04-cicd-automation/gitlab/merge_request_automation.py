"""
merge_request_automation.py

GitLab Merge Request (MR) automation.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('GITLAB_URL', 'https://gitlab.com') + '/api/v4'


def _get_headers():
    return {'PRIVATE-TOKEN': os.environ.get('GITLAB_TOKEN', '')}


def list_merge_requests(
    project_id: int,
    state: str = 'opened',
    per_page: int = 20
) -> List[Dict[str, Any]]:
    """
    List merge requests with pipeline status.

    Interview Question:
        Q: How do you enforce code quality in GitLab CI?
        A: 1. MR pipelines: run tests before merge
           2. Code review approvals (CODEOWNERS)
           3. Merge checks: pipeline must pass, no conflicts
           4. SAST/DAST scanning in pipeline
           5. Code coverage thresholds
           6. Protected branches require approval
    """
    url = f'{_get_base_url()}/projects/{project_id}/merge_requests'
    params = {'state': state, 'per_page': per_page}
    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()

    mrs = []
    for mr in response.json():
        mrs.append({
            'iid': mr['iid'],
            'title': mr['title'],
            'author': mr['author']['username'],
            'source_branch': mr['source_branch'],
            'target_branch': mr['target_branch'],
            'state': mr['state'],
            'pipeline_status': mr.get('head_pipeline', {}).get('status') if mr.get('head_pipeline') else 'N/A',
            'web_url': mr['web_url'],
        })
    return mrs


def create_merge_request(
    project_id: int,
    source_branch: str,
    target_branch: str = 'main',
    title: str = '',
    description: str = '',
    remove_source: bool = True
) -> Dict[str, Any]:
    """Create a merge request."""
    url = f'{_get_base_url()}/projects/{project_id}/merge_requests'
    payload = {
        'source_branch': source_branch,
        'target_branch': target_branch,
        'title': title or f"Merge {source_branch} into {target_branch}",
        'description': description,
        'remove_source_branch': remove_source,
    }

    response = requests.post(url, headers=_get_headers(), json=payload)
    if response.status_code == 201:
        data = response.json()
        logger.info(f"Created MR !{data['iid']}: {data['title']}")
        return {'iid': data['iid'], 'web_url': data['web_url'], 'status': 'created'}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("GitLab MR Automation — Usage Examples")
    print("""
    mrs = list_merge_requests(12345, state='opened')
    create_merge_request(12345, 'feature/new', 'main', title='Add new feature')
    """)
