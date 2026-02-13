"""
build_triggers.py

Jenkins build trigger automation.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, Optional

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


def get_crumb() -> Optional[Dict[str, str]]:
    """
    Get Jenkins CSRF crumb for POST requests.

    Interview Question:
        Q: How does Jenkins CSRF protection work?
        A: Jenkins generates a crumb (token) per session. All POST
           requests must include the crumb header. Get it via
           /crumbIssuer/api/json. In pipelines, use
           'Jenkins-Crumb' header. Disable CSRF only in dev.
    """
    url = f'{_get_base_url()}/crumbIssuer/api/json'
    try:
        response = requests.get(url, auth=_get_auth())
        if response.status_code == 200:
            data = response.json()
            return {data['crumbRequestField']: data['crumb']}
    except Exception:
        pass
    return None


def trigger_parameterized_build(
    job_name: str,
    parameters: Dict[str, str],
    wait: bool = False
) -> Dict[str, Any]:
    """Trigger a parameterized Jenkins build."""
    url = f'{_get_base_url()}/job/{job_name}/buildWithParameters'
    headers = get_crumb() or {}

    response = requests.post(url, auth=_get_auth(), headers=headers, params=parameters)
    if response.status_code in (200, 201):
        logger.info(f"Triggered {job_name} with params: {parameters}")
        return {'job': job_name, 'status': 'queued', 'parameters': parameters}
    return {'status': 'error', 'code': response.status_code}


def trigger_multibranch_scan(job_name: str) -> Dict[str, Any]:
    """Trigger a multibranch pipeline scan."""
    url = f'{_get_base_url()}/job/{job_name}/build'
    headers = get_crumb() or {}

    response = requests.post(url, auth=_get_auth(), headers=headers)
    if response.status_code in (200, 201):
        logger.info(f"Triggered scan for {job_name}")
        return {'job': job_name, 'status': 'scanning'}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("Jenkins Build Triggers — Usage Examples")
    print("""
    trigger_parameterized_build('deploy', {'ENV': 'staging', 'VERSION': '1.2.3'})
    trigger_multibranch_scan('my-service')
    """)
