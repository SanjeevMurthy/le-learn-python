"""
key_management.py

Cryptographic key management utilities.

Prerequisites:
- cryptography (pip install cryptography)
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_rsa_keypair(key_size: int = 2048) -> Dict[str, bytes]:
    """
    Generate an RSA key pair.

    Interview Question:
        Q: Symmetric vs asymmetric encryption — when to use each?
        A: Symmetric (AES): same key for encrypt/decrypt. Fast.
           Use for: data at rest, bulk data, session encryption.
           Asymmetric (RSA, ECDSA): public/private key pair. Slow.
           Use for: key exchange, digital signatures, TLS handshake.
           TLS combines both: asymmetric for handshake → establish
           symmetric session key → symmetric for data transfer.
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=key_size
    )

    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.SubjectPublicKeyInfo,
    )

    logger.info(f"Generated RSA-{key_size} key pair")
    return {'private_key': private_pem, 'public_key': public_pem}


def hash_data(data: str, algorithm: str = 'sha256') -> str:
    """Hash data using the specified algorithm."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    algo_map = {
        'sha256': hashes.SHA256(),
        'sha384': hashes.SHA384(),
        'sha512': hashes.SHA512(),
    }
    h = hashes.Hash(algo_map.get(algorithm, hashes.SHA256()), backend=default_backend())
    h.update(data.encode())
    digest = h.finalize()
    return digest.hex()


def derive_key_from_password(
    password: str, salt: Optional[bytes] = None, length: int = 32
) -> Dict[str, bytes]:
    """Derive an encryption key from a password using PBKDF2."""
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    salt = salt or os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=600_000,  # OWASP recommended minimum
    )
    key = kdf.derive(password.encode())
    return {'key': key, 'salt': salt}


if __name__ == "__main__":
    print("Key Management — Usage Examples")
    print("""
    # Generate RSA key pair
    keys = generate_rsa_keypair(2048)

    # Hash data
    digest = hash_data('hello world', 'sha256')
    print(f"  SHA-256: {digest}")

    # Derive key from password
    result = derive_key_from_password('my-secure-password')
    print(f"  Key length: {len(result['key'])} bytes")
    """)
