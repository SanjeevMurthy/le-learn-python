"""
resource_lifecycle.py

Pulumi resource management and configuration.

Prerequisites:
- subprocess
"""

import subprocess
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def set_config(key: str, value: str, stack: str = 'dev', secret: bool = False, cwd: str = '.') -> Dict[str, Any]:
    """Set a Pulumi stack config value."""
    args = ['pulumi', 'config', 'set', key, value, '--stack', stack]
    if secret:
        args.append('--secret')
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return {'success': result.returncode == 0, 'key': key}


def get_config(stack: str = 'dev', cwd: str = '.') -> Dict[str, str]:
    """Get all config values for a stack."""
    result = subprocess.run(
        ['pulumi', 'config', '--stack', stack, '--json'],
        cwd=cwd, capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}
    return {}


def refresh_state(stack: str = 'dev', cwd: str = '.') -> Dict[str, Any]:
    """Refresh the state to match actual cloud resources."""
    result = subprocess.run(
        ['pulumi', 'refresh', '--stack', stack, '--yes'],
        cwd=cwd, capture_output=True, text=True, timeout=300
    )
    return {'success': result.returncode == 0, 'output': result.stdout}


if __name__ == "__main__":
    print("Resource Lifecycle — Usage Examples")
    print("""
    set_config('aws:region', 'us-east-1', stack='prod')
    set_config('dbPassword', 's3cret', stack='prod', secret=True)
    config = get_config(stack='prod')
    """)
