"""
slack_notifier.py

Slack notification utilities.

Prerequisites:
- requests (pip install requests)
"""

import json
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_slack_message(
    webhook_url: str,
    text: str,
    channel: str = '',
    username: str = 'DevOps Bot',
    icon_emoji: str = ':robot_face:'
) -> Dict[str, Any]:
    """
    Send a message via Slack Incoming Webhook.

    Interview Question:
        Q: How do you design alerting notifications?
        A: 1. Severity-based routing (critical → PagerDuty, warning → Slack)
           2. Avoid alert fatigue: group related alerts
           3. Include actionable context (runbook link, metrics)
           4. Acknowledge mechanism (reduce duplicate pages)
           5. Escalation: if not ack'd in 15 min → escalate
           6. Rate limit notifications to avoid spam
    """
    try:
        import requests
        payload = {'text': text, 'username': username, 'icon_emoji': icon_emoji}
        if channel:
            payload['channel'] = channel

        response = requests.post(webhook_url, json=payload, timeout=10)
        return {
            'status': 'ok' if response.status_code == 200 else 'error',
            'status_code': response.status_code,
        }
    except ImportError:
        return {'status': 'error', 'error': 'requests not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def send_slack_block_message(
    webhook_url: str,
    title: str,
    fields: Dict[str, str],
    color: str = '#36a64f',
    footer: str = ''
) -> Dict[str, Any]:
    """Send a rich Slack message with attachments."""
    try:
        import requests
        attachment = {
            'color': color,
            'title': title,
            'fields': [
                {'title': k, 'value': v, 'short': len(v) < 40}
                for k, v in fields.items()
            ],
        }
        if footer:
            attachment['footer'] = footer

        payload = {'attachments': [attachment]}
        response = requests.post(webhook_url, json=payload, timeout=10)
        return {'status': 'ok' if response.status_code == 200 else 'error'}
    except ImportError:
        return {'status': 'error', 'error': 'requests not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Slack Notifier — Usage Examples")
    print("""
    send_slack_message(
        webhook_url='https://hooks.slack.com/services/T.../B.../xxx',
        text='🚨 Production alert: High error rate on api-gateway'
    )
    """)
