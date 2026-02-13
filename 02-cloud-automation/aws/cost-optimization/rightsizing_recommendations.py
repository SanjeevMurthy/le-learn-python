"""
rightsizing_recommendations.py

EC2 instance rightsizing analysis using CloudWatch metrics.

Interview Topics:
- How to identify over-provisioned vs under-provisioned instances
- Cost vs performance optimization trade-offs
- Automation of rightsizing recommendations

Production Use Cases:
- Monthly rightsizing reviews for cost optimization
- Automated recommendations piped to Slack/Jira
- Pre-migration instance sizing analysis

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials with EC2 + CloudWatch read access
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


# Instance type pricing (approximate on-demand hourly, us-east-1)
INSTANCE_PRICING = {
    't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
    't3.large': 0.0832, 't3.xlarge': 0.1664,
    'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
    'c5.large': 0.085, 'c5.xlarge': 0.170, 'c5.2xlarge': 0.340,
    'r5.large': 0.126, 'r5.xlarge': 0.252, 'r5.2xlarge': 0.504,
}

# Downsize map: current type → recommended smaller type
DOWNSIZE_MAP = {
    't3.large': 't3.medium', 't3.xlarge': 't3.large',
    'm5.xlarge': 'm5.large', 'm5.2xlarge': 'm5.xlarge',
    'c5.xlarge': 'c5.large', 'c5.2xlarge': 'c5.xlarge',
    'r5.xlarge': 'r5.large', 'r5.2xlarge': 'r5.xlarge',
}


def get_instance_utilization(
    instance_id: str,
    days: int = 14,
    region: str = None
) -> Dict[str, Any]:
    """
    Get CPU and network utilization metrics for an instance.

    Args:
        instance_id: EC2 instance ID
        days: Number of days to analyze
        region: AWS region

    Returns:
        Utilization statistics

    Interview Question:
        Q: What metrics do you look at for rightsizing?
        A: 1. CPU: average < 20% → likely oversized
           2. Memory: requires CloudWatch agent (not default)
           3. Network I/O: low throughput → smaller instance works
           4. Disk I/O: check IOPS for storage-optimized types
           5. Look at peak usage, not just average — ensure headroom
           6. Consider burst patterns (t3 instances with CPU credits)
    """
    import boto3

    cw = boto3.client(
        'cloudwatch',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)

    # Get CPU utilization
    cpu_response = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average', 'Maximum']
    )

    cpu_datapoints = cpu_response['Datapoints']
    cpu_avg = round(
        sum(dp['Average'] for dp in cpu_datapoints) / len(cpu_datapoints), 2
    ) if cpu_datapoints else 0
    cpu_max = round(
        max(dp['Maximum'] for dp in cpu_datapoints), 2
    ) if cpu_datapoints else 0

    # Get network I/O
    net_response = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='NetworkIn',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=86400,  # Daily
        Statistics=['Sum']
    )

    net_datapoints = net_response['Datapoints']
    daily_net_gb = round(
        sum(dp['Sum'] for dp in net_datapoints) / len(net_datapoints) / (1024**3), 2
    ) if net_datapoints else 0

    return {
        'instance_id': instance_id,
        'analysis_days': days,
        'cpu_avg_percent': cpu_avg,
        'cpu_max_percent': cpu_max,
        'daily_network_in_gb': daily_net_gb,
        'datapoints_count': len(cpu_datapoints),
    }


def analyze_rightsizing(
    instance_id: str,
    instance_type: str,
    utilization: Dict[str, Any],
    cpu_threshold_low: float = 20.0,
    cpu_threshold_high: float = 80.0
) -> Dict[str, Any]:
    """
    Analyze an instance and generate a rightsizing recommendation.

    Args:
        instance_id: EC2 instance ID
        instance_type: Current instance type
        utilization: Metrics from get_instance_utilization
        cpu_threshold_low: CPU % below which to recommend downsize
        cpu_threshold_high: CPU % above which to recommend upsize

    Returns:
        Rightsizing recommendation

    Interview Question:
        Q: How would you implement automated rightsizing?
        A: 1. Collect 2+ weeks of CloudWatch metrics (CPU, memory, network)
           2. Analyze patterns — average, peak, burst frequency
           3. Generate recommendations with cost savings estimate
           4. Flag exceptions (batch jobs with periodic high usage)
           5. Require approval before resizing (human-in-the-loop)
           6. Apply changes during maintenance windows
           7. Monitor after resize to validate performance
    """
    cpu_avg = utilization['cpu_avg_percent']
    cpu_max = utilization['cpu_max_percent']

    current_cost = INSTANCE_PRICING.get(instance_type, 0) * 730  # Monthly hours
    recommendation = 'right-sized'
    recommended_type = instance_type
    savings = 0.0

    if cpu_avg < cpu_threshold_low and cpu_max < 60:
        # Under-utilized → recommend downsize
        if instance_type in DOWNSIZE_MAP:
            recommended_type = DOWNSIZE_MAP[instance_type]
            new_cost = INSTANCE_PRICING.get(recommended_type, 0) * 730
            savings = current_cost - new_cost
            recommendation = 'downsize'
        else:
            recommendation = 'review'  # Can't auto-downsize

    elif cpu_avg > cpu_threshold_high or cpu_max > 95:
        # Over-utilized → recommend upsize
        recommendation = 'upsize'

    return {
        'instance_id': instance_id,
        'current_type': instance_type,
        'recommendation': recommendation,
        'recommended_type': recommended_type,
        'cpu_avg': cpu_avg,
        'cpu_max': cpu_max,
        'current_monthly_cost': round(current_cost, 2),
        'estimated_monthly_savings': round(savings, 2),
        'estimated_annual_savings': round(savings * 12, 2),
        'confidence': 'high' if utilization['datapoints_count'] > 100 else 'medium',
    }


def generate_rightsizing_report(
    region: str = None,
    tag_key: str = 'Environment',
    tag_value: str = 'production'
) -> Dict[str, Any]:
    """
    Generate a rightsizing report for tagged instances.

    Args:
        region: AWS region
        tag_key: Filter instances by tag key
        tag_value: Filter instances by tag value

    Returns:
        Full report with recommendations and savings
    """
    import boto3

    ec2 = boto3.client(
        'ec2',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )

    # Get running instances
    response = ec2.describe_instances(
        Filters=[
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': 'instance-state-name', 'Values': ['running']},
        ]
    )

    recommendations = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']

            utilization = get_instance_utilization(instance_id, days=14, region=region)
            rec = analyze_rightsizing(instance_id, instance_type, utilization)
            recommendations.append(rec)

    # Summary
    downsize_count = sum(1 for r in recommendations if r['recommendation'] == 'downsize')
    total_savings = sum(r['estimated_monthly_savings'] for r in recommendations)

    return {
        'generated_at': datetime.now(timezone.utc).isoformat() + 'Z',
        'total_instances': len(recommendations),
        'downsize_candidates': downsize_count,
        'total_monthly_savings': round(total_savings, 2),
        'total_annual_savings': round(total_savings * 12, 2),
        'recommendations': recommendations,
    }


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Rightsizing Recommendations — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires valid AWS credentials with EC2 + CloudWatch access.

    Example usage:

    # Generate report for production instances
    report = generate_rightsizing_report(tag_key='Environment', tag_value='production')
    print(f"  Analyzed: {report['total_instances']} instances")
    print(f"  Downsize candidates: {report['downsize_candidates']}")
    print(f"  Estimated savings: ${report['total_monthly_savings']}/month")

    # Individual instance analysis
    util = get_instance_utilization('i-1234567890abcdef0', days=14)
    rec = analyze_rightsizing('i-1234567890abcdef0', 'm5.xlarge', util)
    print(f"  Recommendation: {rec['recommendation']}")
    print(f"  Savings: ${rec['estimated_monthly_savings']}/month")
    """)
