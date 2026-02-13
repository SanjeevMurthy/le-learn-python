"""
registry_cleanup.py

Docker registry garbage collection and tag cleanup.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

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


def find_untagged_manifests(repository: str) -> List[str]:
    """
    Find dangling (untagged) manifests.

    Interview Question:
        Q: How does Docker registry garbage collection work?
        A: Two-phase process:
           1. Mark: identify unreferenced blobs (layers not pointed to
              by any manifest)
           2. Sweep: delete unreferenced blobs from storage
           Run with `registry garbage-collect /etc/docker/registry/config.yml`.
           Must run with registry in read-only mode or stopped.
           Deleting a tag only removes the tag → manifest link.
           Blob storage is reclaimed only after GC.
    """
    url = f'{_get_base_url()}/v2/{repository}/tags/list'
    response = requests.get(url, auth=_get_auth())
    if response.status_code != 200:
        return []

    tags = response.json().get('tags', []) or []
    # In production, compare manifests against tagged manifests
    # to find orphans. Simplified here.
    logger.info(f"Repository {repository} has {len(tags)} tags")
    return []


def cleanup_old_tags(
    repository: str,
    keep_latest: int = 10,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Remove old tags, keeping the N most recent."""
    url = f'{_get_base_url()}/v2/{repository}/tags/list'
    response = requests.get(url, auth=_get_auth())
    if response.status_code != 200:
        return {'status': 'error', 'code': response.status_code}

    tags = response.json().get('tags', []) or []
    if len(tags) <= keep_latest:
        return {'status': 'ok', 'deleted': 0, 'message': 'Nothing to clean'}

    to_delete = tags[:-keep_latest]  # Keep the latest N
    deleted = 0

    for tag in to_delete:
        if dry_run:
            logger.info(f"[DRY RUN] Would delete {repository}:{tag}")
            deleted += 1
        else:
            # Get digest then delete
            manifest_url = f'{_get_base_url()}/v2/{repository}/manifests/{tag}'
            headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
            resp = requests.get(manifest_url, auth=_get_auth(), headers=headers)
            if resp.status_code == 200:
                digest = resp.headers.get('Docker-Content-Digest', '')
                if digest:
                    del_resp = requests.delete(
                        f'{_get_base_url()}/v2/{repository}/manifests/{digest}',
                        auth=_get_auth()
                    )
                    if del_resp.status_code == 202:
                        deleted += 1

    return {'status': 'ok', 'deleted': deleted, 'total_tags': len(tags), 'dry_run': dry_run}


if __name__ == "__main__":
    print("Registry Cleanup — Usage Examples")
    print("""
    result = cleanup_old_tags('myapp', keep_latest=10, dry_run=True)
    print(f"  Would delete {result['deleted']} of {result['total_tags']} tags")
    """)
