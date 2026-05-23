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

