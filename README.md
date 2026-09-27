# Android ADB Toolkit

Web-based ADB control panel — manage Android devices from your browser.

## How to run

### 1. Web UI + API (primary, local device control)

```bash
# Requires: Python 3.8+ and `adb` on your PATH
python3 server.py

# Open http://127.0.0.1:8000/
```

Binds to **127.0.0.1:8000** by default (local only):

```bash
python3 server.py --host 127.0.0.1 --port 8000
# or: ADB_TOOLKIT_PORT=9000 python3 server.py
```

### 2. Command Finder PWA (GitHub Pages)

Installable docs app for browsing/searching ADB + toolkit commands (offline-capable):

**https://involvex.github.io/android-adb-toolkit/**

```bash
# Local preview of the Pages app
python3 -m http.server 5500 --directory docs
# → http://127.0.0.1:5500/
```

Source: [`docs/`](docs/README.md). Deployed from `docs/` via GitHub Actions (`.github/workflows/deploy.yml`).

### 3. Python CLI

```bash
python3 -m adb_toolkit devices
python3 -m adb_toolkit info
python3 -m adb_toolkit packages --type user
python3 -m adb_toolkit shell "getprop ro.product.model"
python3 -m adb_toolkit screenshot -o screen.png
python3 -m adb_toolkit install app.apk

# Equivalent shims: python3 cli.py …   /   python3 adb-cli.py …
```

### 4. Optional Node CLI

```bash
cd cli && npm install && npm link
adb-toolkit info
adb-toolkit screenshot -o screen.png
```

See [`cli/README.md`](cli/README.md).

### Docker (optional)

```bash
docker build -t android-adb-toolkit .
docker run --rm -p 8000:8000 --network host android-adb-toolkit
# On Linux, --network host lets the container use the host ADB server.
```

## Features

- Device info dashboard (multi-device selector)
- App list / uninstall / clear data
- Screen control (tap, text, keyevents)
- Screenshot preview in the UI
- Shell executor panel (device shell only; no host shell)
- Wireless ADB pair / connect / disconnect
- Live logcat streaming (SSE) with level/tag/package filters
- Dark / light theme, responsive layout
- JSON REST API with consistent error shapes

## Project layout

| Path | Role |
|------|------|
| `server.py` | **Primary** — local web UI + API |
| `adb_toolkit/` | Safe ADB helpers, HTTP server, **Python CLI** |
| `static/index.html` | Primary local web UI |
| `docs/` | **GitHub Pages PWA** — command finder |
| `cli/` | Optional Node CLI (`adb-toolkit`) |
| `wireless.py` | Wireless ADB CLI helper |
| `tools/`, `scripts/` | Specialized helpers |
| `API.md` | REST API reference |
| `legacy/` | Deprecated UIs / servers / root CLI copies |
| `tests/` | Automated tests (mocked ADB) |

## Requirements

- Python 3.8+
- [Android platform-tools](https://developer.android.com/tools/releases/platform-tools) (`adb` in `PATH`)
- Device with USB debugging (or wireless debugging) enabled

No pip packages are required to run the server. Optional editable install:

```bash
pip install -e .
# then: adb-toolkit devices   /   adb-toolkit-server
```

## API (summary)

- `GET /api/health` — server + ADB availability
- `GET /api/devices` — list devices
- `GET /api/device/<serial>/info` — device info
- `GET /api/device/<serial>/packages?type=user\|system\|all`
- `GET /api/device/<serial>/screenshot` — PNG as base64 JSON
- `GET /api/device/<serial>/logcat/stream` — live logcat (SSE)
- `POST /api/device/<serial>/shell` — `{"command": "..."}`
- `POST /api/device/<serial>/tap|swipe|text|key|clear|uninstall`
- `POST /api/wireless/pair|connect|disconnect`

See [API.md](API.md) for full documentation.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Other helpers

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

Older overlapping dashboards, servers, and root CLI duplicates live under [`legacy/`](legacy/README.md) (including [`legacy/cli/`](legacy/cli/README.md)). Prefer `python3 server.py` and `python3 -m adb_toolkit`.
