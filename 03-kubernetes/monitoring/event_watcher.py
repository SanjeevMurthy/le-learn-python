"""
event_watcher.py

Watch Kubernetes events in real-time for monitoring and alerting.

Interview Topics:
- K8s watch API and streaming
- Event types: Normal, Warning
- Event-driven automation

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import logging
from typing import Optional, Callable
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_kube_config():
    from kubernetes import config
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def watch_events(
    namespace: Optional[str] = None,
    event_type: Optional[str] = None,
    timeout: int = 60,
    callback: Optional[Callable] = None
) -> list:
    """
    Watch K8s events in real-time using the Watch API.

    Interview Question:
        Q: How does the K8s Watch API work?
        A: Watch uses HTTP long-polling (chunked transfer encoding).
           Client sends GET with ?watch=true, server keeps connection
           open and streams events (ADDED, MODIFIED, DELETED).
           Each event includes resourceVersion for consistency.
           Use resourceVersion to resume watches after disconnect.
           Watches can timeout — handle reconnection in production.
    """
    from kubernetes import client, watch
    load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    events = []

    try:
        if namespace:
            stream = w.stream(
                v1.list_namespaced_event, namespace, timeout_seconds=timeout
            )
        else:
            stream = w.stream(
                v1.list_event_for_all_namespaces, timeout_seconds=timeout
            )

        for event_obj in stream:
            event = event_obj['object']
            action = event_obj['type']

            # Filter by event type if specified
            if event_type and event.type != event_type:
                continue

            event_data = {
                'action': action,
                'type': event.type,
                'reason': event.reason,
                'message': event.message,
                'namespace': event.metadata.namespace,
                'involved_object': (
                    f"{event.involved_object.kind}/{event.involved_object.name}"
                    if event.involved_object else 'N/A'
                ),
                'timestamp': str(event.last_timestamp or event.metadata.creation_timestamp),
            }

            events.append(event_data)

            if callback:
                callback(event_data)
            else:
                level = 'WARNING' if event.type == 'Warning' else 'INFO'
                logger.log(
                    logging.WARNING if level == 'WARNING' else logging.INFO,
                    f"[{event.type}] {event.reason}: {event.message}"
                )

    except Exception as e:
        logger.error(f"Watch error: {e}")

    return events


def get_recent_warnings(namespace: str = '', limit: int = 50) -> list:
    """Get recent Warning events."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    if namespace:
        events = v1.list_namespaced_event(
            namespace, field_selector='type=Warning'
        )
    else:
        events = v1.list_event_for_all_namespaces(
            field_selector='type=Warning'
        )

    warnings = []
    for event in events.items[-limit:]:
        warnings.append({
            'reason': event.reason,
            'message': event.message,
            'namespace': event.metadata.namespace,
            'count': event.count,
            'object': f"{event.involved_object.kind}/{event.involved_object.name}",
            'last_seen': str(event.last_timestamp),
        })

    return warnings


if __name__ == "__main__":
    print("=" * 60)
    print("Event Watcher — Usage Examples")
    print("=" * 60)
    print("""
    # Watch all warning events for 30 seconds
    events = watch_events(event_type='Warning', timeout=30)

    # Get recent warnings
    warnings = get_recent_warnings(limit=20)
    for w in warnings:
        print(f"  [{w['reason']}] {w['object']}: {w['message']}")
    """)
