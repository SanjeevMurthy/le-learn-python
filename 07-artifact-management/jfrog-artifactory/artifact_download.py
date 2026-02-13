"""
artifact_download.py

Download artifacts from JFrog Artifactory.

Prerequisites:
- requests (pip install requests)
"""

import os
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


def download_artifact(
    repo: str, path: str, output_dir: str = '/tmp'
) -> Dict[str, Any]:
    """Download an artifact to local filesystem."""
    url = f'{_get_base_url()}/{repo}/{path}'
    response = requests.get(url, auth=_get_auth(), stream=True)

    if response.status_code == 200:
        filename = path.split('/')[-1]
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded: {output_path}")
        return {'path': output_path, 'status': 'ok'}
    return {'status': 'error', 'code': response.status_code}


def get_artifact_info(repo: str, path: str) -> Dict[str, Any]:
    """
    Get artifact metadata (size, checksums, properties).

    Interview Question:
        Q: What is artifact promotion and why is it important?
        A: Promotion moves artifacts between repos (snapshot → staging → release)
           without re-uploading. The same binary is promoted after passing
           quality gates. Ensures the exact artifact tested is deployed.
           Never rebuild for production — build once, promote everywhere.
    """
    url = f'{_get_base_url()}/api/storage/{repo}/{path}'
    response = requests.get(url, auth=_get_auth())

    if response.status_code == 200:
        data = response.json()
        return {
            'path': data.get('path', ''),
            'size': data.get('size', ''),
            'created': data.get('created', ''),
            'checksums': data.get('checksums', {}),
            'status': 'ok',
        }
    return {'status': 'error', 'code': response.status_code}


if __name__ == "__main__":
    print("Artifact Download — Usage Examples")
    print("""
    info = get_artifact_info('libs-release', 'com/myapp/1.0/myapp-1.0.jar')
    print(f"  Size: {info['size']}, SHA256: {info['checksums'].get('sha256')}")

    download_artifact('libs-release', 'com/myapp/1.0/myapp-1.0.jar')
    """)
