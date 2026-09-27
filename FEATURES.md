# ADB Toolkit Features

## Primary web UI (`python3 server.py` → http://127.0.0.1:8000)

- Device selector (USB + wireless)
- Device info (model, Android/API, battery)
- Package list / uninstall / clear data
- Screen control (tap, text, Home/Back/Power)
- Screenshot preview in the browser
- Shell executor (device `adb shell` only)
- Wireless ADB pair / connect / disconnect
- Logcat snapshot
- Dark / light theme, responsive layout

## REST API

Documented in [API.md](API.md). Health check: `GET /api/health`.

## Optional helpers

- `wireless.py` — CLI wireless pair/connect
- `tools/adb-session-manager.py` — multi-device session summary
- `scripts/adb-device-monitor.sh` — CPU/memory/battery monitor

## ADB requirement

```bash
adb start-server
adb devices
```
