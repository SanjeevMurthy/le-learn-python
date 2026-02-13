"""
encryption_as_service.py

Vault Transit secret engine — encryption as a service.

Prerequisites:
- hvac (pip install hvac)
"""

import os
import logging
import base64
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_client():
    import hvac
    return hvac.Client(
        url=os.environ.get('VAULT_ADDR', 'http://127.0.0.1:8200'),
        token=os.environ.get('VAULT_TOKEN', ''),
    )


def encrypt_data(key_name: str, plaintext: str, mount_point: str = 'transit') -> Dict[str, Any]:
    """
    Encrypt data using Vault Transit.

    Interview Question:
        Q: What is encryption as a service?
        A: Vault Transit engine provides crypto operations without
           exposing keys. Application sends plaintext → Vault encrypts
           → returns ciphertext. Keys never leave Vault.
           Benefits: centralized key management, key rotation without
           re-encryption, audit trail, separation of duties.
           Use case: encrypt PII before storing in database.
    """
    client = _get_client()
    encoded = base64.b64encode(plaintext.encode()).decode()
    try:
        response = client.secrets.transit.encrypt_data(
            key_name, plaintext=encoded, mount_point=mount_point
        )
        ciphertext = response['data']['ciphertext']
        logger.info(f"Encrypted data with key={key_name}")
        return {'ciphertext': ciphertext, 'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def decrypt_data(key_name: str, ciphertext: str, mount_point: str = 'transit') -> Dict[str, Any]:
    """Decrypt data using Vault Transit."""
    client = _get_client()
    try:
        response = client.secrets.transit.decrypt_data(
            key_name, ciphertext=ciphertext, mount_point=mount_point
        )
        decoded = base64.b64decode(response['data']['plaintext']).decode()
        return {'plaintext': decoded, 'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def rotate_key(key_name: str, mount_point: str = 'transit') -> Dict[str, Any]:
    """Rotate an encryption key (old data still decryptable)."""
    client = _get_client()
    try:
        client.secrets.transit.rotate_encryption_key(key_name, mount_point=mount_point)
        logger.info(f"Rotated key: {key_name}")
        return {'key': key_name, 'status': 'rotated'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Encryption as a Service — Usage Examples")
    print("""
    result = encrypt_data('my-key', 'SSN: 123-45-6789')
    print(f"  Ciphertext: {result['ciphertext']}")

    result = decrypt_data('my-key', result['ciphertext'])
    print(f"  Plaintext: {result['plaintext']}")
    """)
