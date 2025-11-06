#!/usr/bin/env python3
import subprocess
import time
import threading
import os
import signal
import sys
from flask import Flask, render_template_string, request, redirect, url_for

sys.stdout.reconfigure(line_buffering=True)
app = Flask(__name__)

WIFI_INTERFACE = "wlan0"
AP_IP = "192.168.42.1"
AP_SSID = "WiFi-Manager"
HOSTAPD_CONF = "/tmp/hostapd.conf"
DNSMASQ_CONF = "/tmp/dnsmasq.conf"
SHUTDOWN_FLAG = False
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WiFi Manager</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; margin-top: 10px; }
        button:hover { background: #0056b3; }
        .instructions { background: #e3f2fd; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .status { text-align: center; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WiFi Manager</h1>
        <div class="instructions">
            <p><strong>Connect to this network:</strong></p>
            <p>SSID: <strong>{{ ap_ssid }}</strong> (Open Network)</p>
            <p>Then visit: <strong>http://{{ ap_ip }}</strong></p>
        </div>
        {% if error %}
        <div class="status error">
            <p>❌ {{ error }}</p>
        </div>
        {% endif %}
        <form method="POST" action="/connect">
            <div class="form-group">
                <label for="ssid">WiFi SSID:</label>
                <input type="text" id="ssid" name="ssid" placeholder="Enter your WiFi network name" required>
            </div>
            <div class="form-group">
                <label for="password">WiFi Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter your WiFi password" required>
            </div>
            <button type="submit">Connect</button>
        </form>
        <p style="text-align: center; margin-top: 30px;">
            <strong>To stop this program:</strong><br>
            Press Ctrl+C in the terminal window
        </p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE, ap_ssid=AP_SSID, ap_ip=AP_IP, error=None)

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form.get('ssid')
    password = request.form.get('password')
    if not ssid or not password:
        return redirect(url_for('index'))
    threading.Thread(target=connect_wifi_background, args=(ssid, password), daemon=True).start()
    return "<h2>Connecting...</h2><p>You may lose connection temporarily</p>"

def connect_wifi_background(ssid, password):
    global SHUTDOWN_FLAG
    if SHUTDOWN_FLAG:
        return
    print(f"🔌 Attempting to connect to: {ssid}")
    try:
        subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], check=False)
        time.sleep(1)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'down'], check=False)
        subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', WIFI_INTERFACE], check=False)
        time.sleep(1)
        subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
        time.sleep(2)
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan', 'ifname', WIFI_INTERFACE], check=False, timeout=10)
        time.sleep(2)
        connect_cmd = [
            'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
            'password', password, 'ifname', WIFI_INTERFACE
        ]
        result = subprocess.run(connect_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Connected!")
        else:
            print(f"❌ Connection failed: {result.stderr.strip() or result.stdout.strip()}")
            create_access_point()
    except Exception as e:
        print(f"❌ Connection error: {e}")
        create_access_point()

def create_access_point():
    global SHUTDOWN_FLAG
    if SHUTDOWN_FLAG:
        return
    print("📡 Creating access point...")
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', 'NetworkManager'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], check=False)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'down'], check=False)
        subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', WIFI_INTERFACE], check=False)
        time.sleep(1)
        subprocess.run(['sudo', 'iw', WIFI_INTERFACE, 'set', 'type', '__ap'], check=False)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
        time.sleep(2)
        with open(HOSTAPD_CONF, 'w') as f:
            f.write(f"""
interface={WIFI_INTERFACE}
driver=nl80211
ssid={AP_SSID}
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
country_code=US
""")
        with open(DNSMASQ_CONF, 'w') as f:
            f.write(f"""
interface={WIFI_INTERFACE}
listen-address={AP_IP}
bind-interfaces
server=8.8.8.8
domain-needed
bogus-priv
dhcp-range=192.168.42.10,192.168.42.100,255.255.255.0,12h
""")
        subprocess.run(['sudo', 'ip', 'addr', 'add', f'{AP_IP}/24', 'dev', WIFI_INTERFACE], check=False)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        subprocess.Popen(['sudo', 'hostapd', '-B', HOSTAPD_CONF], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        subprocess.Popen(['sudo', 'dnsmasq', '-C', DNSMASQ_CONF], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print(f"✅ Access point ready! Connect to '{AP_SSID}' at {AP_IP}")
    except Exception as e:
        print(f"❌ AP creation error: {e}")
        cleanup()
        create_access_point()

def cleanup():
    print("🧹 Performing cleanup...")
    try:
        subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], check=False)
        subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], check=False)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'down'], check=False)
        subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', WIFI_INTERFACE], check=False)
        subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=False)
        time.sleep(2)
        subprocess.run(['sudo', 'ip', 'link', 'set', WIFI_INTERFACE, 'up'], check=False)
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️ Cleanup error (non-critical): {e}")

def signal_handler(sig, frame):
    global SHUTDOWN_FLAG
    SHUTDOWN_FLAG = True
    cleanup()
    sys.exit(0)

def main():
    global SHUTDOWN_FLAG
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("🚀 Starting WiFi Manager")
    cleanup()
    create_access_point()

    def start_flask():
        print("✅ Web server starting")
        print("Press Ctrl+C to stop the program")
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
