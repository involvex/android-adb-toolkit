# Legacy entrypoints

These files are **kept for reference** but are **not** the supported way to run the toolkit.

## Canonical paths (use these)

```bash
# Web UI + API
python3 server.py
# → http://127.0.0.1:8000/

# Python CLI (safe helpers)
python3 -m adb_toolkit devices
python3 -m adb_toolkit info

# Optional Node CLI
cd cli && npm install && npm link
adb-toolkit info
```

Primary code lives in:

- `adb_toolkit/` — ADB helpers, HTTP API, Python CLI
- `static/index.html` — web UI
- `server.py` — web launcher
- `cli/` — optional Node CLI package
- `tools/`, `scripts/`, `wireless.py` — specialized helpers

## What moved here

### Web / servers (`legacy/`)

| File | Why deprecated |
|------|----------------|
| `web-ui.html`, `web-ui-v2.html`, `web-dashboard.html`, `dashboard.html` | Overlapping UIs pointed at different/missing backends |
| `index-cheatsheet.html` | Static cheatsheet only (no live API) |
| `adb_rest_server.py`, `api_server.py`, `web-ui.py`, `server.js` | Alternate servers with inconsistent ports/routes |
| `pm-helper.py` | Empty stub |

### Root CLI maze (`legacy/cli/`)

Near-duplicate Python/JS/TS CLIs (`cli.py`, `cli.js`, `adb-cli.*`, …). See [`cli/README.md`](cli/README.md).

Root may still contain **thin shims** that forward to `python3 -m adb_toolkit` or print a deprecation notice.
