"""
alert_provisioning.py

Grafana alert rule provisioning.

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
    return os.environ.get('GRAFANA_URL', 'http://localhost:3000')


def _get_headers():
    return {'Authorization': f'Bearer {os.environ.get("GRAFANA_TOKEN", "")}',
            'Content-Type': 'application/json'}


def list_alert_rules() -> List[Dict[str, Any]]:
    """List Grafana Unified Alerting rules."""
    url = f'{_get_base_url()}/api/v1/provisioning/alert-rules'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return [
        {'uid': r.get('uid', ''), 'title': r.get('title', ''),
         'condition': r.get('condition', ''), 'folder_uid': r.get('folderUID', '')}
        for r in response.json()
    ]


def list_contact_points() -> List[Dict[str, Any]]:
    """List notification contact points."""
    url = f'{_get_base_url()}/api/v1/provisioning/contact-points'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return [
        {'name': cp.get('name', ''), 'type': cp.get('type', ''),
         'uid': cp.get('uid', '')}
        for cp in response.json()
    ]


if __name__ == "__main__":
    print("Grafana Alert Provisioning — Usage Examples")
    print("""
    for rule in list_alert_rules():
        print(f"  {rule['title']} (uid={rule['uid']})")
    for cp in list_contact_points():
        print(f"  {cp['name']}: {cp['type']}")
    """)
