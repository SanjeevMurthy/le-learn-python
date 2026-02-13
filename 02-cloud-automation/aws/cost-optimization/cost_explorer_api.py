"""
cost_explorer_api.py

AWS Cost Explorer API for analyzing and forecasting cloud spend.

Interview Topics:
- How to programmatically track AWS costs
- Cost allocation tags and billing dimensions
- Budget alerts and forecasting

Production Use Cases:
- Automated daily/weekly cost reports
- Cost anomaly detection
- Budget tracking per team/project
- Forecasting future spend based on trends

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials with Cost Explorer access (ce:*)
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


def get_ce_client():
    """Create a Cost Explorer client (always us-east-1)."""
    import boto3
    # Cost Explorer API is only available in us-east-1
    return boto3.client('ce', region_name='us-east-1')


def get_monthly_costs(
    months: int = 3,
    granularity: str = 'MONTHLY',
    group_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get AWS costs for the last N months.

    Args:
        months: Number of months to look back
        granularity: DAILY, MONTHLY, or HOURLY
        group_by: Optional grouping ('SERVICE', 'LINKED_ACCOUNT', 'REGION')

    Returns:
        Cost data with breakdowns

    Interview Question:
        Q: How do you implement cost visibility across teams?
        A: 1. Mandate cost allocation tags (Team, Project, Environment)
           2. Enable tag-based cost allocation in AWS Billing
           3. Automate weekly cost reports per team via Cost Explorer API
           4. Set up AWS Budgets with alerts per team/project
           5. Create dashboards (QuickSight or Grafana)
           6. Implement showback/chargeback policies
    """
    ce = get_ce_client()

    end_date = datetime.now(timezone.utc).replace(day=1)
    start_date = end_date - timedelta(days=months * 30)

    kwargs = {
        'TimePeriod': {
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d'),
        },
        'Granularity': granularity,
        'Metrics': ['UnblendedCost', 'UsageQuantity'],
    }

    if group_by:
        kwargs['GroupBy'] = [
            {'Type': 'DIMENSION', 'Key': group_by}
        ]

    response = ce.get_cost_and_usage(**kwargs)

    results = []
    for period in response['ResultsByTime']:
        period_data = {
            'start': period['TimePeriod']['Start'],
            'end': period['TimePeriod']['End'],
        }

        if group_by and 'Groups' in period:
            # Grouped costs
            period_data['groups'] = []
            for group in period['Groups']:
                period_data['groups'].append({
                    'key': group['Keys'][0],
                    'cost': round(float(group['Metrics']['UnblendedCost']['Amount']), 2),
                    'unit': group['Metrics']['UnblendedCost']['Unit'],
                })
        else:
            # Total cost
            period_data['total_cost'] = round(
                float(period['Total']['UnblendedCost']['Amount']), 2
            )

        results.append(period_data)

    total = sum(r.get('total_cost', 0) for r in results)
    logger.info(f"Cost data retrieved: {months} months, total: ${total:.2f}")
    return {'periods': results, 'total': round(total, 2)}


def get_cost_forecast(
    days: int = 30,
    granularity: str = 'MONTHLY'
) -> Dict[str, Any]:
    """
    Get AWS cost forecast for the next N days.

    Args:
        days: Number of days to forecast
        granularity: DAILY or MONTHLY

    Returns:
        Forecast data with expected costs

    Interview Question:
        Q: How would you detect cost anomalies automatically?
        A: 1. Track daily costs and calculate moving average
           2. Alert if daily cost > 2x average (sudden spike)
           3. Use AWS Cost Anomaly Detection service for ML-based detection
           4. Monitor specific expensive services (EC2, RDS, S3)
           5. Set up budget alerts at 50%, 80%, 100% thresholds
           6. Correlate spikes with deployment events
    """
    ce = get_ce_client()

    start_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    end_date = (datetime.now(timezone.utc) + timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        response = ce.get_cost_forecast(
            TimePeriod={
                'Start': start_date,
                'End': end_date,
            },
            Metric='UNBLENDED_COST',
            Granularity=granularity,
        )

        forecasted_total = round(float(response['Total']['Amount']), 2)

        forecast_periods = []
        for period in response.get('ForecastResultsByTime', []):
            forecast_periods.append({
                'start': period['TimePeriod']['Start'],
                'end': period['TimePeriod']['End'],
                'mean_value': round(float(period['MeanValue']), 2),
            })

        return {
            'forecasted_total': forecasted_total,
            'forecast_days': days,
            'periods': forecast_periods,
        }

    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        return {'status': 'error', 'error': str(e)}


def get_top_cost_services(days: int = 30, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Get the top N most expensive AWS services.

    Args:
        days: Number of days to analyze
        top_n: Number of top services to return

    Returns:
        List of services sorted by cost (descending)
    """
    ce = get_ce_client()

    end_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    # Aggregate costs per service
    service_costs: Dict[str, float] = {}
    for period in response['ResultsByTime']:
        for group in period.get('Groups', []):
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            service_costs[service] = service_costs.get(service, 0) + cost

    # Sort by cost, descending
    sorted_services = sorted(
        service_costs.items(), key=lambda x: x[1], reverse=True
    )[:top_n]

    total = sum(cost for _, cost in sorted_services)
    results = []
    for service, cost in sorted_services:
        results.append({
            'service': service,
            'cost': round(cost, 2),
            'percentage': round(cost / total * 100, 1) if total > 0 else 0,
        })

    return results


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Cost Explorer API — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials with Cost Explorer access (ce:*).

    Example usage:

    # Get monthly costs for last 3 months
    costs = get_monthly_costs(months=3)
    print(f"  Total (3 months): ${costs['total']}")
    for period in costs['periods']:
        print(f"    {period['start']}: ${period.get('total_cost', 0)}")

    # Get costs grouped by service
    costs = get_monthly_costs(months=1, group_by='SERVICE')

    # Top 10 most expensive services
    top_services = get_top_cost_services(days=30, top_n=10)
    for svc in top_services:
        print(f"  {svc['service']}: ${svc['cost']} ({svc['percentage']}%)")

    # Monthly cost forecast
    forecast = get_cost_forecast(days=30)
    print(f"  Forecasted spend: ${forecast.get('forecasted_total', 'N/A')}")
    """)
