"""
dynamic_inventory.py

Ansible dynamic inventory scripts for cloud providers.

Prerequisites:
- boto3 (pip install boto3)
"""

import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def aws_ec2_inventory(
    region: str = 'us-east-1',
    filters: dict = None
) -> Dict[str, Any]:
    """
    Generate dynamic inventory from AWS EC2 instances.

    Interview Question:
        Q: What is a dynamic inventory and when do you use it?
        A: Static inventory: hardcoded hosts in a file.
           Dynamic inventory: script that queries cloud API for hosts.
           Use when: auto-scaling groups, ephemeral infrastructure,
           multi-cloud, frequently changing hosts.
           Ansible calls the script with --list (all hosts) or
           --host <hostname> (host vars).
           aws_ec2 plugin: built-in, uses boto3, supports keyed_groups
           to auto-create groups from tags/instance attributes.
    """
    try:
        import boto3
    except ImportError:
        return {'_meta': {'hostvars': {}}}

    ec2 = boto3.client('ec2', region_name=region)
    kwargs = {'Filters': filters} if filters else {}
    kwargs.setdefault('Filters', []).append({
        'Name': 'instance-state-name',
        'Values': ['running']
    })

    response = ec2.describe_instances(**kwargs)

    inventory: Dict[str, Any] = {'_meta': {'hostvars': {}}}

    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instance_id = instance['InstanceId']
            ip = instance.get('PrivateIpAddress', instance.get('PublicIpAddress', ''))
            if not ip:
                continue

            # Group by tags
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            group = tags.get('Environment', tags.get('Role', 'ungrouped'))

            if group not in inventory:
                inventory[group] = {'hosts': [], 'vars': {}}
            inventory[group]['hosts'].append(ip)

            inventory['_meta']['hostvars'][ip] = {
                'instance_id': instance_id,
                'instance_type': instance.get('InstanceType', ''),
                'region': region,
                'tags': tags,
            }

    return inventory


if __name__ == "__main__":
    # Dynamic inventory must output JSON when called with --list
    import sys
    if '--list' in sys.argv:
        print(json.dumps(aws_ec2_inventory(), indent=2))
    elif '--host' in sys.argv:
        print(json.dumps({}))
    else:
        print("Dynamic Inventory — Usage Examples")
        print("""
        # As an Ansible inventory script:
        ansible-playbook -i dynamic_inventory.py playbook.yml

        # Or generate and inspect:
        inventory = aws_ec2_inventory(region='us-east-1')
        print(json.dumps(inventory, indent=2))
        """)
