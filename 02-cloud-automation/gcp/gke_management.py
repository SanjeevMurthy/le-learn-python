"""
gke_management.py

GCP Google Kubernetes Engine (GKE) cluster management.

Interview Topics:
- GKE vs EKS vs AKS comparison
- GKE Autopilot vs Standard mode
- Node pool management and auto-scaling

Production Use Cases:
- Cluster inventory and health monitoring
- Node pool scaling operations
- Workload deployment status

Prerequisites:
- google-cloud-container (pip install google-cloud-container)
"""

import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_gke_client():
    from google.cloud import container_v1
    return container_v1.ClusterManagerClient()


def list_clusters(project: str, location: str = '-') -> List[Dict[str, Any]]:
    """
    List all GKE clusters in a project.

    Args:
        project: GCP project ID
        location: Zone or region ('-' for all)

    Interview Question:
        Q: Compare GKE Autopilot vs Standard mode.
        A: Autopilot: Google manages nodes, pay per pod, auto-scales,
           built-in security hardening. Great for teams without
           deep K8s expertise.
           Standard: you manage nodes, more control over machine types,
           GPU support, more flexible but more operational overhead.
           Rule of thumb: start with Autopilot, move to Standard
           when you need fine-grained control.
    """
    client = get_gke_client()
    parent = f"projects/{project}/locations/{location}"

    try:
        response = client.list_clusters(parent=parent)
        clusters = []
        for cluster in response.clusters:
            clusters.append({
                'name': cluster.name,
                'location': cluster.location,
                'status': cluster.status.name,
                'node_count': cluster.current_node_count,
                'master_version': cluster.current_master_version,
                'node_version': cluster.current_node_version,
                'endpoint': cluster.endpoint,
                'autopilot': cluster.autopilot.enabled if cluster.autopilot else False,
            })
        logger.info(f"Found {len(clusters)} GKE clusters")
        return clusters
    except Exception as e:
        logger.error(f"Failed to list clusters: {e}")
        return []


def get_cluster_details(
    project: str,
    location: str,
    cluster_name: str
) -> Dict[str, Any]:
    """Get detailed info about a specific GKE cluster."""
    client = get_gke_client()
    name = f"projects/{project}/locations/{location}/clusters/{cluster_name}"

    try:
        cluster = client.get_cluster(name=name)
        node_pools = []
        for np in cluster.node_pools:
            node_pools.append({
                'name': np.name,
                'machine_type': np.config.machine_type,
                'node_count': np.initial_node_count,
                'autoscaling': np.autoscaling.enabled if np.autoscaling else False,
                'min_nodes': np.autoscaling.min_node_count if np.autoscaling else 0,
                'max_nodes': np.autoscaling.max_node_count if np.autoscaling else 0,
                'status': np.status.name,
            })

        return {
            'name': cluster.name,
            'status': cluster.status.name,
            'master_version': cluster.current_master_version,
            'node_pools': node_pools,
            'network': cluster.network,
            'subnetwork': cluster.subnetwork,
            'endpoint': cluster.endpoint,
        }
    except Exception as e:
        logger.error(f"Failed to get cluster details: {e}")
        return {'status': 'error', 'error': str(e)}


def resize_node_pool(
    project: str,
    location: str,
    cluster_name: str,
    node_pool_name: str,
    node_count: int
) -> Dict[str, Any]:
    """Resize a GKE node pool."""
    client = get_gke_client()
    name = (
        f"projects/{project}/locations/{location}/"
        f"clusters/{cluster_name}/nodePools/{node_pool_name}"
    )

    try:
        operation = client.set_node_pool_size(name=name, node_count=node_count)
        logger.info(f"Resizing {node_pool_name} to {node_count} nodes")
        return {
            'node_pool': node_pool_name, 'target_size': node_count,
            'status': 'resizing', 'operation': operation.name,
        }
    except Exception as e:
        logger.error(f"Resize failed: {e}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("GKE Management — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires GCP credentials.

    # List all clusters
    clusters = list_clusters('my-project')
    for c in clusters:
        print(f"  {c['name']}: {c['node_count']} nodes ({c['status']})")

    # Get cluster details
    details = get_cluster_details('my-project', 'us-central1', 'my-cluster')
    for np in details.get('node_pools', []):
        print(f"  Pool {np['name']}: {np['machine_type']}")
    """)
