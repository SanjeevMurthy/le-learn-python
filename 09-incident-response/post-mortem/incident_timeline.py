"""
incident_timeline.py

Build incident timelines from logs and events.

Prerequisites:
- Standard library
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_timeline_entry(
    timestamp: str,
    event: str,
    source: str,
    severity: str = 'info',
    details: str = ''
) -> Dict[str, Any]:
    """Create a timeline entry."""
    return {
        'timestamp': timestamp,
        'event': event,
        'source': source,
        'severity': severity,
        'details': details,
    }


def build_timeline(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort and deduplicate timeline entries.

    Interview Question:
        Q: What makes a good post-mortem?
        A: Blameless culture: focus on systems, not people.
           Components: timeline, root cause, impact, detection,
           response, resolution, lessons learned, action items.
           Timeline: detailed sequence of events with timestamps.
           Action items: specific, assigned, deadlines.
           Format: write-up distributed to the team and stakeholders.
           SRE practice: publish and review in weekly meetings.
    """
    sorted_entries = sorted(entries, key=lambda e: e.get('timestamp', ''))

    # Deduplicate by timestamp + event
    seen = set()
    deduped = []
    for entry in sorted_entries:
        key = (entry['timestamp'], entry['event'])
        if key not in seen:
            seen.add(key)
            deduped.append(entry)

    return deduped


def format_timeline(entries: List[Dict[str, Any]]) -> str:
    """Format timeline for display."""
    lines = ["# Incident Timeline\n"]
    for e in entries:
        icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(e['severity'], '⚪')
        lines.append(f"{icon} **{e['timestamp']}** [{e['source']}]")
        lines.append(f"   {e['event']}")
        if e['details']:
            lines.append(f"   _{e['details']}_")
        lines.append('')
    return '\n'.join(lines)


if __name__ == "__main__":
    entries = [
        create_timeline_entry('2024-01-15T14:30:00Z', 'Alert: Error rate > 5%', 'PagerDuty', 'critical'),
        create_timeline_entry('2024-01-15T14:25:00Z', 'Deployment v2.3.1 started', 'ArgoCD', 'info'),
        create_timeline_entry('2024-01-15T14:35:00Z', 'Rollback initiated', 'On-call SRE', 'warning'),
        create_timeline_entry('2024-01-15T14:40:00Z', 'Service recovered', 'Monitoring', 'info'),
    ]
    timeline = build_timeline(entries)
    print(format_timeline(timeline))
