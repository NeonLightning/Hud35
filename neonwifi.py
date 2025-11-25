#!/usr/bin/env python3
import subprocess, time, threading, os, signal, sys
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

sys.stdout.reconfigure(line_buffering=True)
app = Flask(__name__)

def load_config():
    try:
        import toml
        config_path = "config.toml"
        if os.path.exists(config_path):
            config = toml.load(config_path)
            wifi_config = config.get("wifi", {})
            ui_config = config.get("ui", {})
            ap_ip = wifi_config.get("ap_ip", "192.168.42.1")
            ap_ssid = wifi_config.get("ap_ssid", "Neonwifi-Manager")
            rescan_time = wifi_config.get("rescan_time", 600)
            theme = ui_config.get("theme", "dark")
            return {
                "ap_ip": ap_ip,
                "ap_ssid": ap_ssid,
                "rescan_time": rescan_time,
                "theme": theme
            }
        else:
            return {
                "ap_ip": "192.168.42.1",
                "ap_ssid": "Neonwifi-Manager",
                "rescan_time": 600,
                "theme": "dark"
            }
    except Exception as e:
        return {
            "ap_ip": "192.168.42.1",
            "ap_ssid": "Neonwifi-Manager",
            "rescan_time": 600,
            "theme": "dark"
        }

