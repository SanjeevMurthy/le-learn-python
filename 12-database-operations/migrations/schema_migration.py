"""
schema_migration.py

Database schema migration management.

Prerequisites:
- subprocess
"""

import os
import time
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_migration(
    name: str,
    migrations_dir: str = 'migrations'
) -> Dict[str, Any]:
    """
    Create a new migration file.

    Interview Question:
        Q: How do you handle database migrations safely?
        A: 1. Version-controlled migration files (sequential numbering)
           2. Forward + rollback scripts for every change
           3. Test on staging with production-size data
           4. Online DDL: avoid long table locks (pt-online-schema-change,
              pg_repack, gh-ost for MySQL)
           5. Deploy strategy: migrate first, then deploy code
              (expand/contract pattern)
           6. Never rename/drop columns immediately — add new, migrate
              data, update code, then drop old.
    """
    os.makedirs(migrations_dir, exist_ok=True)

    timestamp = int(time.time())
    filename_up = f'{timestamp}_{name}_up.sql'
    filename_down = f'{timestamp}_{name}_down.sql'

    up_path = os.path.join(migrations_dir, filename_up)
    down_path = os.path.join(migrations_dir, filename_down)

    up_template = f"-- Migration: {name}\n-- Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n-- Add your UP migration SQL here\n"
    down_template = f"-- Rollback: {name}\n-- Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n-- Add your DOWN migration SQL here\n"

    with open(up_path, 'w') as f:
        f.write(up_template)
    with open(down_path, 'w') as f:
        f.write(down_template)

    return {
        'up_file': up_path,
        'down_file': down_path,
        'version': timestamp,
    }


def list_migrations(migrations_dir: str = 'migrations') -> List[Dict[str, Any]]:
    """List all migration files."""
    if not os.path.exists(migrations_dir):
        return []

    files = sorted(os.listdir(migrations_dir))
    migrations = []
    for f in files:
        if f.endswith('_up.sql'):
            version = f.split('_')[0]
            name = '_'.join(f.split('_')[1:]).replace('_up.sql', '')
            migrations.append({'version': version, 'name': name, 'file': f})
    return migrations


def generate_expand_contract_plan(
    old_column: str, new_column: str, table: str
) -> Dict[str, Any]:
    """Generate an expand/contract migration plan for a column rename."""
    return {
        'phase_1_expand': f"""
-- Phase 1: Add new column
ALTER TABLE {table} ADD COLUMN {new_column} <type>;
-- Backfill data
UPDATE {table} SET {new_column} = {old_column};
-- Add trigger to keep in sync
CREATE TRIGGER sync_{old_column}_{new_column}
  BEFORE INSERT OR UPDATE ON {table}
  FOR EACH ROW EXECUTE FUNCTION sync_columns();
""",
        'phase_2_migrate': f"""
-- Phase 2: Update application code to use {new_column}
-- Deploy new code that reads/writes {new_column}
""",
        'phase_3_contract': f"""
-- Phase 3: Drop old column (after all code uses new column)
DROP TRIGGER sync_{old_column}_{new_column} ON {table};
ALTER TABLE {table} DROP COLUMN {old_column};
""",
    }


if __name__ == "__main__":
    print("Schema Migration — Usage Examples")
    plan = generate_expand_contract_plan('user_name', 'username', 'users')
    for phase, sql in plan.items():
        print(f"\n  {phase}:")
        print(f"  {sql.strip()[:100]}...")
