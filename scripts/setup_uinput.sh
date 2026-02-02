#!/usr/bin/env bash
set -euo pipefail

# Setup script for Linux uinput device access
# This script configures uinput permissions and user group membership
# for CooPad host mode (virtual gamepad creation)

echo "═══════════════════════════════════════════════════════"
echo "CooPad - Linux uinput Setup"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "This script will:"
echo "  1. Create udev rule for uinput device access"
echo "  2. Add current user to 'input' group"
echo "  3. Load uinput kernel module"
echo ""

# Check for sudo
if ! command -v sudo >/dev/null 2>&1; then
    echo "Error: sudo is required to perform system changes."
    echo "Install sudo or run as root." >&2
    exit 1
fi

RULE_PATH="/etc/udev/rules.d/99-coopad-uinput.rules"

# Create udev rule
echo "Creating udev rule at $RULE_PATH (requires sudo)..."
sudo tee "$RULE_PATH" > /dev/null <<'UDEV'
# CooPad uinput access rule
# Allow members of 'input' group to access uinput device
KERNEL=="uinput", MODE="0660", GROUP="input", TAG+="uaccess"
SUBSYSTEM=="uinput", MODE="0660", GROUP="input", TAG+="uaccess"
UDEV

echo "✓ udev rule created"
echo ""

# Reload udev rules
echo "Reloading udev rules..."
sudo udevadm control --reload-rules 2>/dev/null || true
sudo udevadm trigger 2>/dev/null || true
echo "✓ udev rules reloaded"
echo ""

# Create input group if it doesn't exist
if ! getent group input >/dev/null 2>&1; then
    echo "Creating 'input' group..."
    sudo groupadd -r input
    echo "✓ Group created"
else
    echo "✓ Group 'input' already exists"
fi
echo ""

# Add user to input group
echo "Adding user '$USER' to group 'input' (requires sudo)..."
sudo usermod -aG input "$USER"
echo "✓ User added to group"
echo ""

# Load uinput module
echo "Loading uinput kernel module..."
if lsmod | grep -q uinput; then
    echo "✓ uinput module already loaded"
else
    sudo modprobe uinput
    echo "✓ uinput module loaded"
fi

# Make uinput load on boot
echo "Configuring uinput to load on boot..."
if [ ! -f /etc/modules-load.d/uinput.conf ]; then
    echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf > /dev/null
    echo "✓ uinput will load on boot"
else
    echo "✓ uinput already configured for boot"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "Setup Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "IMPORTANT: To apply group membership, you must:"
echo ""
echo "Option 1: Log out and log back in (recommended)"
echo "Option 2: Run in current shell: newgrp input"
echo "Option 3: For testing only: sudo -E python3 main.py"
echo ""
echo "After logging back in, you can run CooPad without sudo."
echo ""

exit 0
