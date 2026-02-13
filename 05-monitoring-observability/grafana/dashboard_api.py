"""
dashboard_api.py

Grafana dashboard management via REST API.

Prerequisites:
- requests (pip install requests)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('GRAFANA_URL', 'http://localhost:3000')


def _get_headers():
    token = os.environ.get('GRAFANA_TOKEN', '')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


def search_dashboards(query: str = '', tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search Grafana dashboards.

    Interview Question:
        Q: What is dashboard-as-code?
        A: Version-controlled dashboard definitions using:
           1. Grafana provisioning: YAML config + JSON dashboards
              in /etc/grafana/provisioning/dashboards/
           2. Terraform grafana provider
           3. Grafonnet (Jsonnet library for Grafana)
           4. Grafana API for programmatic management
           Benefits: reproducible, review via PRs, consistent across envs.
    """
    url = f'{_get_base_url()}/api/search'
    params = {'query': query, 'type': 'dash-db'}
    if tag:
        params['tag'] = tag

    response = requests.get(url, headers=_get_headers(), params=params)
    response.raise_for_status()

    return [
        {
            'uid': d['uid'],
            'title': d['title'],
            'folder': d.get('folderTitle', 'General'),
            'url': d['url'],
            'tags': d.get('tags', []),
        }
        for d in response.json()
    ]


def get_dashboard(uid: str) -> Dict[str, Any]:
    """Get dashboard JSON by UID."""
    url = f'{_get_base_url()}/api/dashboards/uid/{uid}'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return response.json()


def create_dashboard(
    title: str,
    panels: List[Dict[str, Any]],
    folder_id: int = 0,
    overwrite: bool = False
) -> Dict[str, Any]:
    """Create or update a dashboard programmatically."""
    dashboard = {
        'title': title,
        'panels': panels,
        'timezone': 'browser',
        'schemaVersion': 36,
    }

    url = f'{_get_base_url()}/api/dashboards/db'
    payload = {
        'dashboard': dashboard,
        'folderId': folder_id,
        'overwrite': overwrite,
    }

    response = requests.post(url, headers=_get_headers(), json=payload)
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Dashboard created: {title}")
        return {'uid': data.get('uid'), 'url': data.get('url'), 'status': 'created'}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("Grafana Dashboard API — Usage Examples")
    print("""
    dashboards = search_dashboards(tag='kubernetes')
    for d in dashboards:
        print(f"  {d['title']} ({d['folder']})")
    """)
