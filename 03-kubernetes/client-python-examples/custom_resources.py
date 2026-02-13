"""
custom_resources.py

Kubernetes Custom Resource Definition (CRD) management.

Interview Topics:
- What are CRDs and why are they important?
- Operator pattern
- Custom controllers vs CRDs

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


def list_crds() -> List[Dict[str, Any]]:
    """
    List all CustomResourceDefinitions in the cluster.

    Interview Question:
        Q: What is the Operator pattern?
        A: An Operator extends K8s with domain-specific knowledge:
           1. CRD defines a custom resource type (e.g., PostgresCluster)
           2. Controller watches for CRD instances and reconciles
           3. Controller encodes operational knowledge (backup, failover)
           Examples: Prometheus Operator, Cert-Manager, Strimzi (Kafka)
           Build with: Operator SDK, Kubebuilder, or raw client-go
    """
    from kubernetes import client
    load_kube_config()
    api = client.ApiextensionsV1Api()

    crds = api.list_custom_resource_definition()
    result = []
    for crd in crds.items:
        result.append({
            'name': crd.metadata.name,
            'group': crd.spec.group,
            'kind': crd.spec.names.kind,
            'scope': crd.spec.scope,
            'versions': [v.name for v in crd.spec.versions],
        })

    logger.info(f"Found {len(result)} CRDs")
    return result


def list_custom_resources(
    group: str,
    version: str,
    plural: str,
    namespace: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List instances of a custom resource."""
    from kubernetes import client
    load_kube_config()
    api = client.CustomObjectsApi()

    try:
        if namespace:
            resources = api.list_namespaced_custom_object(
                group, version, namespace, plural
            )
        else:
            resources = api.list_cluster_custom_object(group, version, plural)

        items = []
        for item in resources.get('items', []):
            items.append({
                'name': item['metadata']['name'],
                'namespace': item['metadata'].get('namespace', 'N/A'),
                'spec': item.get('spec', {}),
                'status': item.get('status', {}),
            })

        logger.info(f"Found {len(items)} {plural}")
        return items
    except Exception as e:
        logger.error(f"Failed to list custom resources: {e}")
        return []


def create_custom_resource(
    group: str,
    version: str,
    plural: str,
    namespace: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an instance of a custom resource."""
    from kubernetes import client
    load_kube_config()
    api = client.CustomObjectsApi()

    try:
        result = api.create_namespaced_custom_object(
            group, version, namespace, plural, body
        )
        logger.info(f"Created custom resource: {result['metadata']['name']}")
        return {'name': result['metadata']['name'], 'status': 'created'}
    except Exception as e:
        logger.error(f"Failed to create custom resource: {e}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("Custom Resources — Usage Examples")
    print("=" * 60)
    print("""
    # List all CRDs
    crds = list_crds()
    for crd in crds:
        print(f"  {crd['kind']} ({crd['group']})")

    # List Prometheus ServiceMonitors
    monitors = list_custom_resources(
        'monitoring.coreos.com', 'v1', 'servicemonitors', 'monitoring'
    )
    """)
