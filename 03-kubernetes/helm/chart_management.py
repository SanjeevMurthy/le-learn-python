"""
chart_management.py

Helm chart repository and chart lifecycle management.

Interview Topics:
- Chart repository management
- OCI-based chart registries
- Chart versioning and dependencies

Prerequisites:
- helm CLI installed
"""

import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _run_helm(args: List[str], json_output: bool = False) -> Dict[str, Any]:
    """Run a helm command."""
    cmd = ['helm'] + args
    if json_output:
        cmd.extend(['-o', 'json'])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return {'status': 'error', 'error': result.stderr.strip()}
        if json_output and result.stdout.strip():
            return {'status': 'ok', 'data': json.loads(result.stdout)}
        return {'status': 'ok', 'output': result.stdout.strip()}
    except FileNotFoundError:
        return {'status': 'error', 'error': 'helm CLI not found'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def add_repo(name: str, url: str) -> Dict[str, Any]:
    """
    Add a Helm chart repository.

    Interview Question:
        Q: What is the structure of a Helm chart?
        A: Chart.yaml: metadata (name, version, appVersion, deps)
           values.yaml: default configuration values
           templates/: K8s manifest templates (Go templates)
           charts/: dependency charts (subcharts)
           templates/NOTES.txt: post-install instructions
           templates/_helpers.tpl: reusable template snippets
           .helmignore: files to exclude from packaging
    """
    result = _run_helm(['repo', 'add', name, url])
    if result.get('status') != 'error':
        _run_helm(['repo', 'update'])
        logger.info(f"Added repo: {name} ({url})")
    return result


def search_charts(keyword: str, repo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for charts in added repositories."""
    args = ['search', 'repo', keyword]
    result = _run_helm(args, json_output=True)

    if result.get('status') == 'error':
        return []

    charts = result.get('data', [])
    logger.info(f"Found {len(charts)} charts matching '{keyword}'")
    return charts


def get_chart_values(chart: str, version: Optional[str] = None) -> str:
    """Get default values for a chart."""
    args = ['show', 'values', chart]
    if version:
        args.extend(['--version', version])

    result = _run_helm(args)
    return result.get('output', '')


def list_repos() -> List[Dict[str, Any]]:
    """List configured Helm repositories."""
    result = _run_helm(['repo', 'list'], json_output=True)
    if result.get('status') == 'error':
        return []
    return result.get('data', [])


def get_release_history(
    release_name: str,
    namespace: str = 'default',
    max_revisions: int = 10
) -> List[Dict[str, Any]]:
    """
    Get revision history for a Helm release.

    Interview Question:
        Q: How does Helm handle rollbacks?
        A: Each upgrade creates a new revision stored as a K8s Secret
           (type: helm.sh/release.v1). Rollback restores the manifest
           from a previous revision. Important: rollback creates a NEW
           revision (not going back). If at revision 3 and rollback to 1,
           you get revision 4 with content of revision 1.
           Max history controlled by --history-max flag.
    """
    args = ['history', release_name, '-n', namespace, '--max', str(max_revisions)]
    result = _run_helm(args, json_output=True)

    if result.get('status') == 'error':
        return []
    return result.get('data', [])


if __name__ == "__main__":
    print("=" * 60)
    print("Chart Management — Usage Examples")
    print("=" * 60)
    print("""
    # Add a repository
    add_repo('bitnami', 'https://charts.bitnami.com/bitnami')

    # Search for charts
    charts = search_charts('nginx')
    for c in charts:
        print(f"  {c.get('name')}: {c.get('app_version')}")

    # Get default values
    values = get_chart_values('bitnami/nginx')

    # Release history
    history = get_release_history('my-app', 'production')
    for h in history:
        print(f"  Rev {h.get('revision')}: {h.get('status')}")
    """)
