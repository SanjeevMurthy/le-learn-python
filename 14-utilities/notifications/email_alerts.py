"""
email_alerts.py

Email alerting utilities.

Prerequisites:
- smtplib (stdlib)
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_alert_email(
    smtp_host: str,
    smtp_port: int,
    from_addr: str,
    to_addrs: List[str],
    subject: str,
    body: str,
    username: str = '',
    password: str = '',
    use_tls: bool = True
) -> Dict[str, Any]:
    """
    Send an alert email via SMTP.

    Interview Question:
        Q: Email vs Slack vs PagerDuty — when to use each?
        A: Email: low-urgency, audit trail, compliance (reports).
           Slack: medium-urgency, team visibility, collaboration.
           PagerDuty: high-urgency, wake people up, on-call routing.
           Best practice: critical alerts → PagerDuty → Slack → email.
           Never rely on email for time-sensitive alerts.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_host, smtp_port)
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)

        server.sendmail(from_addr, to_addrs, msg.as_string())
        server.quit()

        logger.info(f"Alert email sent: {subject}")
        return {'status': 'ok', 'recipients': len(to_addrs)}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def format_alert_body(
    alert_name: str,
    severity: str,
    description: str,
    runbook_url: str = '',
    metrics: Dict[str, Any] = None
) -> str:
    """Format a standardized alert email body."""
    body = f"""
ALERT: {alert_name}
Severity: {severity}
Description: {description}
"""
    if runbook_url:
        body += f"Runbook: {runbook_url}\n"
    if metrics:
        body += "\nMetrics:\n"
        for k, v in metrics.items():
            body += f"  {k}: {v}\n"
    return body.strip()


if __name__ == "__main__":
    body = format_alert_body(
        'High Error Rate', 'CRITICAL',
        'API error rate exceeded 5% for 5 minutes',
        runbook_url='https://wiki.example.com/runbooks/high-error-rate',
        metrics={'error_rate': '7.2%', 'p99_latency': '2.3s'}
    )
    print(f"  {body}")
