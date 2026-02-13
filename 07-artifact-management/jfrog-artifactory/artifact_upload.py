"""
artifact_upload.py

Upload artifacts to JFrog Artifactory via REST API.

Interview Topics:
- Artifact promotion pipelines
- Checksum-based deduplication
- Repository types (local, remote, virtual)

Prerequisites:
- requests (pip install requests)
"""

import os
import hashlib
import logging
from typing import Dict, Any, Optional

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_auth():
    return HTTPBasicAuth(
        os.environ.get('ARTIFACTORY_USER', 'admin'),
        os.environ.get('ARTIFACTORY_TOKEN', '')
    )


def _get_base_url():
    return os.environ.get('ARTIFACTORY_URL', 'http://localhost:8082/artifactory')


def upload_artifact(
    repo: str,
    path: str,
    filepath: str,
    properties: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload an artifact with checksum verification.

    Interview Question:
        Q: What are the types of Artifactory repositories?
        A: Local: primary storage, you upload artifacts here.
           Remote: proxy/cache for external repos (Maven Central, npm).
           Virtual: aggregates local + remote repos into single URL.
           Federated: replicate across Artifactory instances (multi-site).
           Best practice: separate repos per package type and maturity
           (e.g., libs-snapshot-local, libs-release-local).
    """
    # Calculate checksums
    with open(filepath, 'rb') as f:
        data = f.read()
    sha256 = hashlib.sha256(data).hexdigest()
    md5 = hashlib.md5(data).hexdigest()

    url = f'{_get_base_url()}/{repo}/{path}'
    headers = {
        'X-Checksum-Sha256': sha256,
        'X-Checksum-Md5': md5,
    }

    # Add properties as matrix parameters
    if properties:
        props = ';'.join(f'{k}={v}' for k, v in properties.items())
        url += f';{props}'

    response = requests.put(url, auth=_get_auth(), headers=headers, data=data)

    if response.status_code in (200, 201):
        logger.info(f"Uploaded: {repo}/{path} ({len(data)} bytes)")
        return {'path': f'{repo}/{path}', 'sha256': sha256, 'size': len(data), 'status': 'ok'}
    return {'status': 'error', 'code': response.status_code, 'body': response.text}


def deploy_with_checksum(
    repo: str, path: str, sha256: str
) -> Dict[str, Any]:
    """Deploy artifact by checksum (no upload if already exists)."""
    url = f'{_get_base_url()}/{repo}/{path}'
    headers = {'X-Checksum-Deploy': 'true', 'X-Checksum-Sha256': sha256}

    response = requests.put(url, auth=_get_auth(), headers=headers)
    if response.status_code in (200, 201):
        logger.info(f"Checksum-deployed: {repo}/{path}")
        return {'status': 'ok', 'method': 'checksum-deploy'}
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("Artifact Upload — Usage Examples")
    print("""
    upload_artifact('libs-release', 'com/myapp/1.0/myapp-1.0.jar', '/path/to/myapp.jar',
                    properties={'build.number': '42'})
    """)
