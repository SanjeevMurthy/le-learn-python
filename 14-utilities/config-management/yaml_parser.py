"""
yaml_parser.py

YAML configuration parsing utilities.

Prerequisites:
- pyyaml (pip install pyyaml)
"""

import os
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_yaml(filepath: str) -> Dict[str, Any]:
    """
    Load and parse a YAML file safely.

    Interview Question:
        Q: Why use yaml.safe_load instead of yaml.load?
        A: yaml.load can execute arbitrary Python code via YAML tags
           (!!python/object). This is a security vulnerability
           (arbitrary code execution from config files).
           yaml.safe_load only loads basic types (str, int, list, dict).
           Always use safe_load for untrusted input.
    """
    try:
        import yaml
        with open(filepath) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        logger.error("pyyaml not installed: pip install pyyaml")
        return {}
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {}


def merge_yaml_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge multiple YAML configs (later configs override earlier)."""
    result = {}
    for config in configs:
        _deep_merge(result, config)
    return result


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override into base."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def yaml_to_env(config: Dict[str, Any], prefix: str = '') -> Dict[str, str]:
    """Flatten YAML config to environment variable format."""
    env_vars = {}
    for key, value in config.items():
        env_key = f"{prefix}_{key}".upper() if prefix else key.upper()
        if isinstance(value, dict):
            env_vars.update(yaml_to_env(value, env_key))
        else:
            env_vars[env_key] = str(value)
    return env_vars


if __name__ == "__main__":
    # Demo with inline config
    config = {
        'database': {'host': 'localhost', 'port': 5432},
        'redis': {'host': 'localhost', 'port': 6379},
    }
    override = {'database': {'port': 5433, 'ssl': True}}
    merged = merge_yaml_configs(config, override)
    print(f"  Merged: {merged}")
    print(f"  Env vars: {yaml_to_env(merged, 'APP')}")
