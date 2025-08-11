#!/bin/bash

# Proxmox API credentials
TOKEN="root@pam!flipsync:930bbbbe-6a54-44bd-83a7-0b69992e51fd"
PROXMOX_HOST="proxmox.proxy.equipment"
VM_ID="201"

echo "🔍 Checking VM 201 status..."
curl -k -H "Authorization: PVEAPIToken=$TOKEN" \
  "https://$PROXMOX_HOST:8006/api2/json/nodes/pve/qemu/$VM_ID/status/current"

echo -e "\n\n🔧 Setting root password on VM 201..."
curl -k -X POST -H "Authorization: PVEAPIToken=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command":"echo '\''root:FlipSync2024!'\'' | chpasswd"}' \
  "https://$PROXMOX_HOST:8006/api2/json/nodes/pve/qemu/$VM_ID/agent/exec"

echo -e "\n\n🔑 Enabling SSH password authentication..."
curl -k -X POST -H "Authorization: PVEAPIToken=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command":"sed -i '\''s/#PasswordAuthentication no/PasswordAuthentication yes/'\'' /etc/ssh/sshd_config && sed -i '\''s/#PermitRootLogin prohibit-password/PermitRootLogin yes/'\'' /etc/ssh/sshd_config && systemctl restart ssh"}' \
  "https://$PROXMOX_HOST:8006/api2/json/nodes/pve/qemu/$VM_ID/agent/exec"

echo -e "\n\n✅ SSH should now be enabled with password: FlipSync2024!"
