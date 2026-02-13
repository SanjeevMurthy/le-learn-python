"""
env_manager.py

Environment variable management.

Prerequisites:
- Standard library
"""

import os
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_required(name: str) -> str:
    """
    Get a required environment variable or raise.

    Interview Question:
        Q: How do you manage configuration in a 12-factor app?
        A: Store config in environment variables. Benefits:
           1. Language-agnostic, OS-agnostic
           2. No secrets in code/repos
           3. Different per deploy (dev/staging/prod)
           Precedence: CLI args > env vars > config file > defaults.
           For secrets: use secret managers (Vault, AWS SSM)
           injected as env vars at runtime.
    """
    value = os.environ.get(name)
    if value is None:
        raise EnvironmentError(f"Required env var '{name}' is not set")
    return value


def get_optional(name: str, default: str = '') -> str:
    """Get an optional environment variable with a default."""
    return os.environ.get(name, default)


def get_int(name: str, default: int = 0) -> int:
    """Get an environment variable as an integer."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Env var '{name}' is not a valid integer: '{value}', using default {default}")
        return default


def get_bool(name: str, default: bool = False) -> bool:
    """Get an environment variable as a boolean."""
    value = os.environ.get(name, '').lower()
    if not value:
        return default
    return value in ('true', '1', 'yes', 'on')


def load_dotenv(filepath: str = '.env') -> Dict[str, str]:
    """Load variables from a .env file (simple parser)."""
    loaded = {}
    if not os.path.exists(filepath):
        return loaded
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value
            loaded[key] = value
    return loaded


def check_required_vars(required: List[str]) -> Dict[str, bool]:
    """Check which required env vars are set."""
    return {var: var in os.environ for var in required}


if __name__ == "__main__":
    # Check common DevOps env vars
    common_vars = ['HOME', 'PATH', 'SHELL', 'USER', 'AWS_REGION']
    status = check_required_vars(common_vars)
    for var, is_set in status.items():
        print(f"  {'✅' if is_set else '❌'} {var}")
