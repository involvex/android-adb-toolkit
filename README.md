# Android ADB Toolkit

Web-based ADB control panel — manage Android devices from your browser.

## Recommended start (canonical)

```bash
# Requires: Python 3.8+ and `adb` on your PATH
python3 server.py

# Open http://127.0.0.1:8000/
```

The server binds to **127.0.0.1:8000** by default (local only). Override with:

```bash
python3 server.py --host 127.0.0.1 --port 8000
# or: ADB_TOOLKIT_PORT=9000 python3 server.py
```

### Docker (optional)

```bash
docker build -t android-adb-toolkit .
docker run --rm -p 8000:8000 --network host android-adb-toolkit
# On Linux, --network host lets the container use the host ADB server.
# Otherwise mount/forward ADB as appropriate for your setup.
```

## Features

- Device info dashboard (multi-device selector)
- App list / uninstall / clear data
- Screen control (tap, text, keyevents)
- **Screenshot preview in the UI**
- **Shell executor panel** (device shell only; no host shell)
- **Wireless ADB pair / connect / disconnect**
- Logcat snapshot
- Dark / light theme, responsive layout
- JSON REST API with consistent error shapes

## Project layout

| Path | Role |
|------|------|
| `server.py` | **Start here** — launches the web UI + API |
| `adb_toolkit/` | Safe ADB helpers + HTTP server |
| `static/index.html` | Primary web UI |
| `API.md` | REST API reference |
| `tools/`, `scripts/` | Optional CLI helpers |
| `wireless.py` | Wireless ADB CLI |
| `legacy/` | Older duplicate UIs/servers (not supported) |
| `tests/` | Automated tests (mocked ADB) |

## Requirements

- Python 3.8+
- [Android platform-tools](https://developer.android.com/tools/releases/platform-tools) (`adb` in `PATH`)
- Device with USB debugging (or wireless debugging) enabled

No pip packages are required to run the server. For a local install of the package metadata:

```bash
pip install -e .
```

## API (summary)

- `GET /api/health` — server + ADB availability
- `GET /api/devices` — list devices
- `GET /api/device/<serial>/info` — device info
- `GET /api/device/<serial>/packages?type=user\|system\|all`
- `GET /api/device/<serial>/screenshot` — PNG as base64 JSON
- `POST /api/device/<serial>/shell` — `{"command": "..."}`
- `POST /api/device/<serial>/tap|swipe|text|key|clear|uninstall`
- `POST /api/wireless/pair|connect|disconnect`

See [API.md](API.md) for full documentation.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Optional CLI helpers

```bash
python3 wireless.py --list
python3 wireless.py --connect 192.168.1.20 --port 5555
python3 tools/adb-session-manager.py
./scripts/adb-device-monitor.sh --interval 2 --duration 60
```

## Security notes

- Default bind is localhost only.
- ADB is invoked with argument lists (`shell=False`) and timeouts.
- Device serials, package names, and wireless hosts are validated before use.
- The shell panel runs commands **on the device**, not on your computer.

## Legacy files

Older overlapping dashboards and servers live under [`legacy/`](legacy/README.md). Prefer `python3 server.py`.
