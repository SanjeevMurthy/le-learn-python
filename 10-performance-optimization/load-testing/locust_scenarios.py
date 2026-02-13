"""
locust_scenarios.py

Load testing scenarios using Locust framework.

Interview Topics:
- Load testing vs stress testing
- Percentile latencies (p50, p95, p99)
- Finding the saturation point

Prerequisites:
- locust (pip install locust)
"""

import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from locust import HttpUser, task, between, events
    from locust.env import Environment

    class APILoadTest(HttpUser):
        """
        Load test for a REST API.

        Interview Question:
            Q: How do you determine the capacity of a service?
            A: 1. Define SLOs (p99 < 200ms, error rate < 0.1%)
               2. Start with low load, gradually increase (ramp-up)
               3. Monitor: latency, error rate, CPU, memory, connections
               4. Saturation point: where SLOs start to degrade
               5. Capacity = highest RPS where SLOs are still met
               6. Plan for 2x headroom above normal peak traffic
        """
        wait_time = between(1, 3)

        @task(3)
        def get_health(self):
            self.client.get('/health')

        @task(2)
        def get_items(self):
            self.client.get('/api/items')

        @task(1)
        def create_item(self):
            self.client.post('/api/items', json={'name': 'test'})

    class WebsiteLoadTest(HttpUser):
        """Simulate realistic website browsing."""
        wait_time = between(2, 5)

        @task(5)
        def homepage(self):
            self.client.get('/')

        @task(3)
        def search(self):
            self.client.get('/search?q=test')

        @task(1)
        def profile(self):
            self.client.get('/profile')

except ImportError:
    logger.info("locust not installed — load test classes unavailable")


def generate_locust_config(
    host: str,
    users: int = 100,
    spawn_rate: int = 10,
    run_time: str = '5m'
) -> Dict[str, Any]:
    """Generate Locust CLI command."""
    cmd = (
        f"locust -f locust_scenarios.py --host={host} "
        f"--users={users} --spawn-rate={spawn_rate} "
        f"--run-time={run_time} --headless"
    )
    return {'command': cmd, 'users': users, 'spawn_rate': spawn_rate}


if __name__ == "__main__":
    print("Locust Load Testing — Usage Examples")
    config = generate_locust_config('http://localhost:8080', users=50)
    print(f"  Run: {config['command']}")
    print("""
    # Or with web UI:
    locust -f locust_scenarios.py --host=http://localhost:8080
    # Open http://localhost:8089
    """)
