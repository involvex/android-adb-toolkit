# ADB Toolkit Features

## Command Finder PWA (GitHub Pages)

- Installable offline-capable app at `docs/`
- Searchable catalog of **280+** curated ADB + toolkit commands with copy-to-clipboard
- Categories include connection, packages, activity, logcat/debug, network, settings, emulator, and more
- URL: https://involvex.github.io/android-adb-toolkit/

## Primary web UI (`python3 server.py` → http://127.0.0.1:8000)

- Device selector (USB + wireless)
- Device info (model, Android/API, battery)
- Package list / uninstall / clear data
- Screen control (tap, text, Home/Back/Power)
- Screenshot preview in the browser
- Shell executor (device `adb shell` only)
- Wireless ADB pair / connect / disconnect
- Live logcat streaming (SSE) with level / tag / package filters
- Dark / light theme, responsive layout

## REST API

Documented in [API.md](API.md). Health check: `GET /api/health`.

## Local setup

- `bun setup.ts` (or `python3 setup.py`) — verify Python/layout/`adb`, print start URL

## CLI

- `python3 -m adb_toolkit` — canonical Python CLI (devices, info, packages, shell, screenshot, install)
- `cli/` — optional Node CLI (`adb-toolkit` after `npm link`)
- `wireless.py` — wireless pair/connect
- `tools/`, `scripts/` — specialized helpers
- `legacy/cli/` — deprecated root CLI duplicates

## ADB requirement

```bash
adb start-server
adb devices
```
