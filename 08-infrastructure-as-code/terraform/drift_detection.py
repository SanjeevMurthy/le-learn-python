"""
drift_detection.py

Detect infrastructure drift from Terraform desired state.

Prerequisites:
- subprocess, json
"""

import subprocess
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_drift(cwd: str = '.') -> Dict[str, Any]:
    """
    Run terraform plan to detect configuration drift.

    Interview Question:
        Q: What is infrastructure drift and how do you handle it?
        A: Drift = actual infra differs from IaC definition.
           Causes: manual console changes, external automation,
           out-of-band updates, failed applies.
           Detection: `terraform plan` shows pending changes.
           Remediation: either update code to match reality
           or `terraform apply` to enforce desired state.
           Prevention: lock down console access, use CI/CD for all changes,
           scheduled drift detection (cron job running plan).
    """
    result = subprocess.run(
        ['terraform', 'plan', '-detailed-exitcode', '-json', '-input=false'],
        cwd=cwd, capture_output=True, text=True, timeout=600
    )

    # Exit codes: 0=no changes, 1=error, 2=changes detected
    has_drift = result.returncode == 2
    changes = []

    if has_drift:
        for line in result.stdout.strip().split('\n'):
            try:
                entry = json.loads(line)
                if entry.get('type') == 'resource_drift':
                    resource = entry.get('change', {}).get('resource', {})
                    changes.append({
                        'address': resource.get('addr', ''),
                        'type': resource.get('resource_type', ''),
                        'action': entry.get('change', {}).get('action', ''),
                    })
            except json.JSONDecodeError:
                continue

    return {
        'has_drift': has_drift,
        'drift_count': len(changes),
        'changes': changes,
        'exit_code': result.returncode,
    }


def generate_drift_report(drift_result: Dict[str, Any]) -> str:
    """Generate a human-readable drift report."""
    if not drift_result['has_drift']:
        return "✅ No drift detected — infrastructure matches desired state."

    lines = [f"⚠️ Drift detected: {drift_result['drift_count']} resource(s) changed\n"]
    for change in drift_result['changes']:
        lines.append(f"  - {change['address']} ({change['action']})")
    return '\n'.join(lines)


if __name__ == "__main__":
    print("Drift Detection — Usage Examples")
    print("""
    result = detect_drift('/path/to/infra')
    print(generate_drift_report(result))
    """)
