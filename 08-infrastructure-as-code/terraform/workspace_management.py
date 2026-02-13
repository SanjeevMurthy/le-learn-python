"""
workspace_management.py

Terraform workspace management for multi-environment deployments.

Prerequisites:
- subprocess
"""

import subprocess
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def list_workspaces(cwd: str = '.') -> Dict[str, Any]:
    """
    List Terraform workspaces.

    Interview Question:
        Q: Terraform workspaces vs separate state files?
        A: Workspaces: same config, separate state per workspace.
           Good for: dev/staging/prod with same structure.
           Limitation: all envs share the same config and providers.
           Alternative: separate directories per env with shared modules.
           Better for: significantly different environments.
           Terragrunt: DRY wrapper for multi-env Terraform.
    """
    result = subprocess.run(
        ['terraform', 'workspace', 'list'],
        cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        return {'workspaces': [], 'current': ''}

    workspaces = []
    current = ''
    for line in result.stdout.strip().split('\n'):
        name = line.strip()
        if name.startswith('* '):
            current = name[2:]
            workspaces.append(current)
        elif name:
            workspaces.append(name)

    return {'workspaces': workspaces, 'current': current}


def select_workspace(name: str, cwd: str = '.') -> Dict[str, Any]:
    """Switch to an existing workspace."""
    result = subprocess.run(
        ['terraform', 'workspace', 'select', name],
        cwd=cwd, capture_output=True, text=True
    )
    return {'success': result.returncode == 0, 'workspace': name}


def create_workspace(name: str, cwd: str = '.') -> Dict[str, Any]:
    """Create and switch to a new workspace."""
    result = subprocess.run(
        ['terraform', 'workspace', 'new', name],
        cwd=cwd, capture_output=True, text=True
    )
    return {'success': result.returncode == 0, 'workspace': name}


if __name__ == "__main__":
    print("Workspace Management — Usage Examples")
    print("""
    info = list_workspaces('/path/to/infra')
    print(f"  Current: {info['current']}, All: {info['workspaces']}")

    select_workspace('staging')
    create_workspace('feature-xyz')
    """)
