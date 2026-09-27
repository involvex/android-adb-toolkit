#!/usr/bin/env python3
"""Canonical entrypoint for the Android ADB Toolkit web UI + API.

Usage:
    python3 server.py
    python3 server.py --port 8000

Then open: http://127.0.0.1:8000/

Requires: Python 3.8+ and ``adb`` on PATH. No pip packages required for the
server itself (see requirements.txt for optional test deps).
"""

from adb_toolkit.server import main

if __name__ == "__main__":
    raise SystemExit(main())
