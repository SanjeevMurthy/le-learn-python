"""
aks_operations.py

Azure Kubernetes Service (AKS) cluster management.

Interview Topics:
- AKS vs EKS vs GKE comparison
- AKS node pool management
- Azure AD integration with AKS

Production Use Cases:
- Cluster inventory and health monitoring
- Node pool scaling
- Managed identity and RBAC integration

Prerequisites:
- azure-mgmt-containerservice, azure-identity
"""

import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_aks_client():
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.containerservice import ContainerServiceClient
    subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID', '')
    credential = DefaultAzureCredential()
    return ContainerServiceClient(credential, subscription_id)


def list_clusters(resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List AKS clusters.

    Interview Question:
        Q: Compare AKS, EKS, and GKE.
        A: AKS: free control plane, Azure AD integration, best for
           Azure-heavy orgs. Node auto-repair built in.
           EKS: $0.10/hr control plane, tight AWS integration,
           Fargate for serverless pods.
           GKE: most mature, Autopilot mode, best multi-cluster
           (Anthos), free tier with Autopilot.
           All support managed node pools, auto-scaling, and RBAC.
    """
    client = get_aks_client()

    clusters = []
    if resource_group:
        cluster_list = client.managed_clusters.list_by_resource_group(resource_group)
    else:
        cluster_list = client.managed_clusters.list()

    for cluster in cluster_list:
        node_pools = []
        for np in (cluster.agent_pool_profiles or []):
            node_pools.append({
                'name': np.name,
                'vm_size': np.vm_size,
                'count': np.count,
                'min_count': np.min_count,
                'max_count': np.max_count,
                'auto_scaling': np.enable_auto_scaling or False,
                'mode': np.mode,
            })

        clusters.append({
            'name': cluster.name,
            'location': cluster.location,
            'kubernetes_version': cluster.kubernetes_version,
            'provisioning_state': cluster.provisioning_state,
            'node_pools': node_pools,
            'fqdn': cluster.fqdn,
            'resource_group': cluster.id.split('/')[4] if cluster.id else 'N/A',
        })

    logger.info(f"Found {len(clusters)} AKS clusters")
    return clusters


def scale_node_pool(
    resource_group: str,
    cluster_name: str,
    node_pool_name: str,
    node_count: int
) -> Dict[str, Any]:
    """Scale an AKS node pool to a specific count."""
    client = get_aks_client()
    try:
        # Get current node pool config
        agent_pool = client.agent_pools.get(
            resource_group, cluster_name, node_pool_name
        )
        agent_pool.count = node_count

        poller = client.agent_pools.begin_create_or_update(
            resource_group, cluster_name, node_pool_name, agent_pool
        )
        logger.info(f"Scaling {node_pool_name} to {node_count} nodes")
        return {
            'cluster': cluster_name, 'node_pool': node_pool_name,
            'target_count': node_count, 'status': 'scaling'
        }
    except Exception as e:
        logger.error(f"Scale failed: {e}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("AKS Operations — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires Azure credentials.

    # List all AKS clusters
    clusters = list_clusters()
    for c in clusters:
        print(f"  {c['name']}: K8s {c['kubernetes_version']} ({c['provisioning_state']})")
        for np in c['node_pools']:
            print(f"    Pool {np['name']}: {np['vm_size']} x{np['count']}")

    # Scale a node pool
    scale_node_pool('my-rg', 'my-cluster', 'agentpool', 5)
    """)
