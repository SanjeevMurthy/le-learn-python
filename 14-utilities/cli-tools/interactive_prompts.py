"""
interactive_prompts.py

Interactive CLI prompt utilities.

Prerequisites:
- Standard library
"""

import getpass
import logging
from typing import List, Optional, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask for yes/no confirmation.

    Interview Question:
        Q: How do you make destructive CLI operations safe?
        A: 1. Require explicit confirmation for destructive actions
           2. --force flag to skip confirmation (for automation)
           3. --dry-run to preview changes
           4. Show what will be affected before confirming
           5. Require typing the resource name for critical deletes
    """
    suffix = ' [Y/n]: ' if default else ' [y/N]: '
    response = input(message + suffix).strip().lower()
    if not response:
        return default
    return response in ('y', 'yes')


def choose(message: str, options: List[str], default: int = 0) -> str:
    """Present a numbered menu and return the chosen option."""
    print(message)
    for i, option in enumerate(options):
        marker = '→' if i == default else ' '
        print(f"  {marker} {i + 1}. {option}")

    while True:
        response = input(f"  Choice [1-{len(options)}] (default {default + 1}): ").strip()
        if not response:
            return options[default]
        try:
            idx = int(response) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print(f"  Invalid choice. Enter 1-{len(options)}")


def prompt_secret(message: str = 'Password') -> str:
    """Securely prompt for a secret (no echo)."""
    return getpass.getpass(f"  {message}: ")


def multi_input(message: str, end_marker: str = '') -> List[str]:
    """Collect multiple lines of input until empty line."""
    print(f"{message} (empty line to finish):")
    lines = []
    while True:
        line = input('  > ')
        if line == end_marker:
            break
        lines.append(line)
    return lines


if __name__ == "__main__":
    print("Interactive Prompts — Demo")
    env = choose("Select environment:", ["development", "staging", "production"])
    print(f"  Selected: {env}")

    if env == "production":
        if confirm("⚠️  Deploy to PRODUCTION?"):
            print("  Deploying...")
        else:
            print("  Cancelled")
