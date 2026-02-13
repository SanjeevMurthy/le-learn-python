"""
plugin_management.py

Jenkins plugin management via REST API.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any

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


def list_plugins(active_only: bool = True) -> List[Dict[str, Any]]:
    """
    List installed Jenkins plugins.

    Interview Question:
        Q: What are essential Jenkins plugins for a CI/CD pipeline?
        A: Pipeline (required for Jenkinsfile), Blue Ocean (UI),
           Git, Credentials Binding, Docker Pipeline,
           Kubernetes (dynamic agents), Configuration as Code (JCasC),
           Shared Groovy Libraries, Warnings Next Gen (code quality),
           Slack/Teams notifications.
    """
    url = f'{_get_base_url()}/pluginManager/api/json'
    params = {'depth': 1}
    response = requests.get(url, auth=_get_auth(), params=params)
    response.raise_for_status()

    plugins = []
    for p in response.json().get('plugins', []):
        if active_only and not p['active']:
            continue
        plugins.append({
            'name': p['shortName'],
            'version': p['version'],
            'active': p['active'],
            'has_update': p.get('hasUpdate', False),
        })

    logger.info(f"Found {len(plugins)} plugins")
    return plugins


def check_plugin_updates() -> List[Dict[str, str]]:
    """Find plugins with available updates."""
    plugins = list_plugins()
    return [p for p in plugins if p['has_update']]


if __name__ == "__main__":
    print("Jenkins Plugin Management — Usage Examples")
    print("""
    plugins = list_plugins()
    for p in plugins:
        print(f"  {p['name']}: v{p['version']} (update={p['has_update']})")
    """)
