# Legacy CLI entrypoints

Near-identical root CLIs (Python / JS / TS) were moved here so the
supported entrypoints stay obvious.

## Use these instead

| Goal | Command |
|------|---------|
| Web UI + API | `python3 server.py` |
| Python CLI | `python3 -m adb_toolkit devices` (also `python3 cli.py`) |
| Wireless ADB | `python3 wireless.py --list` |
| Node CLI | `cd cli && npm install && npm link` → `adb-toolkit info` |
| Specialized scripts | `tools/`, `scripts/` |

## What lived at the repo root

| File | Notes |
|------|-------|
| `cli.py` | Device info / install / list-apps / debloat (used `shell=True`) |
| `cli.js` / `cli.ts` | Overlapping Node/TS CLIs |
| `adb-cli.py` / `adb-cli.js` / `adb-cli-ts.ts` | More overlapping shortcuts + interactive hints |
| `adb-wrapper.py` | install / screenshot / logcat |
| `adb-shell.js` | Tiny shell helper |
| `adb-client.ts` | Deno-oriented client library experiment |
| `adb-toolkit` | Bash dispatcher pointing at missing scripts |

Root still has **thin shims** (`cli.py`, `adb-cli.py`, `cli.js`, …) that forward
or print a deprecation notice.

Unique bits worth browsing here if you need them: list-file debloat
(`cli.js`), `pull-apks` / `top-apps` (`adb-cli.js`), interactive hint REPL
(`adb-cli-ts.ts`), Facebook-suite debloat list (`cli.py`).
