"""
port_scanner.py

TCP port scanning utility.

Prerequisites:
- socket (stdlib), concurrent.futures (stdlib)
"""

import socket
import logging
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scan_port(host: str, port: int, timeout: float = 2.0) -> Dict[str, Any]:
    """Check if a single TCP port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return {'port': port, 'open': result == 0}
    except socket.error:
        return {'port': port, 'open': False}


def scan_ports(
    host: str,
    ports: List[int] = None,
    timeout: float = 1.0,
    max_workers: int = 50
) -> Dict[str, Any]:
    """
    Scan multiple ports concurrently.

    Interview Question:
        Q: What's the difference between TCP and UDP scanning?
        A: TCP: SYN → SYN-ACK = open, RST = closed. Reliable, 3-way handshake.
           UDP: send packet → no response = open|filtered, ICMP unreachable = closed.
           UDP is slower and less reliable (no handshake).
           Tools: nmap (-sT TCP connect, -sS SYN stealth, -sU UDP).
           In SRE: TCP scans verify service availability, port 80/443/8080 etc.
    """
    if ports is None:
        ports = [22, 80, 443, 3306, 5432, 6379, 8080, 8443, 9090, 27017]

    open_ports = []
    closed_ports = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_port, host, p, timeout): p for p in ports}
        for future in as_completed(futures):
            result = future.result()
            if result['open']:
                open_ports.append(result['port'])
            else:
                closed_ports.append(result['port'])

    open_ports.sort()
    return {
        'host': host,
        'open_ports': open_ports,
        'closed_ports': sorted(closed_ports),
        'total_scanned': len(ports),
    }


# Well-known port to service mapping
COMMON_PORTS = {
    22: 'SSH', 80: 'HTTP', 443: 'HTTPS', 3306: 'MySQL',
    5432: 'PostgreSQL', 6379: 'Redis', 8080: 'HTTP-Alt',
    8443: 'HTTPS-Alt', 9090: 'Prometheus', 27017: 'MongoDB',
}


if __name__ == "__main__":
    print("Port Scanner")
    result = scan_ports('localhost')
    for port in result['open_ports']:
        service = COMMON_PORTS.get(port, 'unknown')
        print(f"  ✅ {port}/{service} — open")
    print(f"  Scanned {result['total_scanned']} ports, {len(result['open_ports'])} open")
