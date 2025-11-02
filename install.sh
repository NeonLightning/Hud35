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

# Copy files
echo "Copying files to /opt/hud35..."
sudo mkdir -p /opt/hud35/bg
sudo cp hud35.py /opt/hud35/

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
if [ -f "requirements.txt" ]; then
    echo "Using pip:"
    echo "  pip3 install -r requirements.txt"
    echo ""
    echo "Or using apt (on Debian/Ubuntu):"
    echo "  apt update"
    echo "  apt install python3-requests python3-spotipy python3-pil python3-evdev python3-toml python3-numpy"
else
    echo "Required packages:"
    echo "  requests, spotipy, Pillow, evdev, toml, numpy"
    echo ""
    echo "Install with pip:"
    echo "  pip3 install requests spotipy Pillow evdev toml numpy"
    echo ""
    echo "Or using apt (on Debian/Ubuntu):"
    echo "  apt update"
    echo "  apt install python3-requests python3-spotipy python3-pil python3-evdev python3-toml python3-numpy"
fi
echo "----------------------------------------"
echo ""

read -p "Press Enter to continue with installation..."

# Create service file
echo ""
echo "Creating systemd service..."
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

# Set permissions
sudo chmod +x /opt/hud35/hud35.py
sudo chown -R root:root /opt/hud35

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable hud35.service
sudo systemctl start hud35.service

echo ""
echo "----------------------------------------"
echo "INSTALLATION COMPLETE"
echo "----------------------------------------"
echo ""
echo "✓ Spotify authentication was copied"
echo "✓ Service is installed and enabled"
echo ""
echo "NEXT STEPS:"
if [ ! -f "config.toml" ]; then
    echo "1. Edit /opt/hud35/config.toml with your API keys (if needed)"
fi
echo "1. Install Python dependencies (see above)"
echo "2. Start the service: sudo systemctl start hud35.service"
echo ""
echo "MANAGEMENT COMMANDS:"
echo "  Start:  sudo systemctl start hud35.service"
echo "  Stop:   sudo systemctl stop hud35.service"
echo "  Status: sudo systemctl status hud35.service"
echo "  Logs:   sudo journalctl -u hud35.service -f"
echo ""
echo "To uninstall: sudo ./uninstall.sh"
echo "----------------------------------------"
