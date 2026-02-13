"""
pulumi_automation_api.py

Pulumi Automation API for programmatic IaC.

Interview Topics:
- Pulumi vs Terraform
- Automation API for embedding IaC in applications
- Stack references for cross-stack dependencies

Prerequisites:
- subprocess (for CLI wrapper)
"""

import subprocess
import json
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def preview_stack(
    cwd: str = '.', stack: str = 'dev'
) -> Dict[str, Any]:
    """
    Preview changes for a Pulumi stack.

    Interview Question:
        Q: What are the key differences between Pulumi and Terraform?
        A: Pulumi: real programming languages (Python, Go, TS, C#).
           Full language features: loops, conditionals, classes, testing.
           State: Pulumi Cloud, S3, or local.
           Terraform: HCL (domain-specific language).
           More mature ecosystem, larger community: more providers.
           Both: declarative desired state, plan/preview before apply.
           Choose Pulumi when: complex logic, existing language expertise.
           Choose Terraform when: large team, established workflows.
    """
    result = subprocess.run(
        ['pulumi', 'preview', '--stack', stack, '--json'],
        cwd=cwd, capture_output=True, text=True, timeout=300
    )

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return {
                'stack': stack,
                'changes': data.get('changeSummary', {}),
                'status': 'ok',
            }
        except json.JSONDecodeError:
            return {'status': 'ok', 'raw': result.stdout}
    return {'status': 'error', 'stderr': result.stderr}


def deploy_stack(
    cwd: str = '.', stack: str = 'dev', yes: bool = False
) -> Dict[str, Any]:
    """Deploy a Pulumi stack."""
    args = ['pulumi', 'up', '--stack', stack]
    if yes:
        args.append('--yes')

    result = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=600
    )
    return {
        'success': result.returncode == 0,
        'output': result.stdout,
        'stderr': result.stderr,
    }


def get_stack_outputs(cwd: str = '.', stack: str = 'dev') -> Dict[str, Any]:
    """Get stack outputs."""
    result = subprocess.run(
        ['pulumi', 'stack', 'output', '--stack', stack, '--json'],
        cwd=cwd, capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}
    return {}


if __name__ == "__main__":
    print("Pulumi Automation API — Usage Examples")
    print("""
    preview = preview_stack('/path/to/project', 'staging')
    deploy_stack('/path/to/project', 'staging', yes=True)
    outputs = get_stack_outputs('/path/to/project', 'staging')
    """)
