"""
network_latency.py

Network latency measurement and analysis.

Prerequisites:
- subprocess, socket (stdlib)
"""

import subprocess
import time
import socket
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def measure_tcp_latency(
    host: str, port: int = 443, samples: int = 5
) -> Dict[str, Any]:
    """
    Measure TCP connection latency.

    Interview Question:
        Q: What causes network latency and how do you measure it?
        A: Sources: physical distance, routing hops, congestion,
           DNS resolution, TLS handshake, packet loss + retransmission.
           Measurement: ping (ICMP RTT), TCP connect time,
           application-level (HTTP TTFB).
           Tools: mtr (combines ping + traceroute), curl -w timing.
           Optimization: CDN, connection pooling, keep-alive,
           HTTP/2 multiplexing, edge computing.
    """
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.close()
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(round(elapsed, 2))
        except socket.error:
            latencies.append(-1)

    valid = [l for l in latencies if l >= 0]
    if not valid:
        return {'host': host, 'port': port, 'error': 'All connections failed'}

    valid.sort()
    return {
        'host': host,
        'port': port,
        'samples': len(valid),
        'min_ms': valid[0],
        'max_ms': valid[-1],
        'avg_ms': round(sum(valid) / len(valid), 2),
        'median_ms': valid[len(valid) // 2],
    }


def ping_host(host: str, count: int = 5) -> Dict[str, Any]:
    """Ping a host and parse results."""
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', '2', host],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            # Parse summary line
            lines = result.stdout.strip().split('\n')
            stats_line = [l for l in lines if 'avg' in l or 'round-trip' in l]
            return {'host': host, 'reachable': True, 'output': stats_line[-1] if stats_line else ''}
        return {'host': host, 'reachable': False}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {'host': host, 'reachable': False}


if __name__ == "__main__":
    print("Network Latency")
    for host in ['google.com', 'github.com']:
        result = measure_tcp_latency(host, 443, samples=3)
        print(f"  {host}: avg={result.get('avg_ms', '?')}ms, min={result.get('min_ms', '?')}ms")
