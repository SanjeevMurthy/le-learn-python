"""
terraform_wrapper.py

Python wrapper for Terraform CLI operations.

Interview Topics:
- Terraform workflow (init, plan, apply, destroy)
- Providers and modules
- HCL vs JSON configuration

Prerequisites:
- subprocess (stdlib), json (stdlib)
"""

import subprocess
import json
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _run_terraform(
    args: List[str], cwd: str = '.', json_output: bool = False
) -> Dict[str, Any]:
    """
    Run a Terraform CLI command.

    Interview Question:
        Q: Explain the Terraform workflow.
        A: 1. terraform init — download providers, init backend
           2. terraform plan — preview changes (diff desired vs actual)
           3. terraform apply — execute the plan
           4. terraform destroy — tear down all resources
           State tracks resource mappings (logical name → cloud ID).
           Plan file can be saved and applied later for review workflows.
    """
    cmd = ['terraform'] + args
    if json_output:
        cmd.append('-json')

    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=600
    )

    output = result.stdout
    if json_output:
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = result.stdout

    return {
        'exit_code': result.returncode,
        'output': output,
        'stderr': result.stderr,
        'success': result.returncode == 0,
    }


def init(cwd: str = '.', backend_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Initialize Terraform working directory."""
    args = ['init', '-input=false']
    if backend_config:
        for k, v in backend_config.items():
            args.append(f'-backend-config={k}={v}')
    return _run_terraform(args, cwd)


def plan(cwd: str = '.', out: str = 'tfplan', var_file: str = '') -> Dict[str, Any]:
    """Generate an execution plan."""
    args = ['plan', '-input=false', f'-out={out}']
    if var_file:
        args.append(f'-var-file={var_file}')
    return _run_terraform(args, cwd)


def apply(cwd: str = '.', plan_file: str = 'tfplan', auto_approve: bool = False) -> Dict[str, Any]:
    """Apply infrastructure changes."""
    args = ['apply', '-input=false']
    if auto_approve:
        args.append('-auto-approve')
    else:
        args.append(plan_file)
    return _run_terraform(args, cwd)


def output(cwd: str = '.') -> Dict[str, Any]:
    """Get Terraform outputs."""
    return _run_terraform(['output', '-json'], cwd, json_output=True)


def destroy(cwd: str = '.', auto_approve: bool = False) -> Dict[str, Any]:
    """Destroy all managed infrastructure."""
    args = ['destroy', '-input=false']
    if auto_approve:
        args.append('-auto-approve')
    return _run_terraform(args, cwd)


if __name__ == "__main__":
    print("Terraform Wrapper — Usage Examples")
    print("""
    init('/path/to/infra', backend_config={'bucket': 'my-state-bucket'})
    plan('/path/to/infra', var_file='prod.tfvars')
    apply('/path/to/infra')
    outputs = output('/path/to/infra')
    """)