config = load_config()
AP_IP = config["ap_ip"]
AP_SSID = config["ap_ssid"]
THEME = config["theme"]
RESCAN_INTERVAL = config["rescan_time"]
WIFI_INTERFACE = "wlan0"
HOSTAPD_CONF = "/tmp/hostapd.conf"
DNSMASQ_CONF = "/tmp/dnsmasq.conf"
SHUTDOWN_FLAG = False
AP_MODE_ACTIVE = False
AP_CREATION_LOCK = threading.Lock()
SCANNED_NETWORKS = []
LAST_SCAN_TIME = None
NEXT_RESCAN_TIME = None

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WiFi Manager</title>
    <style>
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3d3d3d;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --accent-color: #007bff;
            --accent-hover: #0056b3;
            --border-color: #444444;
            --success-bg: #155724;
            --success-border: #c3e6cb;
            --error-bg: #721c24;
            --error-border: #f5c6cb;
            --warning-bg: #856404;
            --warning-border: #ffeaa7;
            --info-bg: #004085;
            --info-border: #b3d7ff;
        }
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --accent-color: #007bff;
            --accent-hover: #0056b3;
            --border-color: #dee2e6;
            --success-bg: #d4edda;
            --success-border: #c3e6cb;
            --error-bg: #f8d7da;
            --error-border: #f5c6cb;
            --warning-bg: #fff3cd;
            --warning-border: #ffeaa7;
            --info-bg: #cce7ff;
            --info-border: #b3d7ff;
        }
        body { 
            font-family: Arial, sans-serif; 
            max-width: 600px; 
            margin: 0 auto; 
            padding: 20px;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.3s ease;
        }
        .container {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
        }
        h1 { 
            text-align: center; 
            color: var(--text-primary);
        }
        .form-group { 
            margin-bottom: 15px; 
        }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold;
            color: var(--text-primary);
        }
        input { 
            width: 100%; 
            padding: 8px; 
            border: 1px solid var(--border-color); 
            border-radius: 4px; 
            box-sizing: border-box;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: var(--accent-color);
            outline: none;
        }
        button { 
            background: var(--accent-color); 
            color: white; 
            border: none; 
            padding: 10px 15px; 
            border-radius: 4px; 
            cursor: pointer; 
            width: 100%; 
            font-size: 16px; 
            margin-top: 10px;
            transition: all 0.3s ease;
        }
        button:hover { 
            background: var(--accent-hover); 
        }
        button.secondary { 
            background: #6c757d; 
            margin-top: 5px; 
        }
        button.secondary:hover { 
            background: #5a6268; 
        }
        .instructions {
            background: var(--info-bg);
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            color: var(--text-primary);
            border: 1px solid var(--info-border);
        }
        .status {
            text-align: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        .status.error { 
            background: var(--error-bg); 
            color: var(--text-primary); 
            border: 1px solid var(--error-border);
        }
        .status.info { 
            background: var(--info-bg); 
            color: var(--text-primary); 
            border: 1px solid var(--info-border);
        }
        .network-list { 
            margin: 20px 0; 
        }
        .network-item { 
            padding: 12px; 
            margin: 8px 0; 
            border: 1px solid var(--border-color); 
            border-radius: 4px; 
            cursor: pointer; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            background: var(--bg-tertiary);
            transition: all 0.3s ease;
        }
        .network-item:hover { 
            background: var(--bg-secondary);
            border-color: var(--accent-color); 
        }
        .network-item.selected { 
            background: var(--info-bg); 
            border-color: var(--accent-color); 
        }
        .network-name { 
            font-weight: bold; 
            color: var(--text-primary);
        }
        .network-signal { 
            color: var(--text-secondary); 
            font-size: 0.9em; 
        }
        .signal-excellent { color: #28a745; }
        .signal-good { color: #ffc107; }
        .signal-fair { color: #fd7e14; }
        .signal-poor { color: #dc3545; }
        .lock-icon { 
            margin-left: 8px; 
        }
        .no-networks { 
            text-align: center; 
            padding: 20px; 
            color: var(--text-secondary); 
            font-style: italic; 
        }
        .manual-entry { 
            margin-top: 15px; 
            padding-top: 15px; 
            border-top: 1px solid var(--border-color); 
        }
        .timer { 
            text-align: center; 
            background: var(--bg-tertiary);
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }
        .timer-warning { 
            background: var(--warning-bg); 
            color: var(--text-primary);
            border: 1px solid var(--warning-border);
        }
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            z-index: 1000;
            width: auto;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        .theme-toggle:hover {
            background: var(--accent-hover);
            transform: scale(1.05);
        }
    </style>
    <script>
        let selectedSSID = '';
        function selectNetwork(ssid, isSecure) {
            selectedSSID = ssid;
            document.querySelectorAll('.network-item').forEach(item => {
                item.classList.remove('selected');
            });
            event.currentTarget.classList.add('selected');
            document.getElementById('ssid').value = ssid;
            document.getElementById('password').focus();
            const passwordGroup = document.getElementById('password-group');
            if (isSecure) {
                passwordGroup.style.display = 'block';
            } else {
                passwordGroup.style.display = 'none';
            }
        }
        function updateTimer() {
            fetch('/timer')
                .then(response => response.json())
                .then(data => {
                    const timerElement = document.getElementById('rescan-timer');
                    const timerContainer = document.getElementById('rescan-timer-container');
                    if (data.next_rescan) {
                        if (data.seconds_left <= 30) {
                            timerElement.textContent = "Reconnect to access point in a short while to try again.";
                            timerContainer.className = 'timer timer-warning';
                        } else {
                            timerElement.textContent = data.next_rescan;
                            if (data.seconds_left < 60) {
                                timerContainer.className = 'timer timer-warning';
                            } else {
                                timerContainer.className = 'timer';
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('Timer update error:', error);
                });
        }
        function toggleTheme() {
            const currentTheme = document.body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-theme', newTheme);
            const button = document.querySelector('.theme-toggle');
            button.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
            localStorage.setItem('wifi-manager-theme', newTheme);
            fetch('/toggle_theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `theme=${newTheme}`
            }).catch(error => {
                console.error('Error saving theme:', error);
            });
        }
        window.onload = function() {
            updateTimer();
            setInterval(updateTimer, 1000);
            const savedTheme = localStorage.getItem('wifi-manager-theme') || '{{ theme }}';
            document.body.setAttribute('data-theme', savedTheme);
            const button = document.querySelector('.theme-toggle');
            button.innerHTML = savedTheme === 'dark' ? '☀️' : '🌙';
        };
    </script>
</head>
<body data-theme="{{ theme }}">
    <button class="theme-toggle" onclick="toggleTheme()">
        {% if theme == 'dark' %}
        ☀️
        {% else %}
        🌙
        {% endif %}
    </button>
    <div class="container">
        <h1>WiFi Manager</h1>
        <div class="instructions">
            <p><strong>Connected to:</strong> {{ ap_ssid }}</p>
            <p>Access Point: <strong>http://{{ ap_ip }}</strong></p>
            <div class="timer" id="rescan-timer-container">
                <p>Next rescan in: <span id="rescan-timer">{{ next_rescan_time }}</span></p>
            </div>
        </div>
        <div class="network-list" id="network-list">
            {% if networks %}
                {% for network in networks %}
                <div class="network-item" onclick="selectNetwork('{{ network.ssid }}', {{ network.secure|lower }})">
                    <div>
                        <span class="network-name">{{ network.ssid }}</span>
                        {% if network.secure %}<span class="lock-icon">🔒</span>{% endif %}
                    </div>
                    <div class="network-signal 
                        {% if network.signal > 75 %}signal-excellent
                        {% elif network.signal > 50 %}signal-good
                        {% elif network.signal > 25 %}signal-fair
                        {% else %}signal-poor{% endif %}">
                        {% if network.signal > 75 %}▂▄▆█
                        {% elif network.signal > 50 %}▂▄▆_
                        {% elif network.signal > 25 %}▂▄__
                        {% else %}▂___{% endif %} {{ network.signal }}%
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-networks">
                    <p>No access points found</p>
                </div>
            {% endif %}
        </div>
        {% if error %}
        <div class="status error">
            <p>❌ {{ error }}</p>
        </div>
        {% endif %}
        <form method="POST" action="/connect">
            <div class="manual-entry">
                <h3>Connect to Network</h3>
                <div class="form-group">
                    <label for="ssid">WiFi SSID:</label>
                    <input type="text" id="ssid" name="ssid" placeholder="Select network or enter manually" required>
                </div>
                <div class="form-group" id="password-group">
                    <label for="password">WiFi Password:</label>
                    <input type="password" id="password" name="password" placeholder="Enter password">
                </div>
                <button type="submit">Connect</button>
            </div>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    global SCANNED_NETWORKS, NEXT_RESCAN_TIME
    next_rescan_str = format_time_remaining(NEXT_RESCAN_TIME) if NEXT_RESCAN_TIME else "Calculating..."
    return render_template_string(
        INDEX_TEMPLATE, 
        ap_ssid=AP_SSID, 
        ap_ip=AP_IP, 
        error=None,
        networks=SCANNED_NETWORKS,
        next_rescan_time=next_rescan_str,
        theme=THEME
    )

@app.route('/toggle_theme', methods=['POST'])
def toggle_theme():
    try:
        import toml
        new_theme = request.form.get('theme', 'dark')
        config_path = "config.toml"
        if os.path.exists(config_path):
            config = toml.load(config_path)
        else:
            config = {}
        if 'ui' not in config:
            config['ui'] = {}
        config['ui']['theme'] = new_theme
        with open(config_path, 'w') as f:
            toml.dump(config, f)
        global THEME
        THEME = new_theme
        return '', 200
    except Exception as e:
        print(f"Error saving theme: {e}")
        return '', 500

@app.route('/timer')
def timer():
    global NEXT_RESCAN_TIME
    if NEXT_RESCAN_TIME:
        seconds_left = max(0, (NEXT_RESCAN_TIME - datetime.now()).total_seconds())
        return jsonify({
            'next_rescan': format_time_remaining(NEXT_RESCAN_TIME),
            'seconds_left': seconds_left
        })
    return jsonify({'next_rescan': 'Calculating...', 'seconds_left': 0})

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form.get('ssid', '').strip()
    password = request.form.get('password', '').strip()
    if not ssid:
        return redirect(url_for('index'))
    if len(ssid) > 32 or len(password) > 63:
        return "<h2>Error</h2><p>Invalid SSID or password length</p>"
    threading.Thread(target=connect_wifi_background, args=(ssid, password), daemon=True).start()
    return "<h2>Connecting...</h2><p>You will lose connection to this interface.</p>"

def format_time_remaining(target_time):
    if not target_time:
        return "Calculating..."
    now = datetime.now()
    if target_time <= now:
        return "00:00"
    diff = target_time - now
    total_seconds = int(diff.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def scan_networks():
    global SCANNED_NETWORKS, LAST_SCAN_TIME
    subprocess.run(['sudo', 'nmcli', 'device', 'set', WIFI_INTERFACE, 'managed', 'yes'], check=False)
    time.sleep(1)
    subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
    time.sleep(2)
    networks = scan_with_nmcli()
    seen = set()
    unique_networks = []
    for net in sorted(networks, key=lambda x: x['signal'], reverse=True):
        if net['ssid'] and net['ssid'] not in seen:
            seen.add(net['ssid'])
            unique_networks.append(net)
    SCANNED_NETWORKS = unique_networks
    LAST_SCAN_TIME = datetime.now()
    return unique_networks

def scan_with_nmcli():
    networks = []
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'NetworkManager'], capture_output=True, text=True)
        if 'inactive' in result.stdout or result.returncode != 0:
            subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
            time.sleep(3)
        result = subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan', 'ifname', WIFI_INTERFACE], check=False, timeout=20, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️ Rescan command failed: {result.stderr}")
        time.sleep(5)
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list', 'ifname', WIFI_INTERFACE], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line and line.strip():
                    parts = line.split(':')
                    if len(parts) >= 3:
                        ssid = parts[0].strip()
                        try:
                            signal = int(parts[1].strip())
                        except:
                            signal = 0
                        security = parts[2].strip()
                        is_secure = bool(security and security != '--')
                        if ssid and ssid != '--':
                            networks.append({
                                'ssid': ssid,
                                'signal': signal,
                                'secure': is_secure
                            })
        else:
            print(f"  ❌ No networks found or command failed")
    except subprocess.TimeoutExpired:
        print("  ❌ Network scan timed out")
    except Exception as e:
        print(f"  ❌ nmcli scan error: {e}")
    return networks

def is_wifi_connected():
    try:
        ip_result = subprocess.run(
            ['ip', '-4', 'addr', 'show', 'dev', WIFI_INTERFACE], 
            capture_output=True, text=True, timeout=5
        )
        has_ip = 'inet' in ip_result.stdout and '127.0.0.1' not in ip_result.stdout
        is_up = 'state UP' in ip_result.stdout
        if not has_ip or not is_up:
            return False
        iw_result = subprocess.run(
            ['iwconfig', WIFI_INTERFACE],
            capture_output=True, text=True, timeout=5
        )
        is_associated = 'Not-Associated' not in iw_result.stdout
        if not is_associated:
            return False
        ping_result = subprocess.run(
            ['ping', '-c', '2', '-W', '3', '-I', WIFI_INTERFACE, '8.8.8.8'],
            capture_output=True, text=True, timeout=10
        )
        internet_available = ping_result.returncode == 0
        if not internet_available:
            dns_result = subprocess.run(
                ['nslookup', '-timeout=3', 'google.com'],
                capture_output=True, text=True, timeout=5
            )
            internet_available = dns_result.returncode == 0
        route_result = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True, text=True, timeout=5
        )
        wifi_is_default = WIFI_INTERFACE in route_result.stdout
        connected = internet_available and wifi_is_default
        return connected
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        return False

def monitor_wifi_connection():
    global SHUTDOWN_FLAG, AP_MODE_ACTIVE
    print("🔍 Starting WiFi connection monitor (checking every 30 seconds)")
    while not SHUTDOWN_FLAG:
        time.sleep(30)
        if SHUTDOWN_FLAG:
            break
        wifi_connected = is_wifi_connected()
        if not wifi_connected and not AP_MODE_ACTIVE:
            print("⚠️ WiFi connection lost - creating access point")
            create_access_point()
        elif wifi_connected and AP_MODE_ACTIVE:
            print("ℹ️ WiFi reconnected while AP mode was active")

def periodic_rescan():
    global SHUTDOWN_FLAG, AP_MODE_ACTIVE, NEXT_RESCAN_TIME
    while not SHUTDOWN_FLAG:
        time.sleep(RESCAN_INTERVAL)
        if SHUTDOWN_FLAG:
            break
        if AP_MODE_ACTIVE:
            cleanup()
            time.sleep(3)
            nm_ready = False
            for i in range(3):
                result = subprocess.run(['sudo', 'systemctl', 'is-active', 'NetworkManager'], capture_output=True, text=True)
                if 'active' in result.stdout:
                    nm_ready = True
                    break
                time.sleep(1)
            if nm_ready:
                subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
                subprocess.run(['sudo', 'nmcli', 'device', 'set', WIFI_INTERFACE, 'managed', 'yes'], check=False)
                time.sleep(2)
                scan_networks()
                print(f"📡 Rescan found {len(SCANNED_NETWORKS)} networks")
                time.sleep(3)
                if not is_wifi_connected():
                    create_access_point()
                else:
                    AP_MODE_ACTIVE = False
            else:
                print("❌ NetworkManager not ready - recreating access point")
                create_access_point()
            NEXT_RESCAN_TIME = datetime.now() + timedelta(seconds=RESCAN_INTERVAL)

def connect_wifi_background(ssid, password):
    global SHUTDOWN_FLAG, AP_MODE_ACTIVE
    if SHUTDOWN_FLAG:
        return
    
    print(f"🔗 Attempting to connect to: {ssid}")
    
    try:
        # Stop AP services
        subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], check=False)
        AP_MODE_ACTIVE = False
        time.sleep(2)
        
        # Ensure NetworkManager is running
        subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
        time.sleep(3)
        
        # Set interface to managed mode
        subprocess.run(['sudo', 'nmcli', 'device', 'set', WIFI_INTERFACE, 'managed', 'yes'], check=False)
        time.sleep(2)
        
        # Clean up interface state
        subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', WIFI_INTERFACE], check=False)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'down'], check=False)
        time.sleep(1)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
        time.sleep(2)
        
        # Wait for NetworkManager to recognize the interface
        print("⏳ Waiting for NetworkManager...")
        for i in range(10):
            result = subprocess.run(['nmcli', 'device', 'status'], capture_output=True, text=True)
            if WIFI_INTERFACE in result.stdout and 'unmanaged' not in result.stdout:
                print("✅ Interface is managed")
                break
            time.sleep(1)
        else:
            print("❌ Interface not managed")
            create_access_point()
            return
        
        # Rescan for networks
        print("📡 Rescanning networks...")
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan', 'ifname', WIFI_INTERFACE], check=False, timeout=15)
        time.sleep(3)
        
        # Delete existing connection to avoid conflicts
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], check=False, capture_output=True)
        time.sleep(1)
        
        # Connect to the network
        print(f"🔌 Connecting to {ssid}...")
        if password:
            connect_cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password, 'ifname', WIFI_INTERFACE]
        else:
            connect_cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'ifname', WIFI_INTERFACE]
        
        result = subprocess.run(
            connect_cmd, 
            capture_output=True, 
            text=True, 
            timeout=45
        )
        
        print(f"Connection output: {result.stdout}")
        if result.stderr:
            print(f"Connection errors: {result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ Successfully connected to {ssid}")
            time.sleep(5)
            
            # Verify connection
            if is_wifi_connected():
                print("🌐 Internet connection verified")
                return  # Success! Don't recreate AP
            else:
                print("❌ Connected but no internet")
        else:
            print(f"❌ Connection failed (code: {result.returncode})")
        
        # If we get here, connection failed
        print("🔄 Recreating access point...")
        create_access_point()
        
    except subprocess.TimeoutExpired:
        print("❌ Connection timed out")
        create_access_point()
    except Exception as e:
        print(f"❌ Connection error: {e}")
        create_access_point()

