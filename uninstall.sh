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

# Check if neonwifi is installed
if [ -f "/etc/systemd/system/neonwifi.service" ] || [ -f "/opt/hud35/neonwifi.py" ]; then
    echo "✓ neonwifi service and files"
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

# Stop and disable HUD35 service
echo "Stopping hud35 service..."
sudo systemctl stop hud35.service 2>/dev/null
sudo systemctl disable hud35.service 2>/dev/null

# Stop and disable neonwifi service if installed
if [ "$NEONWIFI_INSTALLED" = true ]; then
    echo "Stopping neonwifi service..."
    sudo systemctl stop neonwifi.service 2>/dev/null
    sudo systemctl disable neonwifi.service 2>/dev/null
fi

# Remove service files
echo "Removing systemd services..."
sudo rm -f /etc/systemd/system/hud35.service
if [ "$NEONWIFI_INSTALLED" = true ]; then
    sudo rm -f /etc/systemd/system/neonwifi.service
fi

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

if [ "$NEONWIFI_INSTALLED" = true ]; then
    echo "neonwifi has been completely removed from your system."
fi

echo ""
echo "Note: Python dependencies were not removed."
echo "To remove them manually:"
echo "  pip3 uninstall spotipy Pillow evdev toml numpy requests"

if [ "$NEONWIFI_INSTALLED" = true ]; then
    echo "  pip3 uninstall flask"
fi

echo "----------------------------------------"