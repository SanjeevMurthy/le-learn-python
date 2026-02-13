"""
ssl_certificate_checker.py

SSL/TLS certificate checking and validation.

Prerequisites:
- ssl (stdlib), socket (stdlib)
"""

import ssl
import socket
import logging
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_ssl_certificate(
    hostname: str, port: int = 443, timeout: int = 10
) -> Dict[str, Any]:
    """
    Check SSL/TLS certificate of a remote host.

    Interview Question:
        Q: How do you troubleshoot TLS/SSL issues?
        A: Common issues:
           1. Certificate expired → check `not_after`, set up monitoring
           2. Hostname mismatch → check SAN (Subject Alt Names)
           3. Untrusted CA → check certificate chain, add CA to trust store
           4. Protocol version → TLS 1.2+ required, disable TLS 1.0/1.1
           5. Cipher suite → weak ciphers rejected by modern clients
           Tools: `openssl s_client -connect host:443`,
           `openssl x509 -in cert.pem -text -noout`
    """
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                # Parse expiry
                not_after = cert.get('notAfter', '')
                try:
                    expires = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    days_remaining = (expires - datetime.utcnow()).days
                except ValueError:
                    days_remaining = -1

                # Get SANs
                sans = [entry[1] for entry in cert.get('subjectAltName', [])]

                return {
                    'hostname': hostname,
                    'valid': True,
                    'subject': dict(x[0] for x in cert.get('subject', ())),
                    'issuer': dict(x[0] for x in cert.get('issuer', ())),
                    'tls_version': ssock.version(),
                    'cipher': ssock.cipher()[0] if ssock.cipher() else '',
                    'expires': not_after,
                    'days_remaining': days_remaining,
                    'san': sans,
                    'needs_renewal': days_remaining < 30,
                }
    except ssl.SSLCertVerificationError as e:
        return {'hostname': hostname, 'valid': False, 'error': str(e)}
    except Exception as e:
        return {'hostname': hostname, 'valid': False, 'error': str(e)}


def bulk_check_certificates(hosts: List[str]) -> List[Dict[str, Any]]:
    """Check certificates for multiple hosts."""
    results = []
    for host in hosts:
        result = check_ssl_certificate(host)
        status = "✅" if result['valid'] else "❌"
        logger.info(f"{status} {host}: {result.get('days_remaining', '?')} days remaining")
        results.append(result)
    return results


if __name__ == "__main__":
    print("SSL Certificate Checker")
    hosts = ['google.com', 'github.com']
    for result in bulk_check_certificates(hosts):
        status = "✅" if result['valid'] else "❌"
        print(f"  {status} {result['hostname']}: {result.get('days_remaining', '?')} days, TLS {result.get('tls_version', '?')}")
