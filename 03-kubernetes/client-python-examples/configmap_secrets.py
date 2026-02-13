"""
configmap_secrets.py

Kubernetes ConfigMap and Secret management.

Interview Topics:
- ConfigMap vs Secret differences and use cases
- Secret types and encryption at rest
- Mounting configs as volumes vs env vars

Prerequisites:
- kubernetes (pip install kubernetes)
"""

import base64
import logging
from typing import Dict, Any, Optional

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


def create_configmap(
    name: str,
    data: Dict[str, str],
    namespace: str = 'default'
) -> Dict[str, Any]:
    """
    Create a ConfigMap from key-value data.

    Interview Question:
        Q: ConfigMap vs Secret — when to use which?
        A: ConfigMap: non-sensitive config (feature flags, URLs, settings).
           Stored in plain text in etcd.
           Secret: sensitive data (passwords, API keys, TLS certs).
           Base64 encoded (NOT encrypted by default). Enable etcd
           encryption at rest for real security. Both can be mounted
           as volumes or injected as env vars.
           Use ConfigMap for config, Secret for credentials.
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=name),
        data=data,
    )

    try:
        v1.create_namespaced_config_map(namespace, configmap)
        logger.info(f"Created ConfigMap: {name}")
        return {'name': name, 'keys': list(data.keys()), 'status': 'created'}
    except Exception as e:
        logger.error(f"Failed to create ConfigMap: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def create_secret(
    name: str,
    data: Dict[str, str],
    namespace: str = 'default',
    secret_type: str = 'Opaque'
) -> Dict[str, Any]:
    """
    Create a K8s Secret (values auto base64-encoded).

    Interview Question:
        Q: How are secrets secured in K8s?
        A: By default, base64 encoded in etcd (NOT secure).
           To secure: 1. Enable encryption at rest (EncryptionConfiguration)
           2. Use KMS provider (AWS KMS, GCP KMS, Azure Key Vault)
           3. Limit RBAC access to secrets
           4. Use external secret managers (Vault, AWS SM) with operators
           5. Consider Sealed Secrets for GitOps workflows
    """
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    # Encode values to base64
    encoded_data = {
        k: base64.b64encode(v.encode()).decode()
        for k, v in data.items()
    }

    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=name),
        type=secret_type,
        data=encoded_data,
    )

    try:
        v1.create_namespaced_secret(namespace, secret)
        logger.info(f"Created Secret: {name}")
        return {'name': name, 'keys': list(data.keys()), 'status': 'created'}
    except Exception as e:
        logger.error(f"Failed to create Secret: {e}")
        return {'name': name, 'status': 'error', 'error': str(e)}


def get_configmap(name: str, namespace: str = 'default') -> Dict[str, Any]:
    """Read a ConfigMap's data."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        cm = v1.read_namespaced_config_map(name, namespace)
        return {'name': name, 'data': dict(cm.data or {}), 'status': 'found'}
    except Exception as e:
        return {'name': name, 'status': 'error', 'error': str(e)}


def get_secret(name: str, namespace: str = 'default', decode: bool = True) -> Dict[str, Any]:
    """Read a Secret's data, optionally decoding base64 values."""
    from kubernetes import client
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        secret = v1.read_namespaced_secret(name, namespace)
        data = {}
        for k, v in (secret.data or {}).items():
            data[k] = base64.b64decode(v).decode() if decode else v
        return {'name': name, 'data': data, 'type': secret.type, 'status': 'found'}
    except Exception as e:
        return {'name': name, 'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("ConfigMap & Secrets — Usage Examples")
    print("=" * 60)
    print("""
    # Create ConfigMap
    create_configmap('app-config', {
        'DATABASE_URL': 'postgres://db:5432/myapp',
        'LOG_LEVEL': 'INFO',
    })

    # Create Secret
    create_secret('db-credentials', {
        'username': 'admin',
        'password': 'supersecret',
    })

    # Read with decoding
    secret = get_secret('db-credentials')
    print(f"  Username: {secret['data']['username']}")
    """)
