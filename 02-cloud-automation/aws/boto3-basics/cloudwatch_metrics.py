"""
cloudwatch_metrics.py

AWS CloudWatch metrics, alarms, and dashboards using boto3.

Interview Topics:
- CloudWatch metrics vs logs vs alarms
- Custom metrics for application monitoring
- Alarm actions and notification design

Production Use Cases:
- Publishing custom application metrics
- Setting up alarms for SLA monitoring
- Creating operational dashboards
- Automated incident detection

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials configured
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_cloudwatch_client(region: str = None):
    """Create a boto3 CloudWatch client."""
    import boto3
    return boto3.client(
        'cloudwatch',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def publish_custom_metric(
    namespace: str,
    metric_name: str,
    value: float,
    unit: str = 'None',
    dimensions: Optional[Dict[str, str]] = None,
    region: str = None
) -> bool:
    """
    Publish a custom metric to CloudWatch.

    Custom metrics let you track application-specific data
    like request latency, queue depth, or business KPIs.

    Args:
        namespace: CloudWatch namespace (e.g., 'MyApp/Production')
        metric_name: Metric name (e.g., 'RequestLatency')
        value: Metric value
        unit: Unit type (Seconds, Bytes, Count, Percent, etc.)
        dimensions: Key-value pairs for metric dimensions
        region: AWS region

    Returns:
        True if published successfully

    Interview Question:
        Q: What are CloudWatch dimensions and when do you use them?
        A: Dimensions are name-value pairs that identify a metric.
           Example: metric 'CPUUtilization' with dimensions
           InstanceId=i-123 and InstanceType=m5.large.
           They let you filter and aggregate metrics.
           Design tip: choose dimensions that map to your monitoring needs
           (per-service, per-region, per-environment).
    """
    cw = get_cloudwatch_client(region)

    metric_data = {
        'MetricName': metric_name,
        'Value': value,
        'Unit': unit,
        'Timestamp': datetime.now(timezone.utc),
    }

    if dimensions:
        metric_data['Dimensions'] = [
            {'Name': k, 'Value': v}
            for k, v in dimensions.items()
        ]

    try:
        cw.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )
        logger.info(
            f"Published metric: {namespace}/{metric_name} = {value} {unit}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to publish metric: {e}")
        return False


def publish_batch_metrics(
    namespace: str,
    metrics: List[Dict[str, Any]],
    region: str = None
) -> bool:
    """
    Publish multiple metrics in a single API call.

    CloudWatch allows up to 1000 metric values per PutMetricData call.
    Batching reduces API calls and costs.

    Args:
        namespace: CloudWatch namespace
        metrics: List of metric dicts with keys: name, value, unit, dimensions
        region: AWS region

    Returns:
        True if published successfully
    """
    cw = get_cloudwatch_client(region)
    timestamp = datetime.now(timezone.utc)

    metric_data = []
    for m in metrics:
        data = {
            'MetricName': m['name'],
            'Value': m['value'],
            'Unit': m.get('unit', 'None'),
            'Timestamp': timestamp,
        }
        if 'dimensions' in m:
            data['Dimensions'] = [
                {'Name': k, 'Value': v}
                for k, v in m['dimensions'].items()
            ]
        metric_data.append(data)

    # CloudWatch limit: 1000 metrics per batch
    batch_size = 1000
    for i in range(0, len(metric_data), batch_size):
        batch = metric_data[i:i + batch_size]
        try:
            cw.put_metric_data(Namespace=namespace, MetricData=batch)
            logger.info(f"Published batch of {len(batch)} metrics to {namespace}")
        except Exception as e:
            logger.error(f"Failed to publish metric batch: {e}")
            return False

    return True


def create_alarm(
    alarm_name: str,
    namespace: str,
    metric_name: str,
    threshold: float,
    comparison: str = 'GreaterThanThreshold',
    period: int = 300,
    evaluation_periods: int = 2,
    statistic: str = 'Average',
    dimensions: Optional[Dict[str, str]] = None,
    sns_topic_arn: Optional[str] = None,
    region: str = None
) -> bool:
    """
    Create a CloudWatch alarm.

    Alarms watch a metric and trigger actions when the metric
    crosses a threshold for a sustained period.

    Args:
        alarm_name: Name for the alarm
        namespace: Metric namespace
        metric_name: Metric to watch
        threshold: Threshold value
        comparison: GreaterThanThreshold, LessThanThreshold, etc.
        period: Evaluation period in seconds
        evaluation_periods: Number of periods the threshold must be breached
        statistic: Average, Sum, Maximum, Minimum, SampleCount
        dimensions: Metric dimensions
        sns_topic_arn: SNS topic ARN for notifications
        region: AWS region

    Returns:
        True if alarm was created

    Interview Question:
        Q: How do you design alerting to avoid alert fatigue?
        A: 1. Set meaningful thresholds based on SLOs, not arbitrary values
           2. Use evaluation_periods > 1 to avoid transient spikes
           3. Tier alerts: P1 (page) vs P2 (Slack) vs P3 (email)
           4. Include runbook links in alarm descriptions
           5. Regularly review and tune thresholds
           6. Use composite alarms to reduce noise
    """
    cw = get_cloudwatch_client(region)

    alarm_config = {
        'AlarmName': alarm_name,
        'Namespace': namespace,
        'MetricName': metric_name,
        'Threshold': threshold,
        'ComparisonOperator': comparison,
        'Period': period,
        'EvaluationPeriods': evaluation_periods,
        'Statistic': statistic,
        'AlarmDescription': f'Alert when {metric_name} {comparison} {threshold}',
        'TreatMissingData': 'missing',
        'Tags': [
            {'Key': 'ManagedBy', 'Value': 'devops-toolkit'},
        ]
    }

    if dimensions:
        alarm_config['Dimensions'] = [
            {'Name': k, 'Value': v}
            for k, v in dimensions.items()
        ]

    if sns_topic_arn:
        alarm_config['AlarmActions'] = [sns_topic_arn]
        alarm_config['OKActions'] = [sns_topic_arn]

    try:
        cw.put_metric_alarm(**alarm_config)
        logger.info(f"Created alarm: {alarm_name} ({metric_name} {comparison} {threshold})")
        return True

    except Exception as e:
        logger.error(f"Failed to create alarm: {e}")
        return False


def get_metric_data(
    namespace: str,
    metric_name: str,
    dimensions: Optional[Dict[str, str]] = None,
    period_hours: int = 24,
    statistic: str = 'Average',
    period_seconds: int = 3600,
    region: str = None
) -> Dict[str, Any]:
    """
    Query CloudWatch metric data.

    Args:
        namespace: Metric namespace
        metric_name: Metric name
        dimensions: Metric dimensions
        period_hours: How far back to query
        statistic: Statistic type
        period_seconds: Data point resolution
        region: AWS region

    Returns:
        Metric data with timestamps and values
    """
    cw = get_cloudwatch_client(region)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=period_hours)

    kwargs = {
        'Namespace': namespace,
        'MetricName': metric_name,
        'StartTime': start_time,
        'EndTime': end_time,
        'Period': period_seconds,
        'Statistics': [statistic],
    }

    if dimensions:
        kwargs['Dimensions'] = [
            {'Name': k, 'Value': v}
            for k, v in dimensions.items()
        ]

    response = cw.get_metric_statistics(**kwargs)

    datapoints = sorted(
        response['Datapoints'],
        key=lambda x: x['Timestamp']
    )

    return {
        'namespace': namespace,
        'metric': metric_name,
        'statistic': statistic,
        'period_hours': period_hours,
        'datapoints': [
            {
                'timestamp': dp['Timestamp'].isoformat(),
                'value': round(dp[statistic], 4),
            }
            for dp in datapoints
        ]
    }


def list_alarms(
    state: Optional[str] = None,
    region: str = None
) -> List[Dict[str, Any]]:
    """
    List CloudWatch alarms, optionally filtered by state.

    Args:
        state: Filter by state (OK, ALARM, INSUFFICIENT_DATA)
        region: AWS region

    Returns:
        List of alarm details
    """
    cw = get_cloudwatch_client(region)

    kwargs = {}
    if state:
        kwargs['StateValue'] = state

    paginator = cw.get_paginator('describe_alarms')
    alarms = []

    for page in paginator.paginate(**kwargs):
        for alarm in page['MetricAlarms']:
            alarms.append({
                'name': alarm['AlarmName'],
                'state': alarm['StateValue'],
                'metric': alarm.get('MetricName', 'N/A'),
                'namespace': alarm.get('Namespace', 'N/A'),
                'threshold': alarm.get('Threshold', 'N/A'),
                'description': alarm.get('AlarmDescription', ''),
            })

    logger.info(f"Found {len(alarms)} alarms" + (f" in state {state}" if state else ""))
    return alarms


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CloudWatch Metrics — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: These examples require valid AWS credentials.

    Example usage (uncomment to run):

    # Publish custom metric
    publish_custom_metric(
        namespace='MyApp/Production',
        metric_name='RequestLatency',
        value=125.5,
        unit='Milliseconds',
        dimensions={'Service': 'api-gateway', 'Environment': 'prod'}
    )

    # Create alarm
    create_alarm(
        alarm_name='HighCPU-WebServer',
        namespace='AWS/EC2',
        metric_name='CPUUtilization',
        threshold=80.0,
        dimensions={'InstanceId': 'i-1234567890abcdef0'},
        sns_topic_arn='arn:aws:sns:us-east-1:123456789012:alerts'
    )

    # List alarms in ALARM state
    alarms = list_alarms(state='ALARM')
    for a in alarms:
        print(f"  🚨 {a['name']}: {a['metric']} > {a['threshold']}")
    """)
