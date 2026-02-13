"""
network_debugging.py

Kubernetes network troubleshooting utilities.

Interview Topics:
- Pod-to-pod networking
- Service DNS resolution
- NetworkPolicy debugging

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_kube_config():
    from kubernetes import config
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def check_service_endpoints(namespace: str = 'default') -> List[Dict[str, Any]]:
    """
    Find services with no ready endpoints (potential connectivity issues).

    Interview Question:
        Q: How does pod-to-pod networking work in K8s?
        A: The K8s network model requires:
           1. Every pod gets a unique IP
           2. Pods on any node can communicate without NAT
           3. Implemented by CNI plugins (Calico, Cilium, Flannel)
           4. Services use kube-proxy (iptables/IPVS) or eBPF
              to load-balance across pod IPs
           5. DNS resolution via CoreDNS (svc.namespace.svc.cluster.local)
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    services = v1.list_namespaced_service(namespace)
    issues = []

    for svc in services.items:
        if svc.spec.type == 'ExternalName':
            continue

        try:
            endpoints = v1.read_namespaced_endpoints(svc.metadata.name, namespace)
            ready_count = sum(
                len(subset.addresses or [])
                for subset in (endpoints.subsets or [])
            )

            if ready_count == 0:
                issues.append({
                    'service': svc.metadata.name,
                    'type': svc.spec.type,
                    'selector': dict(svc.spec.selector or {}),
                    'issue': 'No ready endpoints',
                    'fix': 'Check if pods match selector labels and are Ready',
                })
        except Exception as e:
            issues.append({
                'service': svc.metadata.name,
                'issue': f'Cannot read endpoints: {e}',
            })

    logger.info(f"Found {len(issues)} services with endpoint issues in {namespace}")
    return issues


def list_network_policies(namespace: str = 'default') -> List[Dict[str, Any]]:
    """
    List NetworkPolicies and their rules.

    Interview Question:
        Q: How do NetworkPolicies work?
        A: By default, all pods can communicate. NetworkPolicies
           are additive — they whitelist traffic. If ANY policy
           selects a pod, only traffic allowed by policies gets through.
           Types: Ingress (incoming), Egress (outgoing).
           Key gotcha: if you create an empty policy selecting pods,
           ALL traffic to/from those pods is denied.
    """
    from kubernetes import client
    load_kube_config()
    networking_v1 = client.NetworkingV1Api()

    policies = networking_v1.list_namespaced_network_policy(namespace)

    result = []
    for policy in policies.items:
        ingress_rules = len(policy.spec.ingress or []) if policy.spec.ingress else 0
        egress_rules = len(policy.spec.egress or []) if policy.spec.egress else 0

        result.append({
            'name': policy.metadata.name,
            'pod_selector': dict(policy.spec.pod_selector.match_labels or {}),
            'policy_types': policy.spec.policy_types or [],
            'ingress_rules': ingress_rules,
            'egress_rules': egress_rules,
        })

    return result


def check_dns_resolution(
    service_name: str,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """Check DNS resolution for a service (via API)."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    fqdn = f"{service_name}.{namespace}.svc.cluster.local"

    try:
        svc = v1.read_namespaced_service(service_name, namespace)
        return {
            'service': service_name,
            'fqdn': fqdn,
            'cluster_ip': svc.spec.cluster_ip,
            'type': svc.spec.type,
            'resolved': True,
        }
    except Exception as e:
        return {
            'service': service_name, 'fqdn': fqdn,
            'resolved': False, 'error': str(e),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("Network Debugging — Usage Examples")
    print("=" * 60)
    print("""
    # Find services with no endpoints
    issues = check_service_endpoints('production')
    for i in issues:
        print(f"  ⚠️ {i['service']}: {i['issue']}")

    # List network policies
    policies = list_network_policies('production')

    # Check DNS
    dns = check_dns_resolution('my-service', 'production')
    print(f"  {dns['fqdn']} → {dns.get('cluster_ip', 'N/A')}")
    """)
