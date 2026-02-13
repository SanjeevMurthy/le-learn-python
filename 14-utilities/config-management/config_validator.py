"""
config_validator.py

Configuration validation utilities.

Prerequisites:
- Standard library
"""

import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_config(
    config: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate a configuration dictionary against a schema.

    Interview Question:
        Q: How do you validate configuration at startup?
        A: 1. Validate ALL config at application startup (fail fast)
           2. Check types, ranges, required fields
           3. Validate relationships (port ranges, URL formats)
           4. Log the effective config (with secrets redacted)
           5. Schema validation (JSON Schema, pydantic, cerberus)
           Fail fast: crash on invalid config rather than running
           with bad settings and failing later in production.
    """
    errors = []
    validated = {}

    for key, rules in schema.items():
        value = config.get(key)

        # Required check
        if rules.get('required', False) and value is None:
            errors.append(f"Missing required field: '{key}'")
            continue

        if value is None:
            validated[key] = rules.get('default')
            continue

        # Type check
        expected_type = rules.get('type')
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"'{key}': expected {expected_type.__name__}, got {type(value).__name__}")
            continue

        # Range check
        if 'min' in rules and value < rules['min']:
            errors.append(f"'{key}': {value} is below minimum {rules['min']}")
        if 'max' in rules and value > rules['max']:
            errors.append(f"'{key}': {value} is above maximum {rules['max']}")

        # Enum check
        if 'choices' in rules and value not in rules['choices']:
            errors.append(f"'{key}': '{value}' not in {rules['choices']}")

        validated[key] = value

    return {'valid': len(errors) == 0, 'errors': errors, 'config': validated}


def redact_secrets(config: Dict[str, Any], secret_keys: List[str] = None) -> Dict[str, Any]:
    """Redact secret values for safe logging."""
    secret_keys = secret_keys or ['password', 'secret', 'token', 'api_key', 'private_key']
    redacted = {}
    for key, value in config.items():
        if isinstance(value, dict):
            redacted[key] = redact_secrets(value, secret_keys)
        elif any(s in key.lower() for s in secret_keys):
            redacted[key] = '***REDACTED***'
        else:
            redacted[key] = value
    return redacted


if __name__ == "__main__":
    schema = {
        'port': {'type': int, 'required': True, 'min': 1024, 'max': 65535},
        'host': {'type': str, 'default': 'localhost'},
        'env': {'type': str, 'required': True, 'choices': ['dev', 'staging', 'prod']},
        'db_password': {'type': str, 'required': True},
    }
    config = {'port': 8080, 'env': 'prod', 'db_password': 'secret123'}
    result = validate_config(config, schema)
    print(f"  Valid: {result['valid']}, Errors: {result['errors']}")
    print(f"  Redacted: {redact_secrets(config)}")
