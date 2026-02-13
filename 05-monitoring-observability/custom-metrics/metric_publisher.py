"""
metric_publisher.py

Publish custom metrics to various backends.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
import time
from typing import Dict, Any, List

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def push_to_pushgateway(
    job: str,
    metrics: Dict[str, float],
    instance: str = '',
    gateway_url: str = ''
) -> Dict[str, Any]:
    """
    Push metrics to Prometheus Pushgateway.

    Interview Question:
        Q: When should you use Pushgateway?
        A: For short-lived jobs (cron, batch, CI/CD) that can't be
           scraped. Push metrics at job completion. IMPORTANT:
           Pushgateway is NOT a cache — metrics persist until deleted.
           Don't use for long-running services (use pull model).
           Delete metrics after they've been scraped.
    """
    url = gateway_url or os.environ.get('PUSHGATEWAY_URL', 'http://localhost:9091')
    endpoint = f'{url}/metrics/job/{job}'
    if instance:
        endpoint += f'/instance/{instance}'

    # Build Prometheus text format
    lines = []
    for name, value in metrics.items():
        lines.append(f'{name} {value}')
    payload = '\n'.join(lines) + '\n'

    response = requests.post(endpoint, data=payload)
    if response.status_code in (200, 202):
        logger.info(f"Pushed {len(metrics)} metrics for job={job}")
        return {'status': 'ok', 'metrics_pushed': len(metrics)}
    return {'status': 'error', 'code': response.status_code}


def push_to_cloudwatch(
    namespace: str,
    metric_name: str,
    value: float,
    dimensions: Dict[str, str] = None,
    unit: str = 'None'
) -> Dict[str, Any]:
    """Push a metric to AWS CloudWatch."""
    import boto3
    client = boto3.client('cloudwatch')

    metric_data = {
        'MetricName': metric_name,
        'Value': value,
        'Unit': unit,
    }
    if dimensions:
        metric_data['Dimensions'] = [
            {'Name': k, 'Value': v} for k, v in dimensions.items()
        ]

    client.put_metric_data(Namespace=namespace, MetricData=[metric_data])
    logger.info(f"Pushed {metric_name}={value} to CloudWatch")
    return {'status': 'ok', 'metric': metric_name}


if __name__ == "__main__":
    print("Metric Publisher — Usage Examples")
    print("""
    # Push to Pushgateway
    push_to_pushgateway('batch_job', {
        'records_processed': 1500,
        'job_duration_seconds': 45.2,
    })
    """)
