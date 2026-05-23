# 🤖 Android ADB Toolkit

Web-based ADB control panel — manage Android devices directly from your browser.

## Features

- ✅ Device info dashboard
- ✅ App install/uninstall/clear
- ✅ Permission manager
- ✅ Settings editor
- ✅ Screen control (tap, swipe, text input)
- ✅ File transfer
- ✅ Logcat viewer
- ✅ Battery & system info
- ✅ Multiple device support

## Quick Start

```bash
# Build the web UI
python3 server.py

# Open in browser
# http://localhost:8000
```

## Requirements

- Python 3.7+
- ADB in PATH
- Device connected via USB with debugging enabled

## API Endpoints

- `GET /api/devices` — list connected devices
- `GET /api/device/<serial>/info` — device info
- `GET /api/device/<serial>/packages` — installed apps
- `POST /api/device/<serial>/install` — install APK
- `POST /api/device/<serial>/tap` — tap screen
- `POST /api/device/<serial>/swipe` — swipe gesture
- `GET /api/device/<serial>/logcat` — live logcat stream

See [API.md](API.md) for full endpoint documentation.

## Android Config Monitor (Go)
Real-time device configuration snapshot.

```bash
go run android-config-monitor.go --json
```

Features:
- Real-time device properties
- Settings snapshot (ADB, WiFi, Bluetooth, Airplane mode)
- Build info (Android version, API level, security patch)
- JSON output support


## adb-device-monitor.sh
Real-time device performance monitor: CPU, memory, battery, thermal, and process tracking.

**Usage:**
```bash
./scripts/adb-device-monitor.sh --interval 2 --duration 60
```


## 🔧 Advanced Tools

### ADB Session Manager
**File:** `tools/adb-session-manager.py` (Python)

Monitor and manage multiple concurrent ADB sessions with detailed device profiling.

**Features:**
- Discover all connected devices (USB + Wireless)
- Get device info: model, Android version, battery level
- Track active port forwarding
- Export session data to JSON
- Verbose logging for troubleshooting

**Usage:**
```bash
python3 tools/adb-session-manager.py              # Print session summary
python3 tools/adb-session-manager.py -v           # Verbose output
python3 tools/adb-session-manager.py -j sessions.json  # Export to JSON
```

**Example Output:**
```
🔌 ADB Session Summary
================================================================================

📱 Pixel 7 (emulator-5554)
   Status:        connected
   Android:       14.0
   Battery:       85%
   Connection:    usb
   Ports:         5555, 8080, 9999
```

