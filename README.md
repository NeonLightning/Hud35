# HUD35 Display System

A Raspberry Pi-based display system that shows weather information and currently playing Spotify tracks on a 3.5"tft or st7789 display hat mini screen. Features automatic background switching based on weather conditions, animated album art, touch screen controls, and a comprehensive web-based management interface.

![Screenshots](screenshots)


### 🎵 Enhanced Music Statistics & Analytics
- **Comprehensive Tracking**: Automatically logs every song played with timestamps
- **Visual Charts**: Interactive bar charts showing top songs and artists
- **Time Period Filtering**: View statistics for:
  - Last 1 hour
  - Last 12 hours  
  - Last 24 hours
  - Last 1 week
  - All time
- **Real-time Updates**: Statistics update automatically as you listen
- **Data Export**: Song history stored in TOML format for easy analysis

### 🎨 Advanced Display Features
- **Animated Artist Images**: Artist photos bounce around the display alongside album art

### 🎮 Improved Input Controls
- **4-Button GPIO Support**: Physical buttons for enhanced control:
  - **Button A**: Switch to Spotify screen
  - **Button B**: Switch to Weather screen  
  - **Button X**: Reset image positions
  - **Button Y**: Toggle time display on/off
- **Touch Screen**: Tap anywhere to toggle between weather and Spotify views

### ⚙️ Enhanced Configuration & Management
- **Web-Based Configuration UI**: Complete setup via browser interface
- **Real-time Service Control**: Start/stop HUD35 and WiFi manager from web UI
- **Live Log Viewer**: Monitor application logs with color-coded output and live updates
- **Theme Support**: Toggle between light and dark modes in web interface
- **Auto-start Configuration**: Configure which services start automatically on boot

### 🌐 Network & Connectivity
- **Multiple Location Services**: Fallback chain for location detection:
  1. GPSD (hardware GPS)
  2. Google Geolocation API(optional)
  3. OpenWeatherMap Geocoding
  4. Manual fallback city
- **WiFi Management**: Built-in access point mode for easy network configuration
- **Internet Detection**: Smart startup that waits for internet connectivity

### 🎵 Spotify Integration Enhancements
- **Robust Authentication**: Web-based OAuth flow with token refresh
- **Error Recovery**: Automatic reconnection on network errors
- **Artist Image Fetching**: Displays artist photos alongside album art
- **Progress Tracking**: Real-time song progress with formatted time display

## Installation & Setup

### Quick Installation
```bash
# Run the automated installer
chmod +x install.sh
sudo ./install.sh
```

The installer now includes:
- Automatic dependency checking
- Systemd service configuration
- File permissions setup
- Web interface activation

### Web Configuration
After installation, access the web interface:
```bash
http://your-pi-ip:5000
```

## Hardware Support

### Supported Displays
- **ST7789** (DisplayHat Mini)
- **Framebuffer** (Standard TFT 3.5" SPI displays)

### GPIO Button Mapping
The system supports 4 physical buttons connected to GPIO pins:
- Button A: GPIO 5
- Button B: GPIO 6  
- Button X: GPIO 16
- Button Y: GPIO 24

*Configurable via `config.toml`*

## Music Statistics Features

### 📊 Analytics Dashboard
- **Total Plays Counter**: Track how many songs you've played
- **Unique Songs & Artists**: Measure your music diversity
- **Top Charts**: 
  - Most played songs with play counts
  - Most listened-to artists
- **Visual Analytics**: Color-coded bar charts showing listening patterns

## Service Management

### New Web Controls
- **One-click Service Control**: Start/stop HUD35 and WiFi manager
- **Real-time Status**: Live status indicators for all services
- **Log Management**: View and clear application logs

### System Commands
```bash
# Start service
sudo systemctl start hud35.service

# Stop service  
sudo systemctl stop hud35.service

# Check status
sudo systemctl status hud35.service

# View logs
sudo journalctl -u hud35.service -f
```

### Accessing Music Statistics
1. Open web interface: `http://your-pi-ip:5000`
2. Click "Music Statistics" button
3. Select time period and number of items to display
4. View interactive charts of your listening habits

### Using Physical Buttons
- **Quick screen switch**: Press A/B buttons
- **Reset animations**: Press X to reset image positions
- **Toggle clock**: Press Y to show/hide time display

## Troubleshooting
- **Web-based log viewer**: Access logs without terminal
- **Service status indicators**: Visual indicators of service health
- **Auto-recovery**: Services automatically restart on failure
- **Configuration validation**: Web UI validates API keys and settings

## Uninstallation

```bash
sudo /opt/hud35/uninstall.sh
```
