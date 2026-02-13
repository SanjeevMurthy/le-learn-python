"""
snapshot_creator.py

Grafana dashboard snapshot management.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, List

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('GRAFANA_URL', 'http://localhost:3000')


def _get_headers():
    return {'Authorization': f'Bearer {os.environ.get("GRAFANA_TOKEN", "")}',
            'Content-Type': 'application/json'}


def create_snapshot(
    dashboard_uid: str, name: str = '', expires: int = 3600
) -> Dict[str, Any]:
    """Create a dashboard snapshot for sharing."""
    # First get the dashboard
    url = f'{_get_base_url()}/api/dashboards/uid/{dashboard_uid}'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    dashboard = response.json().get('dashboard', {})

    snap_url = f'{_get_base_url()}/api/snapshots'
    payload = {
        'dashboard': dashboard,
        'name': name or dashboard.get('title', 'Snapshot'),
        'expires': expires,
    }
    response = requests.post(snap_url, headers=_get_headers(), json=payload)
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Snapshot created: {data.get('url', '')}")
        return {'url': data.get('url'), 'key': data.get('key'), 'delete_key': data.get('deleteKey')}
    return {'status': 'error', 'code': response.status_code}


def list_snapshots() -> List[Dict[str, Any]]:
    """List dashboard snapshots."""
    url = f'{_get_base_url()}/api/dashboard/snapshots'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return [
        {'name': s.get('name', ''), 'key': s.get('key', ''),
         'created': s.get('created', ''), 'expires': s.get('expires', '')}
        for s in response.json()
    ]


if __name__ == "__main__":
    print("Grafana Snapshot Creator — Usage Examples")
    print("""
    snap = create_snapshot('dashboard-uid', name='Incident Report', expires=86400)
    print(f"  Share URL: {snap['url']}")
    """)
