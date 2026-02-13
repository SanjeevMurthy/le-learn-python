"""
nginx_config_generator.py

Nginx configuration generation for load balancing.

Prerequisites:
- Standard library
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_upstream(
    name: str,
    backends: List[Dict[str, Any]],
    algorithm: str = 'round_robin'
) -> str:
    """
    Generate Nginx upstream block.

    Interview Question:
        Q: Explain load balancing algorithms.
        A: Round-robin: equal distribution (default).
           Weighted: backends get proportional traffic.
           Least connections: route to backend with fewest active conns.
           IP hash: same client IP → same backend (session affinity).
           Random with two choices (power of two): pick 2 random, choose least loaded.
           Consistent hashing: minimize remapping when backends change.
    """
    config = f"upstream {name} {{\n"

    if algorithm == 'least_conn':
        config += "    least_conn;\n"
    elif algorithm == 'ip_hash':
        config += "    ip_hash;\n"

    for backend in backends:
        server_line = f"    server {backend['address']}"
        if backend.get('weight'):
            server_line += f" weight={backend['weight']}"
        if backend.get('max_fails'):
            server_line += f" max_fails={backend['max_fails']}"
        if backend.get('backup'):
            server_line += " backup"
        server_line += ";"
        config += server_line + "\n"

    config += "}\n"
    return config


def generate_server_block(
    server_name: str,
    upstream_name: str,
    listen_port: int = 80,
    ssl: bool = False,
    rate_limit: str = ''
) -> str:
    """Generate Nginx server block with reverse proxy."""
    config = "server {\n"
    config += f"    listen {listen_port};\n"
    config += f"    server_name {server_name};\n\n"

    if ssl:
        config += "    listen 443 ssl;\n"
        config += "    ssl_certificate /etc/nginx/ssl/cert.pem;\n"
        config += "    ssl_certificate_key /etc/nginx/ssl/key.pem;\n"
        config += "    ssl_protocols TLSv1.2 TLSv1.3;\n\n"

    if rate_limit:
        config += f"    limit_req zone={rate_limit} burst=20 nodelay;\n\n"

    config += "    location / {\n"
    config += f"        proxy_pass http://{upstream_name};\n"
    config += "        proxy_set_header Host $host;\n"
    config += "        proxy_set_header X-Real-IP $remote_addr;\n"
    config += "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    config += "        proxy_set_header X-Forwarded-Proto $scheme;\n"
    config += "    }\n\n"

    config += "    location /health {\n"
    config += "        return 200 'OK';\n"
    config += "        add_header Content-Type text/plain;\n"
    config += "    }\n"
    config += "}\n"
    return config


if __name__ == "__main__":
    backends = [
        {'address': '10.0.1.1:8080', 'weight': 3},
        {'address': '10.0.1.2:8080', 'weight': 2},
        {'address': '10.0.1.3:8080', 'backup': True},
    ]

    print(generate_upstream('my_app', backends, algorithm='least_conn'))
    print(generate_server_block('app.example.com', 'my_app', ssl=True))
