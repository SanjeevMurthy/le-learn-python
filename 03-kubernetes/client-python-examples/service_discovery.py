"""
service_discovery.py

Kubernetes Service and Endpoints management.

Interview Topics:
- Service types: ClusterIP, NodePort, LoadBalancer, ExternalName
- DNS-based service discovery in K8s
- Ingress vs Service vs Gateway API

Production Use Cases:
- Creating services for deployments
- Querying endpoints for health checks
- Setting up ingress rules programmatically

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


def list_services(
    namespace: str = 'default',
    label_selector: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List services in a namespace.

    Interview Question:
        Q: Explain K8s service types.
        A: ClusterIP: internal only, virtual IP, default type.
           NodePort: exposes on each node's IP at a static port (30000-32767).
           LoadBalancer: provisions cloud LB, superset of NodePort.
           ExternalName: CNAME alias to external DNS name.
           Headless (clusterIP: None): no virtual IP, DNS returns
           pod IPs directly — used for StatefulSets.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    kwargs = {}
    if label_selector:
        kwargs['label_selector'] = label_selector

    services = v1.list_namespaced_service(namespace, **kwargs)

    result = []
    for svc in services.items:
        ports = []
        for port in (svc.spec.ports or []):
            ports.append({
                'port': port.port,
                'target_port': str(port.target_port),
                'protocol': port.protocol,
                'node_port': port.node_port,
            })

        result.append({
            'name': svc.metadata.name,
            'namespace': svc.metadata.namespace,
            'type': svc.spec.type,
            'cluster_ip': svc.spec.cluster_ip,
            'external_ip': (
                svc.status.load_balancer.ingress[0].ip
                if (svc.status.load_balancer and svc.status.load_balancer.ingress)
                else 'N/A'
            ),
            'ports': ports,
            'selector': dict(svc.spec.selector or {}),
        })

    logger.info(f"Found {len(result)} services in {namespace}")
    return result


def create_service(
    name: str,
    selector: Dict[str, str],
    port: int,
    target_port: int = None,
    service_type: str = 'ClusterIP',
    namespace: str = 'default'
) -> Dict[str, Any]:
    """Create a K8s Service."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1ServiceSpec(
            type=service_type,
            selector=selector,
            ports=[client.V1ServicePort(
                port=port,
                target_port=target_port or port,
                protocol='TCP',
            )],
        ),
    )

    try:
        result = v1.create_namespaced_service(namespace, service)
        logger.info(f"Created service: {name} ({service_type})")
        return {
            'name': name, 'type': service_type,
            'cluster_ip': result.spec.cluster_ip, 'status': 'created'
        }
    except Exception as e:
        logger.error(f"Service creation failed: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def get_endpoints(name: str, namespace: str = 'default') -> Dict[str, Any]:
    """
    Get endpoint addresses for a service.

    Interview Question:
        Q: How does K8s DNS service discovery work?
        A: CoreDNS creates DNS records for each Service:
           <service>.<namespace>.svc.cluster.local → ClusterIP
           Pods can reach services by name within same namespace
           or by FQDN across namespaces. Headless services return
           A records for each pod IP. SRV records include port info.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        endpoints = v1.read_namespaced_endpoints(name, namespace)
        addresses = []
        for subset in (endpoints.subsets or []):
            for addr in (subset.addresses or []):
                addresses.append({
                    'ip': addr.ip,
                    'hostname': addr.hostname,
                    'node': addr.node_name,
                    'target_ref': addr.target_ref.name if addr.target_ref else 'N/A',
                })

        return {
            'service': name, 'namespace': namespace,
            'endpoints': addresses, 'ready_count': len(addresses),
        }
    except Exception as e:
        logger.error(f"Failed to get endpoints: {e}")
        return {'service': name, 'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("Service Discovery — Usage Examples")
    print("=" * 60)
    print("""
    # List all services
    services = list_services('default')
    for s in services:
        print(f"  {s['name']}: {s['type']} → {s['cluster_ip']}")

    # Create a service
    create_service('my-svc', {'app': 'web'}, port=80, target_port=8080)

    # Get endpoints
    eps = get_endpoints('my-svc')
    print(f"  Ready endpoints: {eps['ready_count']}")
    """)
