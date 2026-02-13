"""
datasource_management.py

Grafana datasource CRUD operations.

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


def list_datasources() -> List[Dict[str, Any]]:
    """List all configured datasources."""
    url = f'{_get_base_url()}/api/datasources'
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return [
        {'id': ds['id'], 'name': ds['name'], 'type': ds['type'],
         'url': ds.get('url', ''), 'is_default': ds.get('isDefault', False)}
        for ds in response.json()
    ]


def create_prometheus_datasource(
    name: str, url: str, is_default: bool = False
) -> Dict[str, Any]:
    """Add a Prometheus datasource."""
    api_url = f'{_get_base_url()}/api/datasources'
    payload = {
        'name': name, 'type': 'prometheus', 'url': url,
        'access': 'proxy', 'isDefault': is_default,
    }
    response = requests.post(api_url, headers=_get_headers(), json=payload)
    if response.status_code == 200:
        logger.info(f"Created datasource: {name}")
        return response.json()
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("Grafana Datasource Management — Usage Examples")
    print("""
    for ds in list_datasources():
        print(f"  {ds['name']}: {ds['type']} ({ds['url']})")
    create_prometheus_datasource('prod-prometheus', 'http://prometheus:9090')
    """)
