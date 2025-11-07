#!/bin/bash
echo "HUD35 Service Installer"
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi
if [ -f "/etc/systemd/system/hud35.service" ]; then
    echo "⚠ HUD35 appears to be already installed."
    read -p "Do you want to reinstall? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "Reinstalling..."
fi
echo ""
echo "Copying files to /opt/hud35..."
sudo mkdir -p /opt/hud35/bg
sudo cp hud35.py /opt/hud35/
sudo cp launcher.py /opt/hud35/
if [ -f "neonwifi.py" ]; then
    sudo cp neonwifi.py /opt/hud35/
    echo "✓ neonwifi.py copied"
fi
if [ -f "config.toml" ]; then
    sudo cp config.toml /opt/hud35/
    echo "✓ config.toml copied"
else
    echo "ℹ No config.toml found, using defaults"
    sudo cp /dev/null /opt/hud35/config.toml
fi
if [ -f ".spotify_cache" ]; then
    sudo cp .spotify_cache /opt/hud35/
    echo "✓ .spotify_cache copied (Spotify authentication)"
else
    echo "ℹ No .spotify_cache found - setup via web UI after installation"
fi
sudo cp uninstall.sh /opt/hud35/
echo "✓ uninstall.sh copied"
if [ -d "bg" ] && [ "$(ls -A bg 2>/dev/null)" ]; then
    sudo cp bg/* /opt/hud35/bg/
    echo "✓ Background images copied"
else
    echo "ℹ No background images found"
fi
echo ""
echo "----------------------------------------"
echo "PYTHON DEPENDENCIES REQUIRED"
echo "----------------------------------------"
echo "Before running HUD35, install the required dependencies:"
echo ""
echo "sudo apt update"
echo "sudo apt install python3-pip python3-evdev python3-numpy python3-pil python3-flask python3-toml"
echo "sudo pip3 install spotipy --break-system-packages"
read -p "Press Enter to continue with installation..."
echo ""
echo "Creating HUD35 systemd service..."
sudo tee /etc/systemd/system/hud35.service > /dev/null <<EOF
[Unit]
Description=HUD35 Launcher Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hud35
ExecStart=/usr/bin/python3 /opt/hud35/launcher.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
sudo chmod +x /opt/hud35/launcher.py
sudo chmod +x /opt/hud35/hud35.py
if [ -f "/opt/hud35/neonwifi.py" ]; then
    sudo chmod +x /opt/hud35/neonwifi.py
fi
sudo chmod +x /opt/hud35/uninstall.sh
sudo chown -R root:root /opt/hud35
sudo systemctl daemon-reload
sudo systemctl enable hud35.service
sudo systemctl start hud35.service
echo ""
echo "----------------------------------------"
echo "INSTALLATION COMPLETE"
echo "----------------------------------------"
echo ""
echo "✓ HUD35 Launcher service is installed and enabled"
echo "✓ Manages both HUD35 display and neonwifi automatically"
echo "✓ Web configuration UI available"
if [ -f "/opt/hud35/neonwifi.py" ]; then
    echo "✓ neonwifi is available (managed by launcher)"
    echo ""
    echo "NEONWIFI ACCESS:"
    echo "  If no internet is detected, connect to: 'WiFi-Manager'"
    echo "  Then visit: http://192.168.42.1"
fi
echo ""
echo "WEB UI ACCESS:"
echo "  Visit: http://127.0.0.1:5000"
echo "  Configure auto-start settings and API keys"
echo ""
echo "MANAGEMENT COMMANDS:"
echo "  Launcher Start:  sudo systemctl start hud35-launcher.service"
echo "  Launcher Stop:   sudo systemctl stop hud35-launcher.service"
echo "  Launcher Status: sudo systemctl status hud35-launcher.service"
echo "  Launcher Logs:   sudo journalctl -u hud35-launcher.service -f"
echo ""
echo "NEXT STEPS:"
echo "1. Install Python dependencies (see above)"
echo "2. Visit http://127.0.0.1:5000 to complete setup"
echo "3. Configure API keys and auto-start preferences"
echo ""
echo "To uninstall: sudo /opt/hud35/uninstall.sh"
echo "----------------------------------------"