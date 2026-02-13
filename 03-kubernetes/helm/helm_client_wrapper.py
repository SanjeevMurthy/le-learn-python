"""
helm_client_wrapper.py

Python wrapper for Helm CLI operations.

Interview Topics:
- Helm architecture (v3 — no Tiller)
- Chart structure: templates, values, Chart.yaml
- Helm hooks and test framework

Production Use Cases:
- Programmatic chart installation and upgrades
- Release management across environments
- Helm release inventory

Prerequisites:
- helm CLI installed (brew install helm / snap install helm)
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


def _run_helm(args: List[str], json_output: bool = True) -> Dict[str, Any]:
    """
    Run a helm command and return parsed output.

    Interview Question:
        Q: How does Helm v3 differ from v2?
        A: v2: client/server (Tiller), Tiller had cluster-admin,
           security concerns, release state in ConfigMaps.
           v3: client-only, uses kubeconfig RBAC, release state
           in Secrets, supports OCI registries, improved upgrade
           strategy, 3-way strategic merge patch, JSON Schema
           validation for values.yaml.
    """
    cmd = ['helm'] + args
    if json_output:
        cmd.append('-o')
        cmd.append('json')

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return {'status': 'error', 'error': result.stderr.strip()}

        if json_output and result.stdout.strip():
            return {'status': 'ok', 'data': json.loads(result.stdout)}
        return {'status': 'ok', 'output': result.stdout.strip()}

    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Command timed out'}
    except json.JSONDecodeError:
        return {'status': 'ok', 'output': result.stdout.strip()}
    except FileNotFoundError:
        return {'status': 'error', 'error': 'helm CLI not found'}


def list_releases(namespace: str = '', all_namespaces: bool = False) -> List[Dict[str, Any]]:
    """List Helm releases."""
    args = ['list']
    if all_namespaces:
        args.append('--all-namespaces')
    elif namespace:
        args.extend(['-n', namespace])

    result = _run_helm(args)
    if result.get('status') == 'error':
        logger.error(f"Helm list failed: {result['error']}")
        return []

    releases = result.get('data', [])
    logger.info(f"Found {len(releases)} Helm releases")
    return releases


def install_release(
    release_name: str,
    chart: str,
    namespace: str = 'default',
    values: Optional[Dict[str, Any]] = None,
    values_file: Optional[str] = None,
    create_namespace: bool = True,
    wait: bool = True,
    timeout: str = '5m0s'
) -> Dict[str, Any]:
    """
    Install a Helm chart.

    Interview Question:
        Q: Explain the Helm release lifecycle.
        A: install → creates release (revision 1)
           upgrade → new revision with updated values/chart
           rollback → reverts to previous revision
           uninstall → removes release and all resources
           Each revision stored as a K8s Secret.
           Use --atomic for auto-rollback on failed install/upgrade.
    """
    args = ['install', release_name, chart, '-n', namespace]
    if create_namespace:
        args.append('--create-namespace')
    if wait:
        args.append('--wait')
    args.extend(['--timeout', timeout])
    if values_file:
        args.extend(['-f', values_file])

    result = _run_helm(args, json_output=False)
    if result.get('status') == 'error':
        logger.error(f"Install failed: {result['error']}")
    else:
        logger.info(f"Installed {release_name} from {chart}")
    return result


def upgrade_release(
    release_name: str,
    chart: str,
    namespace: str = 'default',
    values_file: Optional[str] = None,
    atomic: bool = True
) -> Dict[str, Any]:
    """Upgrade a Helm release (with optional atomic rollback)."""
    args = ['upgrade', release_name, chart, '-n', namespace]
    if atomic:
        args.append('--atomic')
    if values_file:
        args.extend(['-f', values_file])

    result = _run_helm(args, json_output=False)
    if result.get('status') == 'error':
        logger.error(f"Upgrade failed: {result['error']}")
    else:
        logger.info(f"Upgraded {release_name}")
    return result


def rollback_release(
    release_name: str,
    revision: int = 0,
    namespace: str = 'default'
) -> Dict[str, Any]:
    """Rollback a Helm release (0 = previous revision)."""
    args = ['rollback', release_name, str(revision), '-n', namespace]
    result = _run_helm(args, json_output=False)
    logger.info(f"Rolled back {release_name} to revision {revision}")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Helm Client Wrapper — Usage Examples")
    print("=" * 60)
    print("""
    # List all releases
    releases = list_releases(all_namespaces=True)
    for r in releases:
        print(f"  {r.get('name')}: {r.get('chart')} ({r.get('status')})")

    # Install a chart
    install_release('my-app', 'bitnami/nginx', namespace='web')

    # Upgrade with atomic rollback
    upgrade_release('my-app', 'bitnami/nginx', atomic=True)
    """)
