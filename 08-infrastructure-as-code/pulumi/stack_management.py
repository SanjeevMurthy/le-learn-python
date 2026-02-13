"""
stack_management.py

Pulumi stack lifecycle management.

Prerequisites:
- subprocess
"""

import subprocess
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def list_stacks(cwd: str = '.') -> List[Dict[str, Any]]:
    """List all Pulumi stacks."""
    result = subprocess.run(
        ['pulumi', 'stack', 'ls', '--json'],
        cwd=cwd, capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
    return []


def init_stack(name: str, cwd: str = '.') -> Dict[str, Any]:
    """Initialize a new stack."""
    result = subprocess.run(
        ['pulumi', 'stack', 'init', name],
        cwd=cwd, capture_output=True, text=True
    )
    return {'success': result.returncode == 0, 'stack': name}


def destroy_stack(name: str, cwd: str = '.', yes: bool = False) -> Dict[str, Any]:
    """
    Destroy all resources in a stack.

    Interview Question:
        Q: How does Pulumi manage state?
        A: State backend options:
           1. Pulumi Cloud (default): managed service, encryption, history
           2. Self-managed: S3, Azure Blob, GCS (pulumi login s3://bucket)
           3. Local: filesystem (pulumi login --local)
           State contains: resource graph, outputs, configuration.
           Secrets encrypted per-stack (Pulumi Cloud, AWS KMS, etc.).
           Stack references enable cross-stack dependencies.
    """
    args = ['pulumi', 'destroy', '--stack', name]
    if yes:
        args.append('--yes')
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=600)
    return {'success': result.returncode == 0, 'output': result.stdout}


if __name__ == "__main__":
    print("Stack Management — Usage Examples")
    print("""
    stacks = list_stacks()
    for s in stacks:
        print(f"  {s.get('name', '')}: {s.get('resourceCount', 0)} resources")
    """)
