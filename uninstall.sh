#!/bin/bash
echo "HUD35 Uninstaller"

# Check if running as root
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
echo ""

read -p "Are you sure you want to uninstall HUD35? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Starting uninstall..."

# Stop and disable service
echo "Stopping hud35 service..."
sudo systemctl stop hud35.service 2>/dev/null
sudo systemctl disable hud35.service 2>/dev/null

# Remove service file
echo "Removing systemd service..."
sudo rm -f /etc/systemd/system/hud35.service

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed

# Remove application files
echo "Removing application files..."
sudo rm -rf /opt/hud35

echo ""
echo "----------------------------------------"
echo "UNINSTALL COMPLETE"
echo "----------------------------------------"
echo "HUD35 has been completely removed from your system."
echo ""
echo "Note: Python dependencies were not removed."
echo "To remove them manually:"
echo "  pip3 uninstall spotipy Pillow evdev toml numpy requests"
echo "----------------------------------------"
