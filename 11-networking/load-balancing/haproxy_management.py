"""
haproxy_management.py

HAProxy configuration and stats API.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, List

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_stats(stats_url: str = '') -> List[Dict[str, Any]]:
    """
    Get HAProxy backend stats.

    Interview Question:
        Q: HAProxy vs Nginx for load balancing?
        A: HAProxy: purpose-built LB, advanced health checks (L4+L7),
           connection draining, stick tables, detailed stats API.
           Nginx: web server + reverse proxy, static content serving,
           simpler config, can also LB. Better for serving + proxying.
           HAProxy: better for pure load balancing, connection management.
           Both: support HTTP/2, TLS termination, rate limiting.
           Production: often both — Nginx edge → HAProxy internal LB.
    """
    url = stats_url or os.environ.get('HAPROXY_STATS_URL', 'http://localhost:8404/stats')
    try:
        response = requests.get(f'{url};csv')
        if response.status_code != 200:
            return []

        lines = response.text.strip().split('\n')
        headers = [h.strip('# ') for h in lines[0].split(',')]

        backends = []
        for line in lines[1:]:
            values = line.split(',')
            if len(values) >= len(headers):
                entry = dict(zip(headers, values))
                if entry.get('svname') not in ('FRONTEND', 'BACKEND'):
                    backends.append({
                        'proxy': entry.get('pxname', ''),
                        'server': entry.get('svname', ''),
                        'status': entry.get('status', ''),
                        'current_sessions': int(entry.get('scur', 0)),
                        'total_sessions': int(entry.get('stot', 0)),
                        'bytes_in': int(entry.get('bin', 0)),
                        'bytes_out': int(entry.get('bout', 0)),
                    })
        return backends
    except Exception as e:
        logger.error(f"Failed to get HAProxy stats: {e}")
        return []


def generate_haproxy_config(
    frontends: List[Dict[str, Any]],
    backends: List[Dict[str, Any]]
) -> str:
    """Generate a basic HAProxy configuration."""
    config = """global
    daemon
    maxconn 4096
    log stdout format raw local0

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    option httplog
    option dontlognull

"""

    for fe in frontends:
        config += f"frontend {fe['name']}\n"
        config += f"    bind *:{fe.get('port', 80)}\n"
        config += f"    default_backend {fe['backend']}\n\n"

    for be in backends:
        config += f"backend {be['name']}\n"
        config += f"    balance {be.get('algorithm', 'roundrobin')}\n"
        config += "    option httpchk GET /health\n"
        for server in be.get('servers', []):
            config += f"    server {server['name']} {server['address']} check\n"
        config += "\n"

    return config


if __name__ == "__main__":
    print("HAProxy Management — Usage Examples")
    config = generate_haproxy_config(
        frontends=[{'name': 'http_front', 'port': 80, 'backend': 'app_servers'}],
        backends=[{
            'name': 'app_servers',
            'algorithm': 'leastconn',
            'servers': [
                {'name': 'app1', 'address': '10.0.1.1:8080'},
                {'name': 'app2', 'address': '10.0.1.2:8080'},
            ]
        }]
    )
    print(config)
