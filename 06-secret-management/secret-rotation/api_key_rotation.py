"""
api_key_rotation.py

API key rotation automation.

Prerequisites:
- requests (pip install requests)
"""

import os
import secrets
import logging
from typing import Dict, Any

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_api_key(prefix: str = 'sk', length: int = 32) -> str:
    """Generate a secure API key with prefix."""
    key = secrets.token_urlsafe(length)
    return f'{prefix}_{key}'


def rotate_api_key_with_overlap(
    create_fn, validate_fn, revoke_fn,
    key_name: str
) -> Dict[str, Any]:
    """
    Rotate an API key with overlap period (zero downtime).

    Interview Question:
        Q: How do you rotate API keys without downtime?
        A: Overlap pattern:
           1. Create new key (both old and new are valid)
           2. Update all consumers to use new key
           3. Validate new key works in all services
           4. Revoke old key
           Alternative: dual-key support in API gateway
           (accept both keys during rotation window).
    """
    # Step 1: Create new key
    new_key = generate_api_key()
    if not create_fn(key_name, new_key):
        return {'status': 'create_failed'}

    # Step 2: Validate new key
    if not validate_fn(new_key):
        logger.error("New key validation failed")
        return {'status': 'validation_failed'}

    # Step 3: Revoke old key
    if not revoke_fn(key_name):
        logger.warning("Old key revocation failed — manual cleanup needed")
        return {'status': 'partial', 'new_key': new_key}

    logger.info(f"Rotated API key: {key_name}")
    return {'status': 'rotated', 'key_name': key_name, 'new_key': new_key}


if __name__ == "__main__":
    print("API Key Rotation — Usage Examples")
    print(f"  Generated key: {generate_api_key()}")
    print("""
    result = rotate_api_key_with_overlap(
        create_fn=lambda name, key: True,
        validate_fn=lambda key: True,
        revoke_fn=lambda name: True,
        key_name='payment-service-key'
    )
    """)
