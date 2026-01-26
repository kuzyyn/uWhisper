#!/bin/bash

echo "uWhisper Permission Setup"
echo "========================="
echo "This script will configure your system to allow uWhisper to simulate keystrokes (Auto-Paste)"
echo "without needing to run as root."
echo ""

# 1. Create uinput group
echo "[1/4] Checking 'uinput' group..."
if ! getent group uinput > /dev/null; then
    sudo groupadd uinput
    echo "      Created group 'uinput'."
else
    echo "      Group 'uinput' already exists."
fi

# 2. Add user to groups
echo "[2/4] Adding user '$USER' to groups..."
sudo usermod -aG input $USER
sudo usermod -aG uinput $USER
echo "      User added to 'input' and 'uinput' groups."

# 3. Create udev rule
echo "[3/4] Creating udev rule..."
RULE_CONTENT='KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"'
echo "$RULE_CONTENT" | sudo tee /etc/udev/rules.d/99-uwhisper-uinput.rules > /dev/null
echo "      Rule created at /etc/udev/rules.d/99-uwhisper-uinput.rules"

# 4. Load module and reload rules
echo "[4/4] Applying changes..."
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger

echo ""
echo "========================="
echo "SUCCESS!"
echo "IMPORTANT: You MUST Log Out and Log Back In (or Reboot) for these changes to take effect."
echo "after reboot, the 'Auto-Paste' feature should work natively."
