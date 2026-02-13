"""
job_management.py

Jenkins job management via REST API.

Interview Topics:
- Jenkins architecture (controller, agents, executors)
- Declarative vs Scripted pipelines
- Jenkins shared libraries

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_auth():
    return HTTPBasicAuth(
        os.environ.get('JENKINS_USER', 'admin'),
        os.environ.get('JENKINS_TOKEN', '')
    )


def _get_base_url():
    return os.environ.get('JENKINS_URL', 'http://localhost:8080')


def list_jobs(folder: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all Jenkins jobs.

    Interview Question:
        Q: Explain Jenkins pipeline types.
        A: Declarative: structured syntax, `pipeline { agent, stages }`.
           Easier to write, built-in validation, recommended.
           Scripted: Groovy-based, `node { stage() {} }`.
           More flexible, can use any Groovy construct.
           Shared Libraries: reusable code across pipelines.
           Loaded from Git repo, available via @Library annotation.
    """
    base = _get_base_url()
    url = f'{base}/api/json' if not folder else f'{base}/job/{folder}/api/json'

    response = requests.get(
        url, auth=_get_auth(),
        params={'tree': 'jobs[name,url,color,lastBuild[number,result,timestamp]]'}
    )
    response.raise_for_status()

    jobs = []
    for job in response.json().get('jobs', []):
        last_build = job.get('lastBuild', {})
        jobs.append({
            'name': job['name'],
            'status': job.get('color', 'N/A'),
            'last_build': last_build.get('number') if last_build else None,
            'last_result': last_build.get('result') if last_build else None,
            'url': job['url'],
        })

    logger.info(f"Found {len(jobs)} Jenkins jobs")
    return jobs


def trigger_build(
    job_name: str,
    parameters: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Trigger a Jenkins build."""
    base = _get_base_url()
    if parameters:
        url = f'{base}/job/{job_name}/buildWithParameters'
        response = requests.post(url, auth=_get_auth(), params=parameters)
    else:
        url = f'{base}/job/{job_name}/build'
        response = requests.post(url, auth=_get_auth())

    if response.status_code in (200, 201):
        queue_url = response.headers.get('Location', '')
        logger.info(f"Triggered build: {job_name}")
        return {'job': job_name, 'status': 'queued', 'queue_url': queue_url}
    return {'status': 'error', 'code': response.status_code}


def get_build_info(job_name: str, build_number: int) -> Dict[str, Any]:
    """Get detailed info about a specific build."""
    url = f'{_get_base_url()}/job/{job_name}/{build_number}/api/json'
    response = requests.get(url, auth=_get_auth())
    response.raise_for_status()
    data = response.json()

    return {
        'number': data['number'],
        'result': data.get('result'),
        'building': data['building'],
        'duration_ms': data.get('duration', 0),
        'timestamp': data['timestamp'],
        'url': data['url'],
    }


if __name__ == "__main__":
    print("Jenkins Job Management — Usage Examples")
    print("""
    jobs = list_jobs()
    for j in jobs:
        print(f"  {j['name']}: {j['status']} (build #{j['last_build']})")

    trigger_build('deploy-service', parameters={'ENV': 'staging'})
    """)
