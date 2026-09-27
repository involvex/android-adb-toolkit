# Legacy entrypoints

These files are **kept for reference** but are **not** the supported way to run the toolkit.

## Canonical path (use this)

```bash
python3 server.py
# → http://127.0.0.1:8000/
```

Primary code lives in:

- `adb_toolkit/` — ADB helpers + HTTP API
- `static/index.html` — web UI
- `server.py` — launcher

## What moved here

| File | Why deprecated |
|------|----------------|
| `web-ui.html`, `web-ui-v2.html`, `web-dashboard.html`, `dashboard.html` | Overlapping UIs pointed at different/missing backends |
| `index.html` | Static cheatsheet only (no live API) |
| `adb_rest_server.py`, `api_server.py`, `web-ui.py`, `server.js` | Alternate servers with inconsistent ports/routes |
| `pm-helper.py` | Empty stub |
| Other assorted HTML helpers | Superseded by `static/index.html` panels |

CLI helpers under `tools/`, `scripts/`, and root utilities such as `wireless.py` remain supported as optional scripts — see the main README.

Root shims (`adb_rest_server.py`, `adb-session-manager.py`) print a deprecation notice and forward to the canonical entrypoints.
