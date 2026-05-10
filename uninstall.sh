#!/bin/bash

# ==============================================================================
# Project     : Battery Guard (Full Cleanup)
# Author      : Mohamed Salem
# Date        : May 2026
# Description : Professional uninstallation script. Removes all traces of
#               the Battery Guard project from the system roots.
# ==============================================================================

# Ensure the script is running with root privileges
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] This uninstaller must be run as root. Try: sudo ./uninstall.sh"
   exit 1
fi

echo "----------------------------------------------------"
echo "  Starting Battery Guard Uninstallation - Mohamed Salem"
echo "----------------------------------------------------"

# 1. Stop and Disable Service
echo "[1/3] Terminating background services..."
systemctl stop battery_guard.service 2>/dev/null
systemctl disable battery_guard.service 2>/dev/null

# 2. File and Directory Removal
echo "[2/3] Removing system files and configurations..."
rm -f /etc/systemd/system/battery_guard.service
rm -f /usr/local/bin/battery_guard
rm -rf /etc/battery_guard
rm -f /var/log/battery_guard.log

# 3. Reloading System State
echo "[3/3] Cleaning up systemd state..."
systemctl daemon-reload
systemctl reset-failed

echo "----------------------------------------------------"
echo "  Uninstallation Complete!"
echo "  Battery Guard has been removed from your system."
echo "----------------------------------------------------"