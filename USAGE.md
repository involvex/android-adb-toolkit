# Android ADB Toolkit — Usage

## Run the control panel

```bash
python3 server.py
# Open http://127.0.0.1:8000/
```

Requires Python 3.8+ and `adb` on your `PATH`. The server binds to localhost by default.

## What you can do in the UI

- Pick a connected device
- View model / Android version / battery
- List packages; clear or uninstall by package name
- Capture and preview screenshots
- Send taps, text, and keyevents
- Run device shell commands
- Pair/connect wireless debugging
- Stream live logcat (Start/Pause/Clear) with level, tag, and package filters

## API scripting

```bash
curl -s http://127.0.0.1:8000/api/devices
curl -s http://127.0.0.1:8000/api/device/SERIAL/info
curl -s -X POST http://127.0.0.1:8000/api/device/SERIAL/shell \
  -H 'Content-Type: application/json' \
  -d '{"command":"getprop ro.product.model"}'
```

Full reference: [API.md](API.md).

## Security

- Default bind is `127.0.0.1` (not exposed on the LAN)
- No host shell execution; ADB uses argv lists with timeouts
- Commands in the shell panel run on the Android device only
