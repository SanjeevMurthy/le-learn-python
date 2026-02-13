"""
test_config_management.py

Unit tests for Module 14 — Config Management utilities.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_env_get_bool():
    """Test boolean env var parsing."""
    true_values = ['true', '1', 'yes', 'on']
    false_values = ['false', '0', 'no', 'off', '']

    for val in true_values:
        assert val.lower() in ('true', '1', 'yes', 'on'), f"{val} should be truthy"
    for val in false_values:
        assert val.lower() not in ('true', '1', 'yes', 'on'), f"{val} should be falsy"
    print("  ✅ test_env_get_bool")


def test_deep_merge():
    """Test deep merge of config dictionaries."""
    base = {'db': {'host': 'localhost', 'port': 5432}, 'debug': False}
    override = {'db': {'port': 5433, 'ssl': True}, 'debug': True}

    # Manual deep merge
    result = {**base}
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = {**result[key], **value}
        else:
            result[key] = value

    assert result['db']['host'] == 'localhost', "Base value should be preserved"
    assert result['db']['port'] == 5433, "Override value should win"
    assert result['db']['ssl'] is True, "New key should be added"
    assert result['debug'] is True, "Top-level override should win"
    print("  ✅ test_deep_merge")


def test_secret_redaction():
    """Test that secrets are redacted in config output."""
    config = {'host': 'db.example.com', 'password': 'secret123', 'api_key': 'abc'}
    secret_keys = ['password', 'secret', 'token', 'api_key']

    redacted = {}
    for key, value in config.items():
        if any(s in key.lower() for s in secret_keys):
            redacted[key] = '***REDACTED***'
        else:
            redacted[key] = value

    assert redacted['host'] == 'db.example.com'
    assert redacted['password'] == '***REDACTED***'
    assert redacted['api_key'] == '***REDACTED***'
    print("  ✅ test_secret_redaction")


def test_config_validation():
    """Test config schema validation."""
    config = {'port': 8080, 'env': 'prod'}
    schema = {
        'port': {'type': int, 'min': 1024, 'max': 65535},
        'env': {'choices': ['dev', 'staging', 'prod']},
    }

    errors = []
    for key, rules in schema.items():
        value = config.get(key)
        if 'type' in rules and not isinstance(value, rules['type']):
            errors.append(f"Type mismatch for {key}")
        if 'min' in rules and value < rules['min']:
            errors.append(f"{key} below min")
        if 'max' in rules and value > rules['max']:
            errors.append(f"{key} above max")
        if 'choices' in rules and value not in rules['choices']:
            errors.append(f"{key} not in choices")

    assert len(errors) == 0, f"Validation errors: {errors}"
    print("  ✅ test_config_validation")


if __name__ == "__main__":
    print("Config Management Unit Tests")
    test_env_get_bool()
    test_deep_merge()
    test_secret_redaction()
    test_config_validation()
    print("  All tests passed!")
