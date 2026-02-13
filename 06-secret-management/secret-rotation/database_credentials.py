"""
database_credentials.py

Automated database credential rotation.

Prerequisites:
- requests (pip install requests)
"""

import os
import secrets
import string
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_password(length: int = 24) -> str:
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def rotate_postgres_password(
    host: str, port: int, db_name: str,
    admin_user: str, admin_pass: str,
    target_user: str
) -> Dict[str, Any]:
    """
    Rotate a PostgreSQL user password.

    Interview Question:
        Q: How do you rotate DB credentials safely?
        A: 1. Dual-user pattern: create new user, update app, drop old
           2. Vault dynamic secrets: auto-generate with TTL
           3. AWS RDS: Secrets Manager with rotation Lambda
           4. K8s: External Secrets Operator syncs from Vault
           Key: zero-downtime. Always verify new creds before
           revoking old ones. Use connection poolers (PgBouncer).
    """
    new_password = generate_password()

    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host, port=port, dbname=db_name,
            user=admin_user, password=admin_pass
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                f"ALTER USER {target_user} WITH PASSWORD %s",
                (new_password,)
            )
        conn.close()
        logger.info(f"Rotated password for {target_user}")
        return {'user': target_user, 'status': 'rotated', 'password': new_password}
    except ImportError:
        logger.warning("psycopg2 not installed — returning generated password only")
        return {'user': target_user, 'status': 'password_generated', 'password': new_password}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("Database Credential Rotation — Usage Examples")
    print(f"  Generated password sample: {generate_password()}")
    print("""
    result = rotate_postgres_password(
        'db.example.com', 5432, 'mydb',
        'admin', 'admin_pass', 'app_user'
    )
    """)
