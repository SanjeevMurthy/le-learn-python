"""
security_group_analysis.py

AWS Security Group analysis for identifying risky ingress/egress rules.

Interview Topics:
- Security group best practices
- Identifying overly permissive rules
- Network segmentation in VPCs

Production Use Cases:
- Compliance scanning for open ports
- Detecting 0.0.0.0/0 ingress rules
- Automated remediation of risky rules

Prerequisites:
- boto3 (pip install boto3)
"""

import os
import logging
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RISKY_PORTS = {
    22: 'SSH', 3389: 'RDP', 3306: 'MySQL', 5432: 'PostgreSQL',
    27017: 'MongoDB', 6379: 'Redis', 9200: 'Elasticsearch',
}


def get_ec2_client(region: str = None):
    import boto3
    return boto3.client(
        'ec2',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def analyze_security_groups(region: str = None) -> List[Dict[str, Any]]:
    """
    Analyze all security groups for risky ingress rules.

    Checks for rules open to 0.0.0.0/0 or ::/0 on sensitive ports.

    Interview Question:
        Q: How would you design a security group audit system?
        A: 1. Enumerate all SGs across all regions
           2. Check each rule against policy (allowed ports, CIDR ranges)
           3. Classify findings by severity
           4. Auto-remediate critical findings
           5. Report via Slack/email with remediation guidance
    """
    ec2 = get_ec2_client(region)
    findings = []

    for page in ec2.get_paginator('describe_security_groups').paginate():
        for sg in page['SecurityGroups']:
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            vpc_id = sg.get('VpcId', 'N/A')

            for rule in sg.get('IpPermissions', []):
                protocol = rule.get('IpProtocol', 'N/A')
                from_port = rule.get('FromPort', 0)
                to_port = rule.get('ToPort', 65535)

                for ip_range in rule.get('IpRanges', []):
                    cidr = ip_range.get('CidrIp', '')
                    if cidr == '0.0.0.0/0':
                        findings.append(_classify(
                            sg_id, sg_name, vpc_id, protocol,
                            from_port, to_port, cidr
                        ))

    findings.sort(key=lambda f: {'critical': 0, 'high': 1, 'medium': 2}.get(f['severity'], 9))
    logger.info(f"Found {len(findings)} risky security group rules")
    return findings


def _classify(sg_id, sg_name, vpc_id, protocol, from_port, to_port, cidr):
    """Classify a finding by severity."""
    if protocol == '-1':
        return {
            'sg_id': sg_id, 'sg_name': sg_name, 'vpc_id': vpc_id,
            'severity': 'critical', 'rule': f'ALL traffic from {cidr}',
            'recommendation': 'Remove rule. Never allow all traffic from internet.',
        }

    risky = [(p, n) for p, n in RISKY_PORTS.items() if from_port <= p <= to_port]
    if risky:
        names = ', '.join(f"{n}({p})" for p, n in risky)
        sev = 'critical' if any(p in (3306, 5432, 27017, 6379) for p, _ in risky) else 'high'
        return {
            'sg_id': sg_id, 'sg_name': sg_name, 'vpc_id': vpc_id,
            'severity': sev, 'rule': f'{names} from {cidr}',
            'recommendation': f'Restrict {names} to specific IPs.',
        }

    return {
        'sg_id': sg_id, 'sg_name': sg_name, 'vpc_id': vpc_id,
        'severity': 'medium', 'rule': f'Ports {from_port}-{to_port} from {cidr}',
        'recommendation': 'Review if public access is required.',
    }


def find_unused_security_groups(region: str = None) -> List[Dict[str, Any]]:
    """Find security groups not attached to any network interface."""
    ec2 = get_ec2_client(region)

    all_sgs = set()
    for page in ec2.get_paginator('describe_security_groups').paginate():
        for sg in page['SecurityGroups']:
            if sg['GroupName'] != 'default':
                all_sgs.add(sg['GroupId'])

    used_sgs = set()
    for page in ec2.get_paginator('describe_network_interfaces').paginate():
        for ni in page['NetworkInterfaces']:
            for group in ni['Groups']:
                used_sgs.add(group['GroupId'])

    unused = all_sgs - used_sgs
    unused_details = []
    if unused:
        resp = ec2.describe_security_groups(GroupIds=list(unused))
        for sg in resp['SecurityGroups']:
            unused_details.append({
                'sg_id': sg['GroupId'], 'sg_name': sg['GroupName'],
                'vpc_id': sg.get('VpcId', 'N/A'),
            })

    logger.info(f"Found {len(unused_details)} unused security groups")
    return unused_details


if __name__ == "__main__":
    print("=" * 60)
    print("Security Group Analysis — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials with EC2 read access.

    # Analyze all security groups
    findings = analyze_security_groups()
    for f in findings:
        print(f"  [{f['severity']}] {f['sg_name']}: {f['rule']}")

    # Find unused security groups
    unused = find_unused_security_groups()
    """)
