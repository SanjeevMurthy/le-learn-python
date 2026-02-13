"""
compute_engine.py

GCP Compute Engine instance management.

Interview Topics:
- GCP vs AWS compute model differences
- Preemptible/Spot VMs for cost savings
- Managed instance groups vs ASGs

Production Use Cases:
- Instance lifecycle management
- Preemptible VM fleet management
- Label-based resource organization

Prerequisites:
- google-cloud-compute (pip install google-cloud-compute)
- GCP credentials (GOOGLE_APPLICATION_CREDENTIALS env var or gcloud auth)
"""

import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_compute_client():
    """Create a GCP Compute Engine client."""
    from google.cloud import compute_v1
    return compute_v1.InstancesClient()


def list_instances(
    project: str,
    zone: str = 'us-central1-a',
    label_filter: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    List Compute Engine instances with optional label filtering.

    Interview Question:
        Q: How do GCP labels compare to AWS tags?
        A: Similar concept but different implementation:
           - GCP labels: key-value, lowercase + hyphens only, 64 labels max
           - AWS tags: key-value, case-sensitive, 50 tags max
           - Both used for billing, organization, and automation
           - GCP also has network tags (for firewall rules) — distinct from labels
    """
    client = get_compute_client()
    instances = []

    request = {'project': project, 'zone': zone}
    for instance in client.list(**request):
        inst_labels = dict(instance.labels) if instance.labels else {}

        # Apply label filter
        if label_filter:
            if not all(inst_labels.get(k) == v for k, v in label_filter.items()):
                continue

        instances.append({
            'name': instance.name,
            'machine_type': instance.machine_type.split('/')[-1],
            'status': instance.status,
            'zone': zone,
            'internal_ip': (
                instance.network_interfaces[0].network_i_p
                if instance.network_interfaces else 'N/A'
            ),
            'external_ip': (
                instance.network_interfaces[0].access_configs[0].nat_i_p
                if (instance.network_interfaces and
                    instance.network_interfaces[0].access_configs)
                else 'N/A'
            ),
            'labels': inst_labels,
            'creation_timestamp': instance.creation_timestamp,
        })

    logger.info(f"Found {len(instances)} instances in {zone}")
    return instances


def stop_instance(project: str, zone: str, instance_name: str) -> Dict[str, Any]:
    """Stop a running Compute Engine instance."""
    client = get_compute_client()
    try:
        operation = client.stop(project=project, zone=zone, instance=instance_name)
        logger.info(f"Stopping instance: {instance_name}")
        return {'instance': instance_name, 'status': 'stopping', 'operation': operation.name}
    except Exception as e:
        logger.error(f"Failed to stop {instance_name}: {e}")
        return {'instance': instance_name, 'status': 'error', 'error': str(e)}


def start_instance(project: str, zone: str, instance_name: str) -> Dict[str, Any]:
    """Start a stopped Compute Engine instance."""
    client = get_compute_client()
    try:
        operation = client.start(project=project, zone=zone, instance=instance_name)
        logger.info(f"Starting instance: {instance_name}")
        return {'instance': instance_name, 'status': 'starting', 'operation': operation.name}
    except Exception as e:
        logger.error(f"Failed to start {instance_name}: {e}")
        return {'instance': instance_name, 'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("GCP Compute Engine — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires GCP credentials.

    # List all instances
    instances = list_instances('my-project', 'us-central1-a')
    for i in instances:
        print(f"  {i['name']}: {i['machine_type']} ({i['status']})")

    # Filter by label
    prod_instances = list_instances(
        'my-project', 'us-central1-a',
        label_filter={'environment': 'production'}
    )
    """)
