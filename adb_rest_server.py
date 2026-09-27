#!/usr/bin/env python3
"""Deprecated shim — use ``python3 server.py`` instead.

The REST API now lives at http://127.0.0.1:8000/api/...
See API.md and legacy/README.md.
"""
import sys
import warnings

warnings.warn(
    "adb_rest_server.py is deprecated; run: python3 server.py",
    DeprecationWarning,
    stacklevel=1,
)
print(
    "NOTE: adb_rest_server.py is deprecated.\n"
    "Starting the canonical server instead (python3 server.py).\n"
    "Legacy copy: legacy/adb_rest_server.py\n",
    file=sys.stderr,
)
from adb_toolkit.server import main

if __name__ == "__main__":
    raise SystemExit(main())
