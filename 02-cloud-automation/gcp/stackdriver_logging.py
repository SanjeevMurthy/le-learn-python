"""
stackdriver_logging.py

GCP Cloud Logging (formerly Stackdriver) operations.

Interview Topics:
- Structured vs unstructured logging in GCP
- Log-based metrics and alerting
- Cloud Logging vs CloudWatch Logs comparison

Production Use Cases:
- Querying logs with advanced filters
- Creating log-based metrics for alerting
- Exporting logs to BigQuery for analysis
- Setting up log sinks

Prerequisites:
- google-cloud-logging (pip install google-cloud-logging)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_logging_client():
    from google.cloud import logging as cloud_logging
    return cloud_logging.Client()


def query_logs(
    project: str,
    log_filter: str,
    hours: int = 1,
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Query Cloud Logging with a filter expression.

    Interview Question:
        Q: How does GCP Cloud Logging differ from AWS CloudWatch Logs?
        A: GCP: advanced query language, automatic ingestion from GKE/GCE,
           integrated with Error Reporting, log-based metrics, BigQuery export.
           AWS: simpler query (Insights), need CloudWatch agent for custom logs,
           log groups/streams organization.
           GCP advantage: better query syntax, automatic K8s integration.
           AWS advantage: tighter integration with Lambda/other AWS services.
    """
    client = get_logging_client()

    # Build time-bounded filter
    start_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    full_filter = f'{log_filter} AND timestamp >= "{start_time}"'

    entries = []
    for entry in client.list_entries(
        filter_=full_filter,
        page_size=max_results,
        max_results=max_results
    ):
        entries.append({
            'timestamp': str(entry.timestamp),
            'severity': entry.severity,
            'log_name': entry.log_name,
            'payload': str(entry.payload),
            'resource': {
                'type': entry.resource.type,
                'labels': dict(entry.resource.labels),
            },
        })

    logger.info(f"Query returned {len(entries)} log entries")
    return entries


def write_structured_log(
    log_name: str,
    message: str,
    severity: str = 'INFO',
    labels: Optional[Dict[str, str]] = None
) -> bool:
    """
    Write a structured log entry to Cloud Logging.

    Interview Question:
        Q: What are the benefits of structured logging in GCP?
        A: 1. Searchable fields (not just text matching)
           2. Can create log-based metrics on specific fields
           3. Better integration with Error Reporting
           4. JSON payloads are automatically parsed
           5. Can include trace IDs for distributed tracing
    """
    client = get_logging_client()
    gcp_logger = client.logger(log_name)

    struct = {
        'message': message,
        'severity': severity,
    }
    if labels:
        struct['labels'] = labels

    try:
        gcp_logger.log_struct(struct, severity=severity)
        logger.info(f"Wrote structured log to {log_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to write log: {e}")
        return False


def list_log_sinks(project: str) -> List[Dict[str, Any]]:
    """List all log sinks (exports) configured in the project."""
    client = get_logging_client()
    sinks = []

    for sink in client.list_sinks():
        sinks.append({
            'name': sink.name,
            'destination': sink.destination,
            'filter': sink.filter_,
        })

    logger.info(f"Found {len(sinks)} log sinks")
    return sinks


if __name__ == "__main__":
    print("=" * 60)
    print("GCP Cloud Logging — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires GCP credentials.

    # Query error logs from the last hour
    errors = query_logs(
        'my-project',
        'severity >= ERROR',
        hours=1
    )
    for e in errors:
        print(f"  [{e['severity']}] {e['payload']}")

    # Write structured log
    write_structured_log(
        'my-app-logs', 'Deployment completed',
        severity='INFO', labels={'version': '2.0.1'}
    )

    # List log sinks
    for sink in list_log_sinks('my-project'):
        print(f"  {sink['name']} → {sink['destination']}")
    """)
