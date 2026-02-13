"""
azure_monitor.py

Azure Monitor metrics and alerts management.

Interview Topics:
- Azure Monitor vs CloudWatch vs Cloud Monitoring
- Log Analytics workspaces
- Application Insights integration

Production Use Cases:
- Querying Azure resource metrics
- Setting up metric alerts
- Log Analytics queries

Prerequisites:
- azure-monitor-query, azure-identity
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


def get_metrics_client():
    from azure.identity import DefaultAzureCredential
    from azure.monitor.query import MetricsQueryClient
    credential = DefaultAzureCredential()
    return MetricsQueryClient(credential)


def get_logs_client():
    from azure.identity import DefaultAzureCredential
    from azure.monitor.query import LogsQueryClient
    credential = DefaultAzureCredential()
    return LogsQueryClient(credential)


def query_metrics(
    resource_uri: str,
    metric_names: List[str],
    timespan_hours: int = 24,
    granularity_minutes: int = 60
) -> Dict[str, Any]:
    """
    Query Azure Monitor metrics for a resource.

    Interview Question:
        Q: How does Azure Monitor compare to CloudWatch?
        A: Azure Monitor: centralized for all Azure resources,
           Log Analytics with KQL (Kusto Query Language),
           Application Insights for APM, Workbooks for visualization.
           CloudWatch: per-service metrics, CloudWatch Logs with
           Insights query, X-Ray for tracing, dashboards.
           Azure advantage: KQL is more powerful than CW Insights.
           AWS advantage: tighter integration with each service.
    """
    client = get_metrics_client()

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=timespan_hours)
    timespan = (start_time, end_time)

    try:
        response = client.query_resource(
            resource_uri,
            metric_names=metric_names,
            timespan=timespan,
            granularity=timedelta(minutes=granularity_minutes),
        )

        results = {}
        for metric in response.metrics:
            datapoints = []
            for ts in metric.timeseries:
                for data in ts.data:
                    datapoints.append({
                        'timestamp': data.timestamp.isoformat(),
                        'average': data.average,
                        'maximum': data.maximum,
                        'minimum': data.minimum,
                    })
            results[metric.name] = {
                'unit': metric.unit,
                'datapoints': datapoints,
            }

        return {'resource': resource_uri, 'metrics': results}

    except Exception as e:
        logger.error(f"Metrics query failed: {e}")
        return {'status': 'error', 'error': str(e)}


def query_logs(
    workspace_id: str,
    query: str,
    timespan_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Query Log Analytics workspace using KQL.

    Interview Question:
        Q: What is KQL and why is it useful?
        A: Kusto Query Language — Azure's log query language.
           More expressive than CloudWatch Insights:
           - Supports joins across tables
           - Built-in time-series analysis
           - Aggregation and visualization functions
           - Can query across multiple workspaces
           Example: ContainerLog | where LogEntry contains "error"
           | summarize count() by bin(TimeGenerated, 1h)
    """
    client = get_logs_client()

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=timespan_hours)

    try:
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=(start_time, end_time),
        )

        rows = []
        if response.tables:
            table = response.tables[0]
            columns = [col.name for col in table.columns]
            for row in table.rows:
                rows.append(dict(zip(columns, row)))

        logger.info(f"Log query returned {len(rows)} rows")
        return rows

    except Exception as e:
        logger.error(f"Log query failed: {e}")
        return []


if __name__ == "__main__":
    print("=" * 60)
    print("Azure Monitor — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires Azure credentials.

    # Query VM CPU metrics
    metrics = query_metrics(
        '/subscriptions/.../resourceGroups/.../providers/Microsoft.Compute/virtualMachines/my-vm',
        metric_names=['Percentage CPU'],
        timespan_hours=24
    )

    # Query Log Analytics
    rows = query_logs(
        workspace_id='workspace-id-here',
        query='ContainerLog | where LogEntry contains "error" | take 10'
    )
    for row in rows:
        print(f"  {row}")
    """)
