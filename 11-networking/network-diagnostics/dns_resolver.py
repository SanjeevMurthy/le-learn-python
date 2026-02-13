"""
dns_resolver.py

DNS resolution and lookup utilities.

Prerequisites:
- socket (stdlib)
"""

import socket
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def resolve_hostname(hostname: str) -> Dict[str, Any]:
    """
    Resolve a hostname to IP addresses.

    Interview Question:
        Q: Explain DNS resolution in Kubernetes.
        A: CoreDNS runs as pods in kube-system namespace.
           Service DNS: <svc>.<ns>.svc.cluster.local → ClusterIP.
           Pod DNS: <pod-ip-dashed>.<ns>.pod.cluster.local.
           Headless service (ClusterIP: None): returns pod IPs directly.
           ndots:5 in /etc/resolv.conf: short names get 5 search suffixes.
           Common issue: DNS resolution slow → check CoreDNS logs/metrics.
    """
    try:
        results = socket.getaddrinfo(hostname, None)
        ipv4 = list(set(r[4][0] for r in results if r[0] == socket.AF_INET))
        ipv6 = list(set(r[4][0] for r in results if r[0] == socket.AF_INET6))
        return {
            'hostname': hostname,
            'ipv4': ipv4,
            'ipv6': ipv6,
            'resolved': True,
        }
    except socket.gaierror as e:
        return {'hostname': hostname, 'resolved': False, 'error': str(e)}


def reverse_dns(ip: str) -> Dict[str, Any]:
    """Perform reverse DNS lookup."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return {'ip': ip, 'hostname': hostname, 'resolved': True}
    except socket.herror:
        return {'ip': ip, 'resolved': False}


def check_dns_propagation(hostname: str, expected_ip: str) -> Dict[str, Any]:
    """Check if DNS has propagated to expected IP."""
    result = resolve_hostname(hostname)
    if not result['resolved']:
        return {'hostname': hostname, 'propagated': False, 'error': 'DNS resolution failed'}

    all_ips = result['ipv4'] + result['ipv6']
    return {
        'hostname': hostname,
        'expected_ip': expected_ip,
        'actual_ips': all_ips,
        'propagated': expected_ip in all_ips,
    }


if __name__ == "__main__":
    print("DNS Resolver")
    for host in ['google.com', 'github.com']:
        result = resolve_hostname(host)
        print(f"  {host}: {result.get('ipv4', [])}")
