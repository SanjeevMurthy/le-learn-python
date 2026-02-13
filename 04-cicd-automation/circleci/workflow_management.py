"""
workflow_management.py

CircleCI workflow management and monitoring.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CIRCLECI_API = 'https://circleci.com/api/v2'


def _get_headers():
    return {'Circle-Token': os.environ.get('CIRCLECI_TOKEN', '')}


def get_workflow_jobs(workflow_id: str) -> List[Dict[str, Any]]:
    """Get jobs in a workflow."""
    url = f'{CIRCLECI_API}/workflow/{workflow_id}/job'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()

    return [
        {
            'name': j['name'],
            'status': j['status'],
            'type': j['type'],
            'started_at': j.get('started_at'),
            'stopped_at': j.get('stopped_at'),
            'job_number': j.get('job_number'),
        }
        for j in response.json().get('items', [])
    ]


def rerun_workflow(workflow_id: str, from_failed: bool = True) -> Dict[str, Any]:
    """
    Rerun a workflow (all jobs or from failed).

    Interview Question:
        Q: How do you optimize CI/CD pipeline speed?
        A: 1. Caching (deps, Docker layers, build artifacts)
           2. Parallelism (split tests, matrix builds)
           3. Incremental builds (only rebuild changed code)
           4. Resource classes (larger machines for heavy tasks)
           5. Docker layer caching
           6. Rerun from failed (skip passed jobs)
           7. Selective pipelines (path-based triggers)
    """
    url = f'{CIRCLECI_API}/workflow/{workflow_id}/rerun'
    payload = {'from_failed': from_failed}
    response = requests.post(url, headers=_get_headers(), json=payload)

    if response.status_code == 202:
        return {'workflow_id': workflow_id, 'status': 'rerunning', 'from_failed': from_failed}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("CircleCI Workflow Management — Usage Examples")
    print("""
    jobs = get_workflow_jobs('workflow-uuid')
    for j in jobs:
        print(f"  {j['name']}: {j['status']}")

    rerun_workflow('workflow-uuid', from_failed=True)
    """)
