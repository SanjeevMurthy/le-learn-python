"""
iam_audit.py

AWS IAM security audit — identify risky users, roles, and policies.

Interview Topics:
- Principle of least privilege
- IAM best practices for security
- Automated compliance auditing

Production Use Cases:
- Audit for users without MFA enabled
- Find overly permissive policies (e.g., admin access)
- Detect stale access keys and unused credentials
- Compliance reporting for SOC2/ISO27001

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials with IAM read access
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_iam_client():
    """Create a boto3 IAM client (global service, no region needed)."""
    import boto3
    return boto3.client('iam')


def audit_mfa_status() -> Dict[str, Any]:
    """
    Check which IAM users have MFA enabled.

    MFA is a critical security control. All console users should
    have MFA enabled — this is a common compliance requirement.

    Returns:
        Audit results with users missing MFA

    Interview Question:
        Q: What are the top IAM security best practices?
        A: 1. Enable MFA for all users (especially root)
           2. Use IAM roles for applications (not access keys)
           3. Apply least-privilege policies
           4. Rotate access keys regularly (< 90 days)
           5. Use AWS Organizations SCPs for guardrails
           6. Enable CloudTrail for audit logging
           7. Use IAM Access Analyzer for external access detection
    """
    iam = get_iam_client()

    users_without_mfa = []
    users_with_mfa = []

    paginator = iam.get_paginator('list_users')
    for page in paginator.paginate():
        for user in page['Users']:
            username = user['UserName']

            # Check if user has MFA devices
            mfa_response = iam.list_mfa_devices(UserName=username)
            has_mfa = len(mfa_response['MFADevices']) > 0

            user_info = {
                'username': username,
                'has_mfa': has_mfa,
                'created': user['CreateDate'].isoformat(),
                'password_last_used': (
                    user['PasswordLastUsed'].isoformat()
                    if 'PasswordLastUsed' in user else 'Never'
                ),
            }

            if has_mfa:
                users_with_mfa.append(user_info)
            else:
                users_without_mfa.append(user_info)

    total = len(users_with_mfa) + len(users_without_mfa)
    logger.info(
        f"MFA audit: {len(users_with_mfa)}/{total} users have MFA enabled"
    )

    return {
        'total_users': total,
        'mfa_enabled': len(users_with_mfa),
        'mfa_disabled': len(users_without_mfa),
        'compliance_percentage': round(
            len(users_with_mfa) / total * 100, 1
        ) if total > 0 else 100,
        'users_without_mfa': users_without_mfa,
    }


def find_stale_access_keys(days_threshold: int = 90) -> List[Dict[str, Any]]:
    """
    Find access keys that haven't been rotated in N days.

    Stale access keys are a security risk — they should be rotated
    regularly and deactivated when no longer needed.

    Args:
        days_threshold: Keys older than this are considered stale

    Returns:
        List of users with stale access keys
    """
    iam = get_iam_client()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

    stale_keys = []

    paginator = iam.get_paginator('list_users')
    for page in paginator.paginate():
        for user in page['Users']:
            username = user['UserName']

            # List access keys for user
            keys_response = iam.list_access_keys(UserName=username)
            for key_meta in keys_response['AccessKeyMetadata']:
                key_created = key_meta['CreateDate']

                if key_created < cutoff_date:
                    # Get last used info
                    last_used_response = iam.get_access_key_last_used(
                        AccessKeyId=key_meta['AccessKeyId']
                    )
                    last_used = last_used_response['AccessKeyLastUsed']

                    stale_keys.append({
                        'username': username,
                        'access_key_id': key_meta['AccessKeyId'],
                        'status': key_meta['Status'],
                        'created': key_created.isoformat(),
                        'age_days': (datetime.now(timezone.utc) - key_created).days,
                        'last_used': (
                            last_used['LastUsedDate'].isoformat()
                            if 'LastUsedDate' in last_used else 'Never'
                        ),
                        'last_service': last_used.get('ServiceName', 'N/A'),
                    })

    logger.info(
        f"Found {len(stale_keys)} access keys older than {days_threshold} days"
    )
    return stale_keys


def find_overly_permissive_policies() -> List[Dict[str, Any]]:
    """
    Find IAM policies that grant excessive permissions.

    Looks for policies with '*' actions or '*' resources,
    which violate the principle of least privilege.

    Returns:
        List of overly permissive policies

    Interview Question:
        Q: What is the principle of least privilege and how do you enforce it?
        A: Grant only the minimum permissions required for a task.
           Enforce with:
           1. Start with no permissions, add as needed
           2. Use managed policies scoped to specific services
           3. Condition keys to restrict by IP, time, MFA
           4. IAM Access Analyzer to find unused permissions
           5. Regular permission reviews and automated auditing
           6. SCPs in AWS Organizations as guardrails
    """
    iam = get_iam_client()
    import json

    risky_policies = []

    paginator = iam.get_paginator('list_policies')
    for page in paginator.paginate(Scope='Local', OnlyAttached=True):
        for policy in page['Policies']:
            # Get the current policy version
            version_response = iam.get_policy_version(
                PolicyArn=policy['Arn'],
                VersionId=policy['DefaultVersionId']
            )

            policy_doc = version_response['PolicyVersion']['Document']
            if isinstance(policy_doc, str):
                policy_doc = json.loads(policy_doc)

            # Check for overly permissive statements
            for statement in policy_doc.get('Statement', []):
                if statement.get('Effect') != 'Allow':
                    continue

                actions = statement.get('Action', [])
                resources = statement.get('Resource', [])

                if isinstance(actions, str):
                    actions = [actions]
                if isinstance(resources, str):
                    resources = [resources]

                is_admin = '*' in actions and '*' in resources
                has_wildcard_actions = '*' in actions
                has_wildcard_resources = '*' in resources

                if has_wildcard_actions or has_wildcard_resources:
                    risky_policies.append({
                        'policy_name': policy['PolicyName'],
                        'policy_arn': policy['Arn'],
                        'is_admin_access': is_admin,
                        'wildcard_actions': has_wildcard_actions,
                        'wildcard_resources': has_wildcard_resources,
                        'attached_entities': policy['AttachmentCount'],
                        'risk_level': 'critical' if is_admin else 'high',
                    })

    logger.info(f"Found {len(risky_policies)} overly permissive policies")
    return risky_policies


def generate_iam_security_report() -> Dict[str, Any]:
    """
    Generate a comprehensive IAM security audit report.

    Returns:
        Full audit report with findings and recommendations
    """
    mfa_audit = audit_mfa_status()
    stale_keys = find_stale_access_keys(90)
    risky_policies = find_overly_permissive_policies()

    critical_findings = (
        mfa_audit['mfa_disabled']
        + len([k for k in stale_keys if k['status'] == 'Active'])
        + len([p for p in risky_policies if p['risk_level'] == 'critical'])
    )

    return {
        'generated_at': datetime.now(timezone.utc).isoformat() + 'Z',
        'overall_risk': 'critical' if critical_findings > 5 else 'high' if critical_findings > 0 else 'low',
        'critical_findings': critical_findings,
        'mfa_audit': mfa_audit,
        'stale_access_keys': stale_keys,
        'risky_policies': risky_policies,
    }


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("IAM Security Audit — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires AWS credentials with IAM read access.

    Example usage:

    # Full security report
    report = generate_iam_security_report()
    print(f"  Overall risk: {report['overall_risk']}")
    print(f"  Critical findings: {report['critical_findings']}")

    # MFA audit
    mfa = audit_mfa_status()
    print(f"  MFA compliance: {mfa['compliance_percentage']}%")
    for user in mfa['users_without_mfa']:
        print(f"  ⚠️  {user['username']}: NO MFA")

    # Stale keys
    stale = find_stale_access_keys(days_threshold=90)
    for key in stale:
        print(f"  🔑 {key['username']}: key age {key['age_days']} days")
    """)
