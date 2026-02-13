"""
vm_management.py

Azure Virtual Machine management using Azure SDK.

Interview Topics:
- Azure VM vs AWS EC2 vs GCP Compute Engine
- Azure Resource Groups concept
- Managed disks and availability sets

Production Use Cases:
- VM inventory across resource groups
- Start/stop/deallocate operations for cost savings
- VM sizing and status reporting

Prerequisites:
- azure-mgmt-compute, azure-identity (pip install azure-mgmt-compute azure-identity)
"""

import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_compute_client():
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID', '')
    credential = DefaultAzureCredential()
    return ComputeManagementClient(credential, subscription_id)


def list_vms(resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Azure VMs, optionally filtered by resource group.

    Interview Question:
        Q: What are Azure Resource Groups and why do they matter?
        A: Resource Groups are logical containers for Azure resources.
           Key differences from AWS:
           - Every Azure resource MUST belong to exactly one RG
           - RGs can span regions
           - Deleting an RG deletes all contained resources
           - RBAC can be applied at RG level
           - Tags are inherited by resources in the RG
           Best practice: one RG per application per environment.
    """
    client = get_compute_client()

    vms = []
    if resource_group:
        vm_list = client.virtual_machines.list(resource_group)
    else:
        vm_list = client.virtual_machines.list_all()

    for vm in vm_list:
        # Get power state (requires instance view)
        power_state = 'unknown'
        try:
            rg = vm.id.split('/')[4]  # Extract RG from resource ID
            instance_view = client.virtual_machines.instance_view(rg, vm.name)
            for status in instance_view.statuses:
                if status.code.startswith('PowerState/'):
                    power_state = status.code.split('/')[-1]
        except Exception:
            pass

        vms.append({
            'name': vm.name,
            'location': vm.location,
            'vm_size': vm.hardware_profile.vm_size,
            'power_state': power_state,
            'resource_group': vm.id.split('/')[4],
            'os_type': vm.storage_profile.os_disk.os_type if vm.storage_profile.os_disk else 'N/A',
            'tags': dict(vm.tags) if vm.tags else {},
        })

    logger.info(f"Found {len(vms)} Azure VMs")
    return vms


def deallocate_vm(resource_group: str, vm_name: str) -> Dict[str, Any]:
    """
    Deallocate (stop + release compute) an Azure VM.

    Interview Question:
        Q: What is the difference between Stop and Deallocate in Azure?
        A: Stop: VM is stopped but compute resources are still allocated
           (you still pay for compute). Deallocate: VM is stopped AND
           compute resources are released (you stop paying for compute,
           but still pay for storage). Always deallocate to save costs.
    """
    client = get_compute_client()
    try:
        poller = client.virtual_machines.begin_deallocate(resource_group, vm_name)
        logger.info(f"Deallocating VM: {vm_name}")
        return {'vm_name': vm_name, 'status': 'deallocating'}
    except Exception as e:
        logger.error(f"Deallocate failed: {e}")
        return {'vm_name': vm_name, 'status': 'error', 'error': str(e)}


def start_vm(resource_group: str, vm_name: str) -> Dict[str, Any]:
    """Start a deallocated Azure VM."""
    client = get_compute_client()
    try:
        poller = client.virtual_machines.begin_start(resource_group, vm_name)
        logger.info(f"Starting VM: {vm_name}")
        return {'vm_name': vm_name, 'status': 'starting'}
    except Exception as e:
        logger.error(f"Start failed: {e}")
        return {'vm_name': vm_name, 'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("Azure VM Management — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: Requires Azure credentials (AZURE_SUBSCRIPTION_ID).

    # List all VMs
    vms = list_vms()
    for vm in vms:
        print(f"  {vm['name']}: {vm['vm_size']} ({vm['power_state']})")

    # Deallocate a VM
    deallocate_vm('my-resource-group', 'dev-vm-01')
    """)
