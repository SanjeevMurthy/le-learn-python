"""
statsd_client.py

StatsD client for sending custom metrics.

Prerequisites:
- Standard library only (uses UDP socket)
"""

import socket
import logging
import time
import random
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StatsDClient:
    """
    Simple StatsD client.

    Interview Question:
        Q: StatsD vs Prometheus — when to use each?
        A: StatsD: push-based, UDP, fire-and-forget, low overhead.
           Good for high-frequency metrics from application code.
           Prometheus: pull-based, scrapes /metrics endpoint.
           Better for infrastructure monitoring, service discovery,
           powerful query language (PromQL). In practice, use both:
           StatsD for app-level metrics → StatsD exporter → Prometheus.
    """

    def __init__(self, host: str = 'localhost', port: int = 8125, prefix: str = ''):
        self.host = host
        self.port = port
        self.prefix = f'{prefix}.' if prefix else ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _send(self, metric: str, value: str, metric_type: str, sample_rate: float = 1.0):
        """Send a metric to StatsD."""
        name = f'{self.prefix}{metric}'
        data = f'{name}:{value}|{metric_type}'
        if sample_rate < 1.0:
            data += f'|@{sample_rate}'
        try:
            self.sock.sendto(data.encode(), (self.host, self.port))
        except Exception as e:
            logger.debug(f"StatsD send failed: {e}")

    def increment(self, metric: str, count: int = 1, sample_rate: float = 1.0):
        """Increment a counter."""
        self._send(metric, str(count), 'c', sample_rate)

    def gauge(self, metric: str, value: float):
        """Set a gauge value."""
        self._send(metric, str(value), 'g')

    def timing(self, metric: str, ms: float, sample_rate: float = 1.0):
        """Record a timing value in milliseconds."""
        self._send(metric, str(ms), 'ms', sample_rate)

    def histogram(self, metric: str, value: float):
        """Record a histogram value (DataDog extension)."""
        self._send(metric, str(value), 'h')

    def timer(self, metric: str):
        """Context manager for timing code blocks."""
        return _Timer(self, metric)


class _Timer:
    def __init__(self, client: StatsDClient, metric: str):
        self.client = client
        self.metric = metric
        self.start = 0.0

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, *args):
        elapsed_ms = (time.monotonic() - self.start) * 1000
        self.client.timing(self.metric, elapsed_ms)


if __name__ == "__main__":
    print("StatsD Client — Usage Examples")
    print("""
    client = StatsDClient('localhost', 8125, prefix='myapp')

    # Counter
    client.increment('requests.total')
    client.increment('requests.errors', count=1)

    # Gauge
    client.gauge('connections.active', 42)

    # Timing
    with client.timer('handler.duration'):
        time.sleep(0.1)  # Your code here
    """)
