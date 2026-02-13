"""
in_transit_encryption.py

TLS/SSL utilities for securing data in transit.

Prerequisites:
- cryptography (pip install cryptography)
"""

import ssl
import socket
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_tls_certificate(
    hostname: str,
    port: int = 443,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Check TLS certificate of a remote host.

    Interview Question:
        Q: What is mTLS and when do you use it?
        A: Mutual TLS: both client and server present certificates.
           Standard TLS: only server presents cert.
           mTLS: both sides verify identity.
           Use cases: service-to-service in service mesh (Istio, Linkerd),
           zero-trust networks, API authentication.
           Implementation: Cert-Manager + Vault PKI in K8s,
           or Istio auto-injects Envoy sidecars with mTLS.
    """
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                return {
                    'hostname': hostname,
                    'port': port,
                    'subject': dict(x[0] for x in cert.get('subject', ())),
                    'issuer': dict(x[0] for x in cert.get('issuer', ())),
                    'version': ssock.version(),
                    'cipher': ssock.cipher(),
                    'not_before': cert.get('notBefore', ''),
                    'not_after': cert.get('notAfter', ''),
                    'san': [
                        entry[1] for entry in cert.get('subjectAltName', [])
                    ],
                    'valid': True,
                }
    except ssl.SSLCertVerificationError as e:
        return {'hostname': hostname, 'valid': False, 'error': str(e)}
    except Exception as e:
        return {'hostname': hostname, 'valid': False, 'error': str(e)}


def create_ssl_context(
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    ca_file: Optional[str] = None,
    min_version: str = 'TLSv1.2'
) -> ssl.SSLContext:
    """
    Create a secure SSL context for client or server.

    Best practices applied:
    - TLS 1.2+ only
    - No weak ciphers
    - Certificate verification enabled
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT if not cert_file else ssl.PROTOCOL_TLS_SERVER)

    # Set minimum TLS version
    if min_version == 'TLSv1.3':
        context.minimum_version = ssl.TLSVersion.TLSv1_3
    else:
        context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Load certificates
    if cert_file and key_file:
        context.load_cert_chain(cert_file, key_file)
    if ca_file:
        context.load_verify_locations(ca_file)

    return context


if __name__ == "__main__":
    print("In-Transit Encryption — Usage Examples")
    print("""
    # Check a website's TLS certificate
    info = check_tls_certificate('google.com', 443)
    print(f"  Subject: {info.get('subject')}")
    print(f"  TLS version: {info.get('version')}")
    print(f"  Valid: {info['valid']}")
    """)
