"""
artifact_cleanup.py

Automated artifact cleanup and retention policies.

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
    return HTTPBasicAuth(
        os.environ.get('ARTIFACTORY_USER', 'admin'),
        os.environ.get('ARTIFACTORY_TOKEN', '')
    )


def _get_base_url():
    return os.environ.get('ARTIFACTORY_URL', 'http://localhost:8082/artifactory')


def find_old_artifacts(
    repo: str,
    older_than_days: int = 90,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Find artifacts older than a threshold using AQL.

    Interview Question:
        Q: What's a good artifact retention policy?
        A: 1. Release artifacts: keep N latest versions per project
           2. Snapshot/dev: expire after 30-90 days
           3. Docker tags: keep tagged releases, delete untagged after 7 days
           4. Never delete artifacts referenced by production deployments
           5. Use AQL (Artifactory Query Language) for complex searches
           6. Implement cleanup as a scheduled job, never manual
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    cutoff_str = cutoff.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    aql = f"""items.find({{
        "repo": "{repo}",
        "created": {{"$lt": "{cutoff_str}"}}
    }}).include("repo","path","name","size","created").sort({{"$asc":["created"]}}).limit({limit})"""

    url = f'{_get_base_url()}/api/search/aql'
    response = requests.post(url, auth=_get_auth(), data=aql,
                             headers={'Content-Type': 'text/plain'})

    if response.status_code == 200:
        results = response.json().get('results', [])
        return [
            {'repo': r['repo'], 'path': f"{r['path']}/{r['name']}",
             'size': r.get('size', 0), 'created': r.get('created', '')}
            for r in results
        ]
    return []


def delete_artifacts(artifacts: List[Dict[str, str]], dry_run: bool = True) -> Dict[str, Any]:
    """Delete artifacts (with dry-run support)."""
    deleted = 0
    errors = 0

    for a in artifacts:
        if dry_run:
            logger.info(f"[DRY RUN] Would delete: {a['repo']}/{a['path']}")
            deleted += 1
            continue

        url = f"{_get_base_url()}/{a['repo']}/{a['path']}"
        response = requests.delete(url, auth=_get_auth())
        if response.status_code == 204:
            deleted += 1
        else:
            errors += 1

    return {'deleted': deleted, 'errors': errors, 'dry_run': dry_run}


if __name__ == "__main__":
    print("Artifact Cleanup — Usage Examples")
    print("""
    old = find_old_artifacts('libs-snapshot-local', older_than_days=90)
    print(f"  Found {len(old)} old artifacts")

    result = delete_artifacts(old, dry_run=True)
    print(f"  Would delete: {result['deleted']}")
    """)
