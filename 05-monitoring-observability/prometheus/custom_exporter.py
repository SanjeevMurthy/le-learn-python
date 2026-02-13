"""
custom_exporter.py

Build a custom Prometheus exporter using prometheus_client.

Prerequisites:
- prometheus_client (pip install prometheus-client)
"""

import logging
import time
import random
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_exporter(port: int = 9100) -> Dict[str, Any]:
    """
    Create a custom Prometheus exporter with metrics.

    Interview Question:
        Q: What are the four Prometheus metric types?
        A: Counter: monotonically increasing (requests_total).
           Gauge: can go up/down (current_temperature, active_connections).
           Histogram: observations in configurable buckets (request_duration).
              Also provides _sum and _count. Use for latency/sizes.
           Summary: similar to histogram but calculates quantiles client-side.
              Less flexible, use histogram with histogram_quantile() instead.
    """
    from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

    # Define metrics
    request_counter = Counter(
        'app_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )
    active_connections = Gauge(
        'app_active_connections',
        'Number of active connections'
    )
    request_duration = Histogram(
        'app_request_duration_seconds',
        'Request duration in seconds',
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )
    request_summary = Summary(
        'app_request_latency_seconds',
        'Request latency summary'
    )

    # Start the metrics HTTP server
    start_http_server(port)
    logger.info(f"Exporter running on :{port}/metrics")

    return {
        'counter': request_counter,
        'gauge': active_connections,
        'histogram': request_duration,
        'summary': request_summary,
    }


def simulate_metrics(metrics: Dict[str, Any], iterations: int = 100) -> None:
    """Simulate metric updates for demonstration."""
    for i in range(iterations):
        # Simulate request
        method = random.choice(['GET', 'POST', 'PUT'])
        endpoint = random.choice(['/api/users', '/api/orders', '/health'])
        status = random.choice(['200', '200', '200', '500'])

        metrics['counter'].labels(method=method, endpoint=endpoint, status=status).inc()
        metrics['gauge'].set(random.randint(10, 100))

        duration = random.uniform(0.01, 2.0)
        metrics['histogram'].observe(duration)
        metrics['summary'].observe(duration)

        time.sleep(0.1)


if __name__ == "__main__":
    print("Custom Exporter — Usage Examples")
    print("""
    metrics = create_exporter(port=9100)
    simulate_metrics(metrics, iterations=1000)
    # Visit http://localhost:9100/metrics to see metrics
    """)
