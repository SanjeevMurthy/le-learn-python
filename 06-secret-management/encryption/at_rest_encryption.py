"""
at_rest_encryption.py

Data encryption at rest using Python's cryptography library.

Prerequisites:
- cryptography (pip install cryptography)
"""

import os
import logging
import base64
from typing import Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_key() -> bytes:
    """Generate a 256-bit AES key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key()


def encrypt_data(plaintext: str, key: bytes) -> str:
    """
    Encrypt data using Fernet (AES-128-CBC + HMAC-SHA256).

    Interview Question:
        Q: What is envelope encryption?
        A: Two-tier key system:
           1. Data Encryption Key (DEK): encrypts actual data
           2. Key Encryption Key (KEK): wraps/encrypts the DEK
           KEK is stored in KMS (AWS KMS, GCP KMS, Vault Transit).
           Encrypted DEK + encrypted data stored together.
           Benefits: key rotation without re-encrypting all data
           (just re-wrap DEK), centralized key management.
    """
    from cryptography.fernet import Fernet
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_data(ciphertext: str, key: bytes) -> str:
    """Decrypt Fernet-encrypted data."""
    from cryptography.fernet import Fernet
    f = Fernet(key)
    decrypted = f.decrypt(ciphertext.encode())
    return decrypted.decode()


def encrypt_file(filepath: str, key: bytes, output_path: str = '') -> str:
    """Encrypt a file."""
    from cryptography.fernet import Fernet
    f = Fernet(key)

    with open(filepath, 'rb') as file:
        data = file.read()

    encrypted = f.encrypt(data)
    out = output_path or filepath + '.enc'

    with open(out, 'wb') as file:
        file.write(encrypted)

    logger.info(f"Encrypted {filepath} → {out}")
    return out


def decrypt_file(filepath: str, key: bytes, output_path: str = '') -> str:
    """Decrypt an encrypted file."""
    from cryptography.fernet import Fernet
    f = Fernet(key)

    with open(filepath, 'rb') as file:
        encrypted = file.read()

    decrypted = f.decrypt(encrypted)
    out = output_path or filepath.replace('.enc', '.dec')

    with open(out, 'wb') as file:
        file.write(decrypted)

    logger.info(f"Decrypted {filepath} → {out}")
    return out


if __name__ == "__main__":
    print("At-Rest Encryption — Usage Examples")
    print("""
    key = generate_key()
    encrypted = encrypt_data('sensitive data', key)
    decrypted = decrypt_data(encrypted, key)
    print(f"  Original → Encrypted → Decrypted: {decrypted}")

    # File encryption
    encrypt_file('config.yaml', key)
    decrypt_file('config.yaml.enc', key)
    """)
