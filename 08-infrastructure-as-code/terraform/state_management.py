"""
state_management.py

Terraform state management operations.

Prerequisites:
- subprocess
"""

import subprocess
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def list_state_resources(cwd: str = '.') -> List[str]:
    """
    List all resources in Terraform state.

    Interview Question:
        Q: What is Terraform state and why is it important?
        A: State is a JSON file mapping config resources to real-world IDs.
           Without state, Terraform can't know what exists. Remote backends
           (S3, GCS, Terraform Cloud) enable team collaboration.
           State locking prevents concurrent modifications.
           State contains sensitive data → encrypt at rest.
           Never edit state manually — use `terraform state` commands.
    """
    result = subprocess.run(
        ['terraform', 'state', 'list'],
        cwd=cwd, capture_output=True, text=True
    )
    if result.returncode == 0:
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    return []


def show_resource(resource_addr: str, cwd: str = '.') -> Dict[str, Any]:
    """Show details of a resource in state."""
    result = subprocess.run(
        ['terraform', 'state', 'show', '-json', resource_addr],
        cwd=cwd, capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {'raw': result.stdout}
    return {'error': result.stderr}


def move_resource(from_addr: str, to_addr: str, cwd: str = '.') -> Dict[str, Any]:
    """Rename a resource in state (refactoring without destroy/recreate)."""
    result = subprocess.run(
        ['terraform', 'state', 'mv', from_addr, to_addr],
        cwd=cwd, capture_output=True, text=True
    )
    return {'success': result.returncode == 0, 'output': result.stdout or result.stderr}


def import_resource(resource_addr: str, resource_id: str, cwd: str = '.') -> Dict[str, Any]:
    """Import an existing resource into Terraform state."""
    result = subprocess.run(
        ['terraform', 'import', resource_addr, resource_id],
        cwd=cwd, capture_output=True, text=True
    )
    return {'success': result.returncode == 0, 'output': result.stdout or result.stderr}


if __name__ == "__main__":
    print("State Management — Usage Examples")
    print("""
    resources = list_state_resources('/path/to/infra')
    for r in resources:
        print(f"  {r}")

    # Refactor: rename a resource
    move_resource('aws_instance.old_name', 'aws_instance.new_name')

    # Import existing infra
    import_resource('aws_instance.web', 'i-1234567890abcdef0')
    """)
