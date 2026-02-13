"""
certificate_renewal.py

TLS certificate renewal automation.

Prerequisites:
- cryptography (pip install cryptography)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_certificate_expiry(cert_path: str) -> Dict[str, Any]:
    """
    Check TLS certificate expiry.

    Interview Question:
        Q: How do you manage TLS certificates at scale?
        A: 1. Cert-Manager (K8s): automated issuance and renewal
           2. Let's Encrypt + ACME protocol: free certs, auto-renew
           3. Vault PKI engine: internal CA for mTLS
           4. AWS ACM: managed certs for ALB/CloudFront
           Monitor expiry and alert 30 days before. Never let
           certs expire — causes outages and security warnings.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    with open(cert_path, 'rb') as f:
        cert_data = f.read()

    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    now = datetime.now(timezone.utc)
    expires = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after.replace(tzinfo=timezone.utc)
    days_remaining = (expires - now).days

    return {
        'subject': cert.subject.rfc4514_string(),
        'issuer': cert.issuer.rfc4514_string(),
        'expires': expires.isoformat(),
        'days_remaining': days_remaining,
        'needs_renewal': days_remaining < 30,
        'serial': str(cert.serial_number),
    }


def generate_self_signed_cert(
    common_name: str,
    days: int = 365,
    key_size: int = 2048
) -> Dict[str, bytes]:
    """Generate a self-signed certificate (for testing/internal use)."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    # Generate key
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

    # Build certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days))
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )

    logger.info(f"Generated self-signed cert for {common_name}")
    return {'certificate': cert_pem, 'private_key': key_pem}


if __name__ == "__main__":
    print("Certificate Renewal — Usage Examples")
    print("""
    # Check cert expiry
    info = check_certificate_expiry('/etc/ssl/certs/server.pem')
    print(f"  Expires in {info['days_remaining']} days")
    if info['needs_renewal']:
        print("  ⚠️ Certificate needs renewal!")

    # Generate self-signed cert (dev/testing)
    cert = generate_self_signed_cert('localhost')
    """)
