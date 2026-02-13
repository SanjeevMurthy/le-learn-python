"""
inventory_management.py

Ansible inventory parsing and management.

Prerequisites:
- Standard library (json, yaml)
"""

import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_ini_inventory(filepath: str) -> Dict[str, List[str]]:
    """
    Parse an INI-format Ansible inventory.

    Interview Question:
        Q: What is Ansible idempotency?
        A: Running the same playbook multiple times produces the same result.
           Modules check current state before acting.
           Example: `apt: name=nginx state=present` only installs if missing.
           `copy: src=app.conf dest=/etc/app.conf` only copies if different.
           Handlers: run only when notified (e.g., restart nginx if config changed).
           Non-idempotent modules: `shell`, `command`, `raw` — use `creates`
           or `when` conditions to make them idempotent.
    """
    groups: Dict[str, List[str]] = {}
    current_group = 'ungrouped'
    groups[current_group] = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            if line.startswith('[') and line.endswith(']'):
                current_group = line[1:-1].split(':')[0]  # Handle [group:vars]
                if current_group not in groups:
                    groups[current_group] = []
            else:
                hostname = line.split()[0]
                groups[current_group].append(hostname)

    return groups


def generate_inventory(
    hosts: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate a JSON inventory for Ansible."""
    inventory: Dict[str, Any] = {'_meta': {'hostvars': {}}}

    for hostname, config in hosts.items():
        group = config.get('group', 'ungrouped')
        if group not in inventory:
            inventory[group] = {'hosts': [], 'vars': {}}
        inventory[group]['hosts'].append(hostname)

        # Add host variables
        host_vars = {k: v for k, v in config.items() if k != 'group'}
        if host_vars:
            inventory['_meta']['hostvars'][hostname] = host_vars

    return inventory


if __name__ == "__main__":
    print("Inventory Management — Usage Examples")
    print("""
    # Parse INI inventory
    groups = parse_ini_inventory('/path/to/hosts')
    for group, hosts in groups.items():
        print(f"  [{group}]: {hosts}")

    # Generate JSON inventory
    inventory = generate_inventory({
        'web-01': {'group': 'webservers', 'ansible_host': '10.0.1.1'},
        'db-01': {'group': 'databases', 'ansible_host': '10.0.2.1'},
    })
    """)
