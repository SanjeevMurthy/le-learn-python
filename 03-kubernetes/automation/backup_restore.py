"""
backup_restore.py

Kubernetes resource backup and restore operations.

Interview Topics:
- etcd backup and restore
- Velero for cluster backup
- Disaster recovery strategies for K8s

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

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


def backup_namespace_resources(
    namespace: str,
    output_dir: str = '/tmp/k8s-backups',
    resource_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Export all resources from a namespace as JSON files.

    Interview Question:
        Q: How do you backup and restore a K8s cluster?
        A: Two levels:
           1. etcd backup: snapshot of all cluster state.
              ETCDCTL_API=3 etcdctl snapshot save backup.db
              Restores entire cluster state. Used for DR.
           2. Resource-level backup: export YAML/JSON per resource.
              Tools: Velero (snapshots + resource backup),
              custom scripts using kubectl/client-go.
              Velero also backs up PVs via CSI snapshots.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    backup_dir = os.path.join(output_dir, f"{namespace}-{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    types = resource_types or ['deployments', 'services', 'configmaps', 'secrets']
    backed_up = {}

    api_map = {
        'deployments': lambda: apps_v1.list_namespaced_deployment(namespace),
        'services': lambda: v1.list_namespaced_service(namespace),
        'configmaps': lambda: v1.list_namespaced_config_map(namespace),
        'secrets': lambda: v1.list_namespaced_secret(namespace),
    }

    for resource_type in types:
        if resource_type not in api_map:
            logger.warning(f"Unsupported resource type: {resource_type}")
            continue

        try:
            items = api_map[resource_type]()
            count = 0
            for item in items.items:
                # Clean metadata for restore
                clean = client.ApiClient().sanitize_for_serialization(item)
                if 'metadata' in clean:
                    for key in ['resourceVersion', 'uid', 'creationTimestamp',
                                'managedFields', 'selfLink']:
                        clean['metadata'].pop(key, None)

                filename = f"{resource_type}-{item.metadata.name}.json"
                filepath = os.path.join(backup_dir, filename)
                with open(filepath, 'w') as f:
                    json.dump(clean, f, indent=2, default=str)
                count += 1

            backed_up[resource_type] = count
            logger.info(f"Backed up {count} {resource_type}")

        except Exception as e:
            logger.error(f"Backup failed for {resource_type}: {e}")
            backed_up[resource_type] = f"error: {e}"

    return {
        'namespace': namespace,
        'backup_dir': backup_dir,
        'resources': backed_up,
        'timestamp': timestamp,
    }


def restore_from_backup(
    backup_dir: str,
    target_namespace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Restore resources from a backup directory.

    WARNING: This applies resources — use with caution.
    """
    from kubernetes import client, utils
    load_kube_config()
    k8s_client = client.ApiClient()

    restored = []
    errors = []

    if not os.path.isdir(backup_dir):
        return {'status': 'error', 'error': f"Directory not found: {backup_dir}"}

    for filename in sorted(os.listdir(backup_dir)):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(backup_dir, filename)
        with open(filepath, 'r') as f:
            resource = json.load(f)

        # Override namespace if specified
        if target_namespace and 'metadata' in resource:
            resource['metadata']['namespace'] = target_namespace

        try:
            utils.create_from_dict(k8s_client, resource)
            restored.append(filename)
        except Exception as e:
            errors.append({'file': filename, 'error': str(e)})

    return {
        'backup_dir': backup_dir,
        'restored': len(restored),
        'errors': errors,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Backup & Restore — Usage Examples")
    print("=" * 60)
    print("""
    # Backup a namespace
    result = backup_namespace_resources('production')
    print(f"  Backup saved to: {result['backup_dir']}")

    # Restore to a different namespace
    restore_from_backup(result['backup_dir'], target_namespace='staging')
    """)
