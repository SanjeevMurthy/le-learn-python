"""
report_generator.py

Post-mortem report generation.

Prerequisites:
- Standard library
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_report(
    title: str,
    severity: str,
    start_time: str,
    end_time: str,
    summary: str,
    timeline: List[Dict[str, Any]],
    root_cause: str,
    impact: str,
    detection: str,
    resolution: str,
    action_items: List[Dict[str, str]],
    lessons_learned: List[str],
) -> str:
    """
    Generate a post-mortem report in Markdown.

    Interview Question:
        Q: How do you run a blameless post-mortem?
        A: 1. Schedule within 48h of resolution
           2. Assign a facilitator (not the responder)
           3. Build timeline collaboratively
           4. Ask "what" and "how", never "who"
           5. Identify systemic issues, not individual mistakes
           6. Create specific, actionable items with owners/deadlines
           7. Publish report to the team/org
           8. Track action items to completion
           Culture: treat incidents as learning opportunities.
    """
    report = f"""# Post-Mortem Report: {title}

**Severity**: {severity}
**Duration**: {start_time} — {end_time}
**Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## Summary
{summary}

## Impact
{impact}

## Detection
{detection}

## Timeline
"""

    for entry in timeline:
        icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(entry.get('severity', ''), '⚪')
        report += f"- {icon} **{entry['timestamp']}**: {entry['event']}\n"

    report += f"""
## Root Cause
{root_cause}

## Resolution
{resolution}

## Action Items
| # | Action | Owner | Deadline | Priority |
|---|--------|-------|----------|----------|
"""

    for i, item in enumerate(action_items, 1):
        report += f"| {i} | {item.get('action', '')} | {item.get('owner', '')} | {item.get('deadline', '')} | {item.get('priority', '')} |\n"

    report += "\n## Lessons Learned\n"
    for lesson in lessons_learned:
        report += f"- {lesson}\n"

    return report


if __name__ == "__main__":
    report = generate_report(
        title="API Gateway Outage",
        severity="SEV-1",
        start_time="2024-01-15 14:25 UTC",
        end_time="2024-01-15 14:45 UTC",
        summary="API Gateway returned 503 for 20 minutes after v2.3.1 deployment.",
        timeline=[
            {'timestamp': '14:25', 'event': 'Deployment v2.3.1 started', 'severity': 'info'},
            {'timestamp': '14:30', 'event': 'Error rate exceeded 5%', 'severity': 'critical'},
            {'timestamp': '14:35', 'event': 'Rollback initiated', 'severity': 'warning'},
            {'timestamp': '14:45', 'event': 'Service recovered', 'severity': 'info'},
        ],
        root_cause="New dependency had incompatible API version.",
        impact="~2000 failed requests, 15% of users affected.",
        detection="PagerDuty alert triggered by error rate threshold.",
        resolution="Rolled back to v2.3.0.",
        action_items=[
            {'action': 'Add integration tests for dependency', 'owner': 'Backend', 'deadline': '2024-01-22', 'priority': 'P1'},
            {'action': 'Implement canary deployments', 'owner': 'Platform', 'deadline': '2024-02-01', 'priority': 'P2'},
        ],
        lessons_learned=[
            "Dependency updates need integration tests before merge.",
            "Canary deployment would have caught this before full rollout.",
        ],
    )
    print(report)
