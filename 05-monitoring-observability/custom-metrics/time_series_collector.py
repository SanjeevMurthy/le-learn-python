"""
time_series_collector.py

Collect and buffer time-series metrics for batch publishing.

Prerequisites:
- Standard library only
"""

import time
import logging
import threading
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_collector(
    flush_fn: Callable[[List[Dict[str, Any]]], None],
    flush_interval: int = 60,
    max_buffer: int = 1000
) -> Dict[str, Any]:
    """
    Create a buffered metric collector that flushes periodically.

    Interview Question:
        Q: Why buffer metrics instead of sending immediately?
        A: 1. Reduces network overhead (batch HTTP requests)
           2. Handles burst traffic without overloading backend
           3. Allows aggregation before sending (pre-aggregation)
           4. More resilient to backend outages (local buffer)
           Tradeoff: data loss risk if process crashes before flush.
           Mitigate with shorter flush intervals and WAL (write-ahead log).
    """
    buffer = []
    lock = threading.Lock()
    running = True

    def record(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric data point."""
        point = {
            'name': metric_name,
            'value': value,
            'timestamp': time.time(),
            'tags': tags or {},
        }
        with lock:
            buffer.append(point)
            if len(buffer) >= max_buffer:
                _flush()

    def _flush():
        """Flush the buffer to the backend."""
        nonlocal buffer
        if not buffer:
            return
        to_send = buffer[:]
        buffer = []
        try:
            flush_fn(to_send)
            logger.info(f"Flushed {len(to_send)} data points")
        except Exception as e:
            logger.error(f"Flush failed: {e}")
            # Put data back in buffer (best-effort)
            buffer = to_send + buffer

    def _flush_loop():
        while running:
            time.sleep(flush_interval)
            with lock:
                _flush()

    # Start background flush thread
    flush_thread = threading.Thread(target=_flush_loop, daemon=True)
    flush_thread.start()

    return {
        'record': record,
        'flush': lambda: _flush(),
    }


if __name__ == "__main__":
    print("Time Series Collector — Usage Examples")
    print("""
    def flush_handler(data_points):
        print(f"Flushing {len(data_points)} points")

    collector = create_collector(flush_handler, flush_interval=10)
    collector['record']('cpu.usage', 45.2, tags={'host': 'web-01'})
    collector['record']('memory.used_mb', 2048, tags={'host': 'web-01'})
    """)
