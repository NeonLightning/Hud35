# HUD35 Display System

A Raspberry Pi-based display system that shows weather information and currently playing Spotify tracks on a 480x320 screen. Features automatic background switching based on weather conditions, animated album art, and touch screen controls.

## Features

- **Weather Display**: Shows current weather with location detection (GPS, Google Geolocation, or fallback city)
- **Spotify Integration**: Displays currently playing track with album art and artist images
- **Animated Elements**: Album art and artist images bounce around the screen
- **Touch Controls**: Tap the screen to switch between weather and Spotify views
- **Automatic Backgrounds**: Weather-appropriate background images
- **Optimized Performance**: Efficient framebuffer rendering with caching
- **WiFi Management**: Optional WiFi configuration service for easy network setup

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- 480x320 TFT display connected via SPI
- Touch screen input
- Internet connection
- WiFi adapter (built-in or USB)

## Display Setup (3.5" ILI9486 TFT with Touch)

For setting up the 3.5" ILI9486 TFT display with XPT2046 touch controller:

```bash
sudo apt update
sudo apt install git
git clone https://github.com/Shinigamy19/RaspberryPi3bplus-3.5inch-displayA-ILI9486-MPI3501-XPT2046  
mv RaspberryPi3bplus-3.5inch-displayA-ILI9486-MPI3501-XPT2046 LCD-show
cd LCD-show
chmod +x LCD35-show
sudo ./LCD35-show
```

The system will reboot after installation. The display should now work at the correct resolution (480x320) with touch functionality.

```

The system will reboot after installation. The display should now work at the correct resolution (480x320) with touch functionality.

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd hud35
```

### 2. Install Dependencies
```bash
# Install system packages
sudo apt update
sudo apt install python3-pip python3-evdev python3-numpy python3-pil
sudo pip3 install spotipy --break-system-packages
```

### 3. Spotify API Setup

#### Create a Spotify Developer Application
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in:
   - **App Name**: `HUD35 Display` (or any name you prefer)
   - **App Description**: `Display for showing currently playing tracks`
   - **Redirect URI**: `http://127.0.0.1:8080`
5. Click "Create"
6. Note your **Client ID** and **Client Secret**

#### Configure the Application
1. Copy `config.toml` if it doesn't exist (the script will create one automatically)
2. Edit `config.toml` and add your Spotify credentials:
```toml
[api_keys]
client_id = "your_spotify_client_id_here"
client_secret = "your_spotify_client_secret_here"
redirect_uri = "http://127.0.0.1:8080"
```

### 4. OpenWeatherMap API
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your API key
3. Add to `config.toml`:
```toml
[api_keys]
openweather = "your_openweather_api_key_here"
```

### 5. Google Geolocation API (Optional)
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Geolocation API
3. Create an API key
4. Add to `config.toml`:
```toml
[api_keys]
google_geo = "your_google_geo_api_key_here"
```

### 6. Initial Spotify Authentication

**This step is required before installing as a service:**

```bash
# Run the script manually first
python3 hud35.py
```

The first time you run it:
- A browser window will open for Spotify authorization
- Log in to your Spotify account if prompted
- Grant permission for the app to access your currently playing track
- The script will create a `.spotify_cache` file with your authentication tokens

Once you see weather and/or Spotify information on your display, press `Ctrl+C` to stop the program.

### 7. Install as a Service

```bash
# Make the installer executable and run it
chmod +x install.sh
sudo ./install.sh
```

The installer will:
- Copy all necessary files to `/opt/hud35/`
- Set up the systemd service
- Enable automatic startup
- **Optionally install the WiFi manager service** (if `neonwifi.py` is present)

## WiFi Management Service

The system includes an optional WiFi management service (`neonwifi.py`) that provides:

### Features
- **Web-based WiFi configuration** - Connect to new networks without SSH
- **Automatic AP mode** - Creates access point when no WiFi is available
- **Connection monitoring** - Automatically restores AP if connection is lost
- **Manual network entry** - Enter any SSID and password
- **Periodic health checks** - Verifies internet connectivity every 30 seconds

### Installation
The WiFi service is automatically detected and offered during installation if `neonwifi.py` is present in the folder.

### Usage
1. **Connect to Access Point**: Look for WiFi network `WiFi-Manager` (open network)
2. **Web Interface**: Visit `http://192.168.42.1` in your browser
3. **Enter Credentials**: Submit your WiFi SSID and password
4. **Automatic Connection**: The system will connect and monitor the connection

### Service Management
```bash
# Start WiFi service
sudo systemctl start neonwifi.service

# Stop WiFi service  
sudo systemctl stop neonwifi.service

# Check status
sudo systemctl status neonwifi.service

# View logs
sudo journalctl -u neonwifi.service -f
```

### Dependencies
If installing the WiFi service, additional dependencies are required:
```bash
sudo apt install python3-flask
```

## Configuration

Edit `/opt/hud35/config.toml` after installation:

### Font Settings
You can customize fonts and sizes in the `[fonts]` section.

## Background Images

Place background images in the `bg/` directory. The script uses these files:
- `bg_clear.png` - Clear skies
- `bg_clouds.png` - Cloudy weather
- `bg_rain.png` - Rainy weather
- `bg_snow.png` - Snowy weather
- `bg_storm.png` - Thunderstorms
- `bg_default.png` - Default background
- `no_track.png` - Displayed when no Spotify track is playing

## Usage

### Manual Operation
```bash
python3 hud35.py
```

### Service Management
```bash
# Start HUD35 service
sudo systemctl start hud35.service

# Stop HUD35 service
sudo systemctl stop hud35.service

# Check status
sudo systemctl status hud35.service

# View logs
sudo journalctl -u hud35.service -f
```

### Touch Controls
- **Tap the screen** to switch between weather and Spotify displays

## Uninstallation

```bash
sudo ./uninstall.sh
```

This will remove:
- All application files from `/opt/hud35/`
- The systemd services (both HUD35 and WiFi manager if installed)
- Service configurations

*Note: Python dependencies and your config file will remain.*

### Logs
View detailed logs with:
```bash
# HUD35 logs
sudo journalctl -u hud35.service -f

# WiFi service logs
sudo journalctl -u neonwifi.service -f
```

## File Structure
```
hud35/
├── hud35.py              # Main application
├── neonwifi.py           # WiFi management service (optional)
├── config.toml           # Configuration file
├── install.sh            # Installation script
├── uninstall.sh          # Uninstallation script
├── requirements.txt      # Python dependencies
├── bg/                   # Background images directory
└── README.md            # This file
```

## Troubleshooting

### WiFi Service Issues
- **Can't connect to AP**: Ensure no other services are using the WiFi interface
- **Web interface not loading**: Check if the service is running with `sudo systemctl status neonwifi.service`
- **Connection failures**: Verify NetworkManager is installed and working

### Display Issues
- **Blank screen**: Check SPI interface and power to display
- **Touch not working**: Verify touch controller calibration
- **Wrong resolution**: Ensure proper display drivers are installed

### Spotify Issues
- **Authentication failures**: Delete `.spotify_cache` and re-authenticate
- **No track info**: Verify Spotify is playing and app has proper permissions
```
- Usage guide for connecting to and using the web interface
- Service management commands
- Dependencies specific to the WiFi service
- Troubleshooting section for common WiFi issues
- Enhanced file structure showing the optional neonwifi.py file
