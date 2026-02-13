"""
pagerduty_integration.py

PagerDuty incident management.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PAGERDUTY_EVENTS_URL = 'https://events.pagerduty.com/v2/enqueue'


def trigger_incident(
    routing_key: str,
    summary: str,
    severity: str = 'critical',
    source: str = 'monitoring',
    dedup_key: str = '',
    custom_details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Trigger a PagerDuty incident via Events API v2.

    Interview Question:
        Q: How do you implement effective on-call alerting?
        A: 1. Dedup key: same issue → same incident (avoid duplicate pages)
           2. Severity: critical/error/warning/info
           3. Escalation policies: primary → secondary → manager
           4. Maintenance windows: suppress alerts during planned work
           5. Alert grouping: related alerts → single incident
           Key metric: MTTA (Mean Time To Acknowledge) < 5 minutes.
    """
    try:
        import requests
        payload = {
            'routing_key': routing_key,
            'event_action': 'trigger',
            'payload': {
                'summary': summary,
                'severity': severity,
                'source': source,
                'custom_details': custom_details or {},
            },
        }
        if dedup_key:
            payload['dedup_key'] = dedup_key

        response = requests.post(PAGERDUTY_EVENTS_URL, json=payload, timeout=10)
        result = response.json()
        return {
            'status': result.get('status', 'error'),
            'dedup_key': result.get('dedup_key', dedup_key),
        }
    except ImportError:
        return {'status': 'error', 'error': 'requests not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def resolve_incident(routing_key: str, dedup_key: str) -> Dict[str, Any]:
    """Resolve a PagerDuty incident."""
    try:
        import requests
        payload = {
            'routing_key': routing_key,
            'event_action': 'resolve',
            'dedup_key': dedup_key,
        }
        response = requests.post(PAGERDUTY_EVENTS_URL, json=payload, timeout=10)
        return {'status': response.json().get('status', 'error')}
    except ImportError:
        return {'status': 'error', 'error': 'requests not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("PagerDuty Integration — Usage Examples")
    print("""
    trigger_incident(
        routing_key='your-pd-routing-key',
        summary='Production database connection pool exhausted',
        severity='critical',
        dedup_key='db-pool-exhausted-prod',
        custom_details={'pool_usage': '100%', 'affected_service': 'api-gateway'}
    )
    """)