def create_access_point():
    global SHUTDOWN_FLAG, AP_MODE_ACTIVE, NEXT_RESCAN_TIME
    if SHUTDOWN_FLAG:
        return
    with AP_CREATION_LOCK:
        if AP_MODE_ACTIVE:
            return
        try:
            nm_result = subprocess.run(['sudo', 'systemctl', 'is-active', 'NetworkManager'], capture_output=True, text=True, check=False)
            if nm_result.returncode == 0 and 'active' in nm_result.stdout:
                subprocess.run(['sudo', 'systemctl', 'stop', 'NetworkManager'], check=False)
                time.sleep(2)
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], check=False)
            subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], check=False)
            subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], check=False)
            subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], check=False)
            time.sleep(2)
            subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'down'], check=False)
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', WIFI_INTERFACE], check=False)
            time.sleep(1)
            result = subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                print(f"    ⚠️ Failed to bring interface up: {result.stderr}")
                return
            with open(HOSTAPD_CONF, 'w') as f:
                f.write(f"""interface={WIFI_INTERFACE}
driver=nl80211
ssid={AP_SSID}
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wmm_enabled=0
country_code=US
""")
            ip_parts = AP_IP.split('.')
            network_prefix = '.'.join(ip_parts[0:3])
            with open(DNSMASQ_CONF, 'w') as f:
                f.write(f"""interface={WIFI_INTERFACE}
listen-address={AP_IP}
bind-interfaces
server=8.8.8.8
domain-needed
bogus-priv
dhcp-range={network_prefix}.10,{network_prefix}.100,255.255.255.0,12h
""")
            result = subprocess.run(['sudo', 'ip', 'addr', 'add', f'{AP_IP}/24', 'dev', WIFI_INTERFACE], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                print(f"    ⚠️ Failed to set IP address: {result.stderr}")
            subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.ip_forward=1'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            hostapd_process = subprocess.Popen(['sudo', 'hostapd', HOSTAPD_CONF], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(5)
            hostapd_running = subprocess.run(['pgrep', '-f', 'hostapd'], capture_output=True).returncode == 0
            if not hostapd_running:
                print("❌ hostapd failed to start")
                try:
                    stdout, stderr = hostapd_process.communicate(timeout=1)
                    print(f"hostapd errors: {stderr}")
                except:
                    pass
                subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
                return
            # Start dnsmasq
            print("    Starting dnsmasq...")
            dnsmasq_process = subprocess.Popen(['sudo', 'dnsmasq', '-C', DNSMASQ_CONF], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
            dnsmasq_running = subprocess.run(['pgrep', '-f', 'dnsmasq'], capture_output=True).returncode == 0
            if hostapd_running and dnsmasq_running:
                AP_MODE_ACTIVE = True
                NEXT_RESCAN_TIME = datetime.now() + timedelta(seconds=RESCAN_INTERVAL)
            else:
                print("❌ Failed to start AP services")
                if not dnsmasq_running:
                    print("   - dnsmasq failed to start")
                AP_MODE_ACTIVE = False
                subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
        except Exception as e:
            print(f"❌ AP creation error: {e}")
            import traceback
            traceback.print_exc()
            AP_MODE_ACTIVE = False
            subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
            time.sleep(5)

def cleanup():
    global AP_MODE_ACTIVE
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], check=False)
        subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], check=False)
        time.sleep(1)
        subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
        time.sleep(2)
        subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', WIFI_INTERFACE], check=False)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
        time.sleep(1)
        subprocess.run(['sudo', 'nmcli', 'device', 'set', WIFI_INTERFACE, 'managed', 'yes'], capture_output=True, text=True, check=False)
        time.sleep(1)
        AP_MODE_ACTIVE = False
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)

def signal_handler(sig, frame):
    global SHUTDOWN_FLAG
    print("\n🛑 Shutdown signal received...")
    SHUTDOWN_FLAG = True
    cleanup()
    time.sleep(2)
    sys.exit(0)

def main():
    global SHUTDOWN_FLAG, SCANNED_NETWORKS, NEXT_RESCAN_TIME
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("🚀 Starting WiFi Manager")
    time.sleep(2)
    scan_networks()
    NEXT_RESCAN_TIME = datetime.now() + timedelta(seconds=RESCAN_INTERVAL)
    if not is_wifi_connected():
        cleanup()
        time.sleep(2)
        create_access_point()
    monitor_thread = threading.Thread(target=monitor_wifi_connection, daemon=True)
    monitor_thread.start()
    rescan_thread = threading.Thread(target=periodic_rescan, daemon=True)
    rescan_thread.start()
    def start_flask():
        print("📱 Access the manager at http://{}".format(AP_IP))
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False)
    threading.Thread(target=start_flask, daemon=True).start()
    try:
        while not SHUTDOWN_FLAG:
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == '__main__':
    main()