#!/bin/bash
echo "HUD35 Uninstaller"
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi
echo ""
echo "This will remove:"
echo "-----------------"
echo "✓ /opt/hud35/ (all files)"
echo "✓ /etc/systemd/system/hud35.service"
echo "✓ Systemd service configuration"
if [ -f "/opt/hud35/neonwifi.py" ]; then
    echo "✓ neonwifi files"
    NEONWIFI_INSTALLED=true
else
    NEONWIFI_INSTALLED=false
fi
echo ""
read -p "Are you sure you want to uninstall HUD35? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi
echo ""
echo "Starting uninstall..."
echo "Stopping hud35-launcher service..."
sudo systemctl stop hud35.service 2>/dev/null
sudo systemctl disable hud35.service 2>/dev/null
echo "Removing systemd services..."
sudo rm -f /etc/systemd/system/hud35.service
sudo systemctl daemon-reload
sudo systemctl reset-failed
echo "Removing application files..."
sudo rm -rf /opt/hud35
echo ""
echo "----------------------------------------"
echo "UNINSTALL COMPLETE"
echo "----------------------------------------"
echo "HUD35 Launcher has been completely removed from your system."
if [ "$NEONWIFI_INSTALLED" = true ]; then
    echo "neonwifi has been completely removed from your system."
fi
echo ""
echo "Note: Python dependencies were not removed."
echo "----------------------------------------"