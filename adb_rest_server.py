#!/usr/bin/env python3
"""
adb_rest_server.py — Local REST API server that exposes ADB as HTTP endpoints
Pair with the bundled dashboard (index.html) or use curl/Postman

Endpoints:
  GET  /devices          — list connected devices
  GET  /device/<serial>  — device info (model, android, battery, etc.)
  POST /device/<serial>/shell — run shell command
  GET  /device/<serial>/apps  — list installed packages
  POST /device/<serial>/install — install APK (multipart upload)
  GET  /device/<serial>/screenshot — capture screen as PNG
  GET  /device/<serial>/logcat — stream logcat (SSE)

Usage:
  python3 adb_rest_server.py           # runs on http://localhost:8765
  python3 adb_rest_server.py --port 9000
"""
import subprocess, json, tempfile, os, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse, base64, re

def adb(*args, serial=None):
    cmd = ['adb']
    if serial: cmd += ['-s', serial]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def get_devices():
    out, _, _ = adb('devices', '-l')
    devices = []
    for line in out.splitlines()[1:]:
        if not line.strip() or 'offline' in line: continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ('device', 'emulator'):
            serial = parts[0]
            props = {k.split(':')[0]: k.split(':')[1] for k in parts[2:] if ':' in k}
            devices.append({'serial': serial, 'status': parts[1], **props})
    return devices

def get_device_info(serial):
    props = {
        'model': 'getprop ro.product.model',
        'brand': 'getprop ro.product.brand',
        'android': 'getprop ro.build.version.release',
        'sdk': 'getprop ro.build.version.sdk',
        'build': 'getprop ro.build.display.id',
        'imei': 'service call iphonesubinfo 1',
    }
    info = {'serial': serial}
    for key, cmd in props.items():
        out, _, _ = adb('shell', cmd, serial=serial)
        info[key] = out.strip()
    
    # Battery
    bat, _, _ = adb('shell', 'dumpsys battery', serial=serial)
    for line in bat.splitlines():
        if 'level:' in line:
            info['battery'] = line.split(':')[1].strip() + '%'
        if 'status:' in line:
            statuses = {1: 'unknown', 2: 'charging', 3: 'discharging', 4: 'not charging', 5: 'full'}
            info['battery_status'] = statuses.get(int(line.split(':')[1].strip()), 'unknown')
    return info

class ADBHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/devices':
            self.send_json({'devices': get_devices()})
        elif re.match(r'^/device/[^/]+$', path):
            serial = path.split('/')[2]
            self.send_json(get_device_info(serial))
        elif re.match(r'^/device/[^/]+/apps$', path):
            serial = path.split('/')[2]
            out, _, _ = adb('shell', 'pm list packages -3', serial=serial)
            pkgs = [l.replace('package:', '') for l in out.splitlines()]
            self.send_json({'packages': pkgs, 'count': len(pkgs)})
        elif re.match(r'^/device/[^/]+/screenshot$', path):
            serial = path.split('/')[2]
            adb('shell', 'screencap -p /data/local/tmp/ss.png', serial=serial)
            adb('pull', '/data/local/tmp/ss.png', '/tmp/ss.png', serial=serial)
            with open('/tmp/ss.png', 'rb') as f:
                img = base64.b64encode(f.read()).decode()
            self.send_json({'image_base64': img, 'format': 'png'})
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if re.match(r'^/device/[^/]+/shell$', path):
            serial = path.split('/')[2]
            cmd = body.get('command', 'echo ok')
            out, err, code = adb('shell', cmd, serial=serial)
            self.send_json({'stdout': out, 'stderr': err, 'returncode': code})
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    parser = argparse.ArgumentParser(description='ADB REST API server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='localhost')
    args = parser.parse_args()
    
    server = HTTPServer((args.host, args.port), ADBHandler)
    print(f"🚀 ADB REST server running at http://{args.host}:{args.port}")
    print("Endpoints: GET /devices | GET /device/<serial> | POST /device/<serial>/shell")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    main()
