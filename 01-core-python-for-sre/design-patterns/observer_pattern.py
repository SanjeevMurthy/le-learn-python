"""
observer_pattern.py

Observer pattern for event-driven monitoring and alerting.

Interview Topics:
- Event-driven architecture
- Pub/sub vs observer pattern
- Decoupling producers from consumers

Production Use Cases:
- Monitoring system alerts (metric threshold → notify multiple channels)
- Deployment event notifications
- Infrastructure change audit trail
- Health check result propagation

Prerequisites:
- No external packages needed (stdlib only)
"""

import logging
import time
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventBus:
    """
    Simple event bus implementing the observer pattern.

    Publishers emit events without knowing who listens.
    Subscribers register interest in specific event types.

    Interview Question:
        Q: What is the Observer pattern and where is it used in DevOps?
        A: Observer decouples event producers from consumers.
           Producers emit events; observers react independently.
           DevOps uses: monitoring alerts (metric → Slack, PagerDuty),
           CI/CD events (build done → deploy, notify, update dashboard),
           infrastructure changes (resource created → audit, tag, monitor).
    """

    def __init__(self):
        # Map event_type → list of subscriber callbacks
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Register a callback for a specific event type.

        Args:
            event_type: Event type string (e.g., 'alert.critical')
            callback: Function to call when event fires.
                     Receives event_data dict as argument.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        logger.info(
            f"Subscribed '{callback.__name__}' to '{event_type}' "
            f"(total: {len(self._subscribers[event_type])} subscribers)"
        )

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Remove a subscriber from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> int:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            data: Event payload

        Returns:
            Number of subscribers notified
        """
        event = {
            'type': event_type,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        self._event_history.append(event)

        subscribers = self._subscribers.get(event_type, [])
        # Also notify wildcard subscribers
        wildcard_subs = self._subscribers.get('*', [])
        all_subscribers = subscribers + wildcard_subs

        if not all_subscribers:
            logger.debug(f"No subscribers for event '{event_type}'")
            return 0

        notified = 0
        for callback in all_subscribers:
            try:
                callback(event)
                notified += 1
            except Exception as e:
                # Don't let one subscriber failure affect others
                logger.error(
                    f"Subscriber '{callback.__name__}' failed for "
                    f"'{event_type}': {e}"
                )

        return notified

    def get_history(self, event_type: Optional[str] = None) -> List[Dict]:
        """Get event history, optionally filtered by type."""
        if event_type:
            return [e for e in self._event_history if e['type'] == event_type]
        return self._event_history.copy()


def create_monitoring_event_bus() -> EventBus:
    """
    Create an event bus pre-configured with common monitoring handlers.

    Returns:
        EventBus with Slack, PagerDuty, and audit subscribers
    """
    bus = EventBus()

    def slack_notifier(event: Dict):
        severity = event['data'].get('severity', 'info')
        message = event['data'].get('message', 'No message')
        print(f"  📨 [Slack] [{severity.upper()}] {message}")

    def pagerduty_handler(event: Dict):
        severity = event['data'].get('severity', 'info')
        if severity in ('critical', 'high'):
            message = event['data'].get('message', 'No message')
            print(f"  🔔 [PagerDuty] Incident created: {message}")

    def audit_logger(event: Dict):
        print(f"  📋 [Audit] Event: {event['type']} at {event['timestamp']}")

    # Subscribe handlers to event types
    bus.subscribe('alert.critical', slack_notifier)
    bus.subscribe('alert.critical', pagerduty_handler)
    bus.subscribe('alert.warning', slack_notifier)
    bus.subscribe('deployment.*', slack_notifier)
    bus.subscribe('*', audit_logger)  # Audit everything

    return bus


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Observer Pattern — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Basic event bus ----
    print("\n--- Example 1: Basic Event Bus ---")
    bus = EventBus()

    # Define subscribers
    def on_build_complete(event):
        print(f"  → Build handler: {event['data']}")

    def on_any_event(event):
        print(f"  → Wildcard: event type='{event['type']}'")

    bus.subscribe('build.complete', on_build_complete)
    bus.subscribe('*', on_any_event)

    # Publish events
    bus.publish('build.complete', {'build_id': 42, 'status': 'success'})
    bus.publish('deploy.started', {'environment': 'staging'})

    # ---- Example 2: Monitoring event bus ----
    print("\n--- Example 2: Monitoring Events ---")
    monitor_bus = create_monitoring_event_bus()

    # Simulate critical alert
    monitor_bus.publish('alert.critical', {
        'message': 'API error rate > 5%',
        'severity': 'critical',
        'service': 'api-gateway',
        'metric_value': 7.2
    })

    # Simulate warning
    monitor_bus.publish('alert.warning', {
        'message': 'CPU usage > 80%',
        'severity': 'warning',
        'host': 'web-server-03'
    })

    # Check event history
    print(f"\n  Event history: {len(monitor_bus.get_history())} events recorded")
