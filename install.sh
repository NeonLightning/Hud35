#!/bin/bash
echo "HUD35 Display Service Installer"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check for Spotify authentication
if [ ! -f ".spotify_cache" ]; then
    echo ""
    echo "❌ SPOTIFY SETUP REQUIRED FIRST"
    echo "----------------------------------------"
    echo "You must set up Spotify authentication before installing."
    echo ""
    echo "Run the program manually from the current folder first:"
    echo "  python3 hud35.py"
    echo ""
    echo "This will:"
    echo "• Open a browser for Spotify authorization"
    echo "• Create the .spotify_cache file"
    echo "• Allow the service to access your Spotify account"
    echo ""
    echo "After Spotify is set up (you see music info on screen),"
    echo "press Ctrl+C to stop the program, then run the installer again."
    echo "----------------------------------------"
    exit 1
fi

# Check if already installed
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

# Check if neonwifi.py exists and offer to install it
INSTALL_NEONWIFI="n"
if [ -f "neonwifi.py" ]; then
    echo ""
    echo "📶 NEONWIFI DETECTED"
    echo "----------------------------------------"
    echo "Found neonwifi.py - WiFi Manager for easy network setup"
    read -p "Do you want to install neonwifi as a service? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        INSTALL_NEONWIFI="y"
        echo "✓ Will install neonwifi service"
    else
        echo "ℕ Skipping neonwifi installation"
    fi
fi

# Copy files
echo ""
echo "Copying files to /opt/hud35..."
sudo mkdir -p /opt/hud35/bg
sudo cp hud35.py /opt/hud35/

# Copy neonwifi if requested
if [ "$INSTALL_NEONWIFI" = "y" ]; then
    sudo cp neonwifi.py /opt/hud35/
    echo "✓ neonwifi.py copied"
fi

# Copy config.toml if it exists
if [ -f "config.toml" ]; then
    sudo cp config.toml /opt/hud35/
    echo "✓ config.toml copied"
else
    echo "ℹ No config.toml found, using defaults"
fi

# Copy .spotify_cache (we know it exists because of the check above)
sudo cp .spotify_cache /opt/hud35/
echo "✓ .spotify_cache copied (Spotify authentication)"
sudo cp uninstall.sh /opt/hud35
echo "✓ copied uninstall.sh"

# Copy background images if they exist
if [ -d "bg" ] && [ "$(ls -A bg 2>/dev/null)" ]; then
    sudo cp bg/* /opt/hud35/bg/
    echo "✓ Background images copied"
else
    echo "ℹ No background images found"
fi

# Show dependency instructions
echo ""
echo "----------------------------------------"
echo "PYTHON DEPENDENCIES REQUIRED"
echo "----------------------------------------"
echo "Before running HUD35, install the required dependencies:"
echo ""
echo "sudo apt update"
echo "sudo apt install python3-pip python3-evdev python3-numpy python3-pil"
echo "sudo pip3 install spotipy --break-system-packages"

# Additional dependencies for neonwifi if installed
if [ "$INSTALL_NEONWIFI" = "y" ]; then
    echo "sudo apt install python3-flask"
fi

read -p "Press Enter to continue with installation..."

# Create HUD35 service file
echo ""
echo "Creating HUD35 systemd service..."
sudo tee /etc/systemd/system/hud35.service > /dev/null <<EOF
[Unit]
Description=HUD35 Display Service
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hud35
ExecStart=/usr/bin/python3 /opt/hud35/hud35.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Create neonwifi service file if requested
if [ "$INSTALL_NEONWIFI" = "y" ]; then
    echo "Creating neonwifi systemd service..."
    sudo tee /etc/systemd/system/neonwifi.service > /dev/null <<EOF
[Unit]
Description=NeonWiFi Manager Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hud35
ExecStart=/usr/bin/python3 /opt/hud35/neonwifi.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
fi

# Set permissions
sudo chmod +x /opt/hud35/hud35.py
if [ "$INSTALL_NEONWIFI" = "y" ]; then
    sudo chmod +x /opt/hud35/neonwifi.py
fi
sudo chown -R root:root /opt/hud35

# Enable services
sudo systemctl daemon-reload

# Start HUD35 service
sudo systemctl enable hud35.service
sudo systemctl start hud35.service

# Start neonwifi service if installed
if [ "$INSTALL_NEONWIFI" = "y" ]; then
    sudo systemctl enable neonwifi.service
    sudo systemctl start neonwifi.service
fi

echo ""
echo "----------------------------------------"
echo "INSTALLATION COMPLETE"
echo "----------------------------------------"
echo ""
echo "✓ Spotify authentication was copied"
echo "✓ HUD35 service is installed and enabled"

if [ "$INSTALL_NEONWIFI" = "y" ]; then
    echo "✓ neonwifi service is installed and enabled"
    echo ""
    echo "NEONWIFI ACCESS:"
    echo "  Connect to WiFi: 'WiFi-Manager' (open network)"
    echo "  Visit: http://192.168.42.1"
    echo "  To stop neonwifi: sudo systemctl stop neonwifi.service"
fi

echo ""
echo "NEXT STEPS:"
if [ ! -f "config.toml" ]; then
    echo "1. Edit /opt/hud35/config.toml with your API keys (if needed)"
fi
echo "1. Install Python dependencies (see above)"
echo "2. Check service status with commands below"
echo ""
echo "MANAGEMENT COMMANDS:"
echo "  HUD35 Start:  sudo systemctl start hud35.service"
echo "  HUD35 Stop:   sudo systemctl stop hud35.service"
echo "  HUD35 Status: sudo systemctl status hud35.service"
echo "  HUD35 Logs:   sudo journalctl -u hud35.service -f"

if [ "$INSTALL_NEONWIFI" = "y" ]; then
    echo ""
    echo "  NeonWiFi Start:  sudo systemctl start neonwifi.service"
    echo "  NeonWiFi Stop:   sudo systemctl stop neonwifi.service"
    echo "  NeonWiFi Status: sudo systemctl status neonwifi.service"
    echo "  NeonWiFi Logs:   sudo journalctl -u neonwifi.service -f"
fi

echo ""
echo "To uninstall: sudo /opt/hud35/uninstall.sh"
echo "----------------------------------------"