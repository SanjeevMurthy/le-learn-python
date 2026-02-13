"""
playbook_runner.py

Ansible playbook execution wrapper.

Interview Topics:
- Ansible architecture (agentless, SSH-based)
- Idempotency in configuration management
- Roles, handlers, variables

Prerequisites:
- subprocess
"""

import subprocess
import json
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_playbook(
    playbook: str,
    inventory: str = 'inventory.yml',
    extra_vars: Optional[Dict[str, str]] = None,
    limit: str = '',
    tags: str = '',
    check: bool = False,
    verbose: int = 0
) -> Dict[str, Any]:
    """
    Run an Ansible playbook.

    Interview Question:
        Q: Ansible vs Terraform — when to use each?
        A: Terraform: infrastructure provisioning (create VMs, networks, DBs).
           Declarative, state-based, cloud-provider focused.
           Ansible: configuration management (install packages, configure services).
           Procedural, agentless (SSH), good for day-2 operations.
           Common pattern: Terraform provisions infra → Ansible configures it.
           Overlap: both can do some of each, but each excels in its domain.
    """
    cmd = ['ansible-playbook', playbook, '-i', inventory]

    if extra_vars:
        for k, v in extra_vars.items():
            cmd.extend(['-e', f'{k}={v}'])
    if limit:
        cmd.extend(['--limit', limit])
    if tags:
        cmd.extend(['--tags', tags])
    if check:
        cmd.append('--check')
    if verbose:
        cmd.append('-' + 'v' * min(verbose, 4))

    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

    return {
        'success': result.returncode == 0,
        'exit_code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'check_mode': check,
    }


def run_ad_hoc(
    pattern: str,
    module: str,
    args: str = '',
    inventory: str = 'inventory.yml'
) -> Dict[str, Any]:
    """Run an ad-hoc Ansible command."""
    cmd = ['ansible', pattern, '-i', inventory, '-m', module]
    if args:
        cmd.extend(['-a', args])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return {
        'success': result.returncode == 0,
        'output': result.stdout,
    }


if __name__ == "__main__":
    print("Playbook Runner — Usage Examples")
    print("""
    # Run a playbook (dry-run first)
    run_playbook('deploy.yml', check=True)
    run_playbook('deploy.yml', extra_vars={'version': '2.0'}, limit='webservers')

    # Ad-hoc command
    run_ad_hoc('all', 'ping')
    run_ad_hoc('webservers', 'shell', args='uptime')
    """)
