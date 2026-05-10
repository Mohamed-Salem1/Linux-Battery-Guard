#!/bin/bash

# ==============================================================================
# Project     : Battery Guard (Native Integration)
# Author      : Mohamed Salem
# Date        : May 2026
# Description : Professional installation script for Ubuntu/Debian systems.
#               Handles Systemd orchestration and DBUS environment bridging.
# ==============================================================================

# Ensure the script is running with root privileges
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] This installer must be run as root. Try: sudo ./install.sh"
   exit 1
fi

# Fetching the real user's ID to bridge Root Service with User GUI/Audio
REAL_USER_ID=$(id -u $SUDO_USER)

echo "----------------------------------------------------"
echo "  Starting Battery Guard Installation - Mohamed Salem"
echo "----------------------------------------------------"

# 1. Directory Initialization
echo "[1/5] Initializing system directories..."
mkdir -p /etc/battery_guard
touch /var/log/battery_guard.log
chmod 666 /var/log/battery_guard.log

# 2. Deploying the Engine
echo "[2/5] Deploying source code to /usr/local/bin..."
if [ -f "battery_guard.py" ]; then
    cp battery_guard.py /usr/local/bin/battery_guard
    chmod +x /usr/local/bin/battery_guard
else
    echo "[CRITICAL] battery_guard.py not found in current directory!"
    exit 1
fi

# 3. Systemd Service Orchestration (With GUI/Audio Bridge)
echo "[3/5] Orchestrating Systemd Service..."
cat <<EOF > /etc/systemd/system/battery_guard.service
[Unit]
Description=Battery Guard Health Monitor Daemon
After=multi-user.target network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/battery_guard
Restart=always
RestartSec=10
User=root

# Bridging Root Service to User Session for Notifications and Audio
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$REAL_USER_ID/bus
Environment=XDG_RUNTIME_DIR=/run/user/$REAL_USER_ID

[Install]
WantedBy=multi-user.target
EOF

# 4. Service Activation
echo "[4/5] Enabling and starting the daemon..."
systemctl daemon-reload
systemctl enable battery_guard.service
systemctl restart battery_guard.service

# 5. Finalizing
echo "[5/5] Finalizing deployment..."
echo "----------------------------------------------------"
echo "  Installation Successful!"
echo "  - Config: /etc/battery_guard/config.json"
echo "  - Logs  : /var/log/battery_guard.log"
echo "  - Status: systemctl status battery_guard.service"
echo "----------------------------------------------------"