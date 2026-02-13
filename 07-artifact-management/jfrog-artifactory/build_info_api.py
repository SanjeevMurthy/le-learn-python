"""
build_info_api.py

Artifactory Build Info API integration.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, List

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_auth():
    return HTTPBasicAuth(
        os.environ.get('ARTIFACTORY_USER', 'admin'),
        os.environ.get('ARTIFACTORY_TOKEN', '')
    )


def _get_base_url():
    return os.environ.get('ARTIFACTORY_URL', 'http://localhost:8082/artifactory')


def get_build_info(build_name: str, build_number: str) -> Dict[str, Any]:
    """
    Get build info for traceability.

    Interview Question:
        Q: Why is build traceability important?
        A: Links artifact → build → source code → dependencies.
           Needed for: security audits (what's in prod?),
           vulnerability response (which builds use log4j?),
           compliance (prove what was deployed), rollback decisions.
           Build info captures: modules, dependencies, environment,
           VCS revision, build agent, timestamps.
    """
    url = f'{_get_base_url()}/api/build/{build_name}/{build_number}'
    response = requests.get(url, auth=_get_auth())

    if response.status_code == 200:
        data = response.json().get('buildInfo', {})
        return {
            'name': data.get('name', ''),
            'number': data.get('number', ''),
            'started': data.get('started', ''),
            'version': data.get('version', ''),
            'modules': len(data.get('modules', [])),
            'status': 'ok',
        }
    return {'status': 'error', 'code': response.status_code}


def list_builds() -> List[Dict[str, Any]]:
    """List all builds in Artifactory."""
    url = f'{_get_base_url()}/api/build'
    response = requests.get(url, auth=_get_auth())
    response.raise_for_status()
    return [
        {'name': b.get('uri', '').strip('/'), 'last_started': b.get('lastStarted', '')}
        for b in response.json().get('builds', [])
    ]


if __name__ == "__main__":
    print("Build Info API — Usage Examples")
    print("""
    for build in list_builds():
        print(f"  {build['name']}: {build['last_started']}")

    info = get_build_info('my-service', '42')
    """)
