"""
ci_variable_management.py

GitLab CI/CD variable (secret) management.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('GITLAB_URL', 'https://gitlab.com') + '/api/v4'


def _get_headers():
    return {'PRIVATE-TOKEN': os.environ.get('GITLAB_TOKEN', '')}


def list_variables(project_id: int) -> List[Dict[str, Any]]:
    """List CI/CD variables (masked values are hidden)."""
    url = f'{_get_base_url()}/projects/{project_id}/variables'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()

    return [
        {
            'key': v['key'],
            'masked': v.get('masked', False),
            'protected': v.get('protected', False),
            'environment_scope': v.get('environment_scope', '*'),
        }
        for v in response.json()
    ]


def create_variable(
    project_id: int, key: str, value: str,
    masked: bool = True, protected: bool = False,
    environment_scope: str = '*'
) -> Dict[str, Any]:
    """
    Create a CI/CD variable.

    Interview Question:
        Q: What's the difference between protected and masked variables?
        A: Protected: only available in pipelines on protected branches/tags.
           Prevents exposure in feature branch builds.
           Masked: value is hidden in job logs (***).
           Requirements for masking: >= 8 chars, no whitespace, single line.
           Best practice: use both for sensitive values on prod branches.
    """
    url = f'{_get_base_url()}/projects/{project_id}/variables'
    payload = {
        'key': key, 'value': value, 'masked': masked,
        'protected': protected, 'environment_scope': environment_scope,
    }
    response = requests.post(url, headers=_get_headers(), json=payload)
    if response.status_code == 201:
        logger.info(f"Created variable: {key}")
        return {'key': key, 'status': 'created'}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("CI Variable Management — Usage Examples")
    print("""
    for v in list_variables(12345):
        print(f"  {v['key']}: masked={v['masked']}, scope={v['environment_scope']}")
    """)
