"""
log_aggregation_client.py

Client for sending logs to centralized aggregation systems.

Interview Topics:
- Centralized vs distributed logging
- Log pipeline architecture
- Log levels and filtering strategies

Production Use Cases:
- Forwarding application logs to ELK/CloudWatch/Stackdriver
- Buffering logs for batch transmission
- Handling network failures gracefully

Prerequisites:
- requests (pip install requests)
"""

import json
import time
import logging
import queue
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_log_entry(
    message: str,
    level: str = "INFO",
    service: str = "default",
    **extra_fields
) -> Dict[str, Any]:
    """
    Create a structured log entry for aggregation.

    Args:
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service: Service name
        **extra_fields: Additional key-value fields

    Returns:
        Structured log entry dictionary
    """
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': level,
        'message': message,
        'service': service,
        'hostname': _get_hostname(),
    }
    entry.update(extra_fields)
    return entry


def _get_hostname() -> str:
    """Get current hostname for log entries."""
    import socket
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


class LogBuffer:
    """
    Thread-safe log buffer that batches log entries for efficient transmission.

    Instead of sending each log entry individually, the buffer collects
    entries and flushes them in batches when the buffer is full or a
    time interval has elapsed.

    Interview Question:
        Q: Why buffer logs instead of sending each one immediately?
        A: 1. Reduces network overhead (fewer HTTP requests)
           2. Better throughput for high-volume logging
           3. Allows the aggregation system to process in batches
           4. Reduces chance of log loss during brief network issues
           Risk: If the process crashes, buffered logs may be lost.
           Mitigation: Keep buffer small and flush on graceful shutdown.
    """

    def __init__(
        self,
        max_size: int = 100,
        flush_interval: float = 5.0,
        on_flush: Optional[callable] = None
    ):
        """
        Args:
            max_size: Maximum entries before automatic flush
            flush_interval: Seconds between timed flushes
            on_flush: Callback function that receives the list of entries
        """
        self._buffer: queue.Queue = queue.Queue()
        self._max_size = max_size
        self._flush_interval = flush_interval
        self._on_flush = on_flush or self._default_flush
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None

    def add(self, entry: Dict[str, Any]) -> None:
        """Add a log entry to the buffer."""
        self._buffer.put(entry)

        # Flush if buffer is full
        if self._buffer.qsize() >= self._max_size:
            self.flush()

    def flush(self) -> List[Dict[str, Any]]:
        """Flush all buffered entries."""
        entries = []
        while not self._buffer.empty():
            try:
                entries.append(self._buffer.get_nowait())
            except queue.Empty:
                break

        if entries:
            logger.info(f"Flushing {len(entries)} log entries")
            self._on_flush(entries)

        return entries

    def start_auto_flush(self) -> None:
        """Start background thread for periodic flushing."""
        self._running = True
        self._flush_thread = threading.Thread(
            target=self._auto_flush_loop,
            daemon=True
        )
        self._flush_thread.start()
        logger.info(f"Auto-flush started (interval: {self._flush_interval}s)")

    def stop(self) -> None:
        """Stop auto-flush and flush remaining entries."""
        self._running = False
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)
        # Final flush to avoid losing entries
        self.flush()
        logger.info("Log buffer stopped")

    def _auto_flush_loop(self) -> None:
        """Background flush loop."""
        while self._running:
            time.sleep(self._flush_interval)
            if not self._buffer.empty():
                self.flush()

    @staticmethod
    def _default_flush(entries: List[Dict[str, Any]]) -> None:
        """Default flush handler — prints to stdout."""
        for entry in entries:
            print(f"  [FLUSH] {json.dumps(entry)}")


def send_logs_to_endpoint(
    entries: List[Dict[str, Any]],
    endpoint_url: str,
    api_key: Optional[str] = None,
    timeout: float = 10.0
) -> bool:
    """
    Send a batch of log entries to an HTTP endpoint.

    Args:
        entries: List of log entry dictionaries
        endpoint_url: URL of the log aggregation endpoint
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds

    Returns:
        True if successfully sent

    Interview Question:
        Q: How do you handle log delivery failures?
        A: 1. Retry with backoff for transient failures
           2. Write to local fallback file if remote is down
           3. Monitor the log pipeline itself (meta-monitoring)
           4. Set alerts on log delivery lag
           5. Accept that some log loss is okay — prioritize app health
    """
    try:
        import requests

        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        response = requests.post(
            endpoint_url,
            json={'logs': entries},
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        logger.info(f"Sent {len(entries)} logs to {endpoint_url}")
        return True

    except ImportError:
        logger.warning("requests not installed — logging entries locally")
        for entry in entries:
            logger.info(f"[LOCAL] {json.dumps(entry)}")
        return True
    except Exception as e:
        logger.error(f"Failed to send logs: {e}")
        return False


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Log Aggregation Client — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Create structured log entries ----
    print("\n--- Example 1: Structured Log Entries ---")
    entry = create_log_entry(
        "Deployment completed",
        level="INFO",
        service="deploy-service",
        environment="production",
        version="2.1.0",
        duration_seconds=45
    )
    print(f"  {json.dumps(entry, indent=2)}")

    # ---- Example 2: Buffered logging ----
    print("\n--- Example 2: Buffered Logging ---")
    buffer = LogBuffer(max_size=5)

    # Add entries — will auto-flush when buffer reaches 5
    for i in range(7):
        buffer.add(create_log_entry(
            f"Processing item {i + 1}",
            service="batch-processor",
            item_id=i + 1
        ))

    # Flush remaining
    remaining = buffer.flush()
    print(f"  Flushed {len(remaining)} remaining entries")

    # ---- Example 3: Auto-flush with timer ----
    print("\n--- Example 3: Auto-Flush (background thread) ---")
    auto_buffer = LogBuffer(
        max_size=50,
        flush_interval=1.0
    )
    auto_buffer.start_auto_flush()

    # Add some entries
    for i in range(3):
        auto_buffer.add(create_log_entry(f"Event {i + 1}", service="event-processor"))
        time.sleep(0.3)

    # Wait for auto-flush
    time.sleep(1.5)
    auto_buffer.stop()
    print("  Auto-flush example completed")
