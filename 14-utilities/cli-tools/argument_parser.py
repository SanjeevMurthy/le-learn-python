"""
argument_parser.py

CLI argument parsing utilities.

Prerequisites:
- argparse (stdlib)
"""

import argparse
import sys
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_deploy_parser() -> argparse.ArgumentParser:
    """
    Create a deployment CLI argument parser.

    Interview Question:
        Q: How do you design a good CLI tool?
        A: 1. Consistent subcommand structure (deploy, rollback, status)
           2. Help text for every argument (--help should be sufficient)
           3. Sensible defaults (environment=staging, timeout=300)
           4. Dry-run mode (--dry-run) for safe testing
           5. Machine-readable output (--output json)
           6. Exit codes: 0=success, 1=error, 2=usage error
           7. Configuration file fallback (CLI > env > config file)
    """
    parser = argparse.ArgumentParser(
        prog='deploy',
        description='Deployment automation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n  deploy app --env production --version v1.2.3\n  deploy rollback --env staging',
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Deploy subcommand
    deploy = subparsers.add_parser('app', help='Deploy an application')
    deploy.add_argument('--env', choices=['dev', 'staging', 'production'],
                        default='staging', help='Target environment')
    deploy.add_argument('--version', required=True, help='Version to deploy')
    deploy.add_argument('--dry-run', action='store_true', help='Simulate deployment')
    deploy.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')

    # Rollback subcommand
    rollback = subparsers.add_parser('rollback', help='Rollback deployment')
    rollback.add_argument('--env', required=True, help='Target environment')
    rollback.add_argument('--version', help='Specific version to rollback to')

    # Status subcommand
    status = subparsers.add_parser('status', help='Check deployment status')
    status.add_argument('--env', default='production', help='Environment to check')
    status.add_argument('--output', choices=['text', 'json'], default='text')

    return parser


def parse_key_value_args(args: list) -> Dict[str, str]:
    """Parse key=value argument pairs."""
    result = {}
    for arg in args:
        if '=' not in arg:
            raise ValueError(f"Invalid format: '{arg}'. Expected key=value")
        key, value = arg.split('=', 1)
        result[key.strip()] = value.strip()
    return result


if __name__ == "__main__":
    parser = create_deploy_parser()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        print(f"  Command: {args.command}")
        print(f"  Args: {vars(args)}")
    else:
        parser.print_help()
