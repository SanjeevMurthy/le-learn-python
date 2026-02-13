"""
alert_manager.py

Prometheus AlertManager API integration.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('ALERTMANAGER_URL', 'http://localhost:9093')


def list_alerts(active: bool = True) -> List[Dict[str, Any]]:
    """
    List current alerts from AlertManager.

    Interview Question:
        Q: How does AlertManager handle alerts?
        A: 1. Grouping: combines similar alerts into one notification
           2. Inhibition: suppresses alerts when related alert is firing
           3. Silencing: mutes alerts for a time period
           4. Routing: sends alerts to correct receiver (Slack, PD, email)
           Routes are matched by labels (severity, team, service).
           Deduplication prevents duplicate notifications.
    """
    url = f'{_get_base_url()}/api/v2/alerts'
    params = {'active': str(active).lower()}
    response = requests.get(url, params=params)
    response.raise_for_status()

    alerts = []
    for alert in response.json():
        alerts.append({
            'name': alert['labels'].get('alertname', 'N/A'),
            'severity': alert['labels'].get('severity', 'N/A'),
            'state': alert['status']['state'],
            'summary': alert.get('annotations', {}).get('summary', ''),
            'starts_at': alert.get('startsAt', ''),
            'labels': alert['labels'],
        })
    return alerts


def create_silence(
    matchers: List[Dict[str, str]],
    duration_hours: int = 4,
    comment: str = '',
    created_by: str = 'devops-toolkit'
) -> Dict[str, Any]:
    """Create a silence in AlertManager."""
    now = datetime.now(timezone.utc)
    ends_at = now + timedelta(hours=duration_hours)

    payload = {
        'matchers': matchers,
        'startsAt': now.isoformat(),
        'endsAt': ends_at.isoformat(),
        'comment': comment or f'Silenced for {duration_hours}h',
        'createdBy': created_by,
    }

    url = f'{_get_base_url()}/api/v2/silences'
    response = requests.post(url, json=payload)
    if response.status_code in (200, 201):
        return {'silence_id': response.json().get('silenceID'), 'status': 'created'}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("AlertManager API — Usage Examples")
    print("""
    alerts = list_alerts()
    for a in alerts:
        print(f"  [{a['severity']}] {a['name']}: {a['summary']}")

    # Silence alerts for maintenance
    create_silence(
        [{'name': 'alertname', 'value': 'HighCPU', 'isRegex': False}],
        duration_hours=2, comment='Planned maintenance'
    )
    """)
