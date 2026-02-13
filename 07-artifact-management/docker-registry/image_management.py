"""
image_management.py

Docker Registry v2 API for image management.

Interview Topics:
- Docker image layers and union filesystem
- Content-addressable storage
- Multi-architecture images (manifests)

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_auth():
    user = os.environ.get('REGISTRY_USER', '')
    passwd = os.environ.get('REGISTRY_PASSWORD', '')
    return HTTPBasicAuth(user, passwd) if user else None


def _get_base_url():
    return os.environ.get('REGISTRY_URL', 'http://localhost:5000')


def list_repositories() -> List[str]:
    """List all repositories in the registry."""
    url = f'{_get_base_url()}/v2/_catalog'
    response = requests.get(url, auth=_get_auth())
    response.raise_for_status()
    return response.json().get('repositories', [])


def list_tags(repository: str) -> List[str]:
    """
    List all tags for a repository.

    Interview Question:
        Q: How are Docker images stored internally?
        A: Image = manifest + config + layers.
           Manifest: JSON listing layer digests (content-addressable).
           Config: JSON with env vars, entrypoint, labels.
           Layers: tar.gz filesystem diffs (union filesystem).
           Content-addressable: sha256 digest = content hash.
           Multi-arch: manifest list points to platform-specific manifests.
           Sharing layers between images saves storage and pull time.
    """
    url = f'{_get_base_url()}/v2/{repository}/tags/list'
    response = requests.get(url, auth=_get_auth())
    response.raise_for_status()
    return response.json().get('tags', [])


def get_manifest(repository: str, tag: str) -> Dict[str, Any]:
    """Get image manifest."""
    url = f'{_get_base_url()}/v2/{repository}/manifests/{tag}'
    headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
    response = requests.get(url, auth=_get_auth(), headers=headers)
    response.raise_for_status()

    data = response.json()
    layers = data.get('layers', [])
    total_size = sum(l.get('size', 0) for l in layers)

    return {
        'schema_version': data.get('schemaVersion'),
        'media_type': data.get('mediaType', ''),
        'layer_count': len(layers),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'digest': response.headers.get('Docker-Content-Digest', ''),
    }


def delete_image(repository: str, digest: str) -> bool:
    """Delete an image by digest."""
    url = f'{_get_base_url()}/v2/{repository}/manifests/{digest}'
    response = requests.delete(url, auth=_get_auth())
    return response.status_code == 202


if __name__ == "__main__":
    print("Docker Image Management — Usage Examples")
    print("""
    repos = list_repositories()
    for repo in repos:
        tags = list_tags(repo)
        print(f"  {repo}: {len(tags)} tags")

    manifest = get_manifest('myapp', 'latest')
    print(f"  Layers: {manifest['layer_count']}, Size: {manifest['total_size_mb']}MB")
    """)
