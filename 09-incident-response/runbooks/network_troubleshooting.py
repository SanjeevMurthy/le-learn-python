"""
network_troubleshooting.py

Network connectivity investigation tools.

Prerequisites:
- socket (stdlib), subprocess
"""

import socket
import subprocess
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_port(host: str, port: int, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check if a TCP port is reachable.

    Interview Question:
        Q: Walk through troubleshooting network connectivity issues.
        A: Layered approach (OSI bottom-up):
           1. Physical/Link: cable, NIC (`ip link`, `ethtool`)
           2. Network: IP, routing (`ip route`, `traceroute`)
           3. Transport: port open? (`telnet`, `nc -zv`)
           4. Application: DNS (`dig`), TLS (`openssl s_client`)
           5. Firewall: security groups, iptables, NACLs
           6. DNS: resolution (`nslookup`, TTL, caching)
           In K8s: also check NetworkPolicies, Service endpoints, kube-proxy.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        reachable = result == 0
        return {'host': host, 'port': port, 'reachable': reachable}
    except socket.gaierror:
        return {'host': host, 'port': port, 'reachable': False, 'error': 'DNS resolution failed'}


def check_dns(hostname: str) -> Dict[str, Any]:
    """Resolve a hostname."""
    try:
        ips = socket.getaddrinfo(hostname, None)
        addresses = list(set(addr[4][0] for addr in ips))
        return {'hostname': hostname, 'addresses': addresses, 'resolved': True}
    except socket.gaierror as e:
        return {'hostname': hostname, 'resolved': False, 'error': str(e)}


def run_traceroute(host: str) -> Dict[str, Any]:
    """Run traceroute to a host."""
    cmd = ['traceroute', '-m', '15', '-w', '2', host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        hops = []
        for line in result.stdout.strip().split('\n')[1:]:
            hops.append(line.strip())
        return {'host': host, 'hops': hops, 'hop_count': len(hops)}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {'host': host, 'error': str(e)}


def connectivity_check(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check connectivity to multiple targets."""
    results = []
    for target in targets:
        result = check_port(target['host'], target['port'])
        result['service'] = target.get('name', f"{target['host']}:{target['port']}")
        results.append(result)
        status = "✅" if result['reachable'] else "❌"
        logger.info(f"{status} {result['service']}")
    return results


if __name__ == "__main__":
    print("Network Troubleshooting")
    targets = [
        {'host': 'google.com', 'port': 443, 'name': 'Google HTTPS'},
        {'host': 'localhost', 'port': 8080, 'name': 'Local app'},
    ]
    for r in connectivity_check(targets):
        status = "✅" if r['reachable'] else "❌"
        print(f"  {status} {r['service']}")
