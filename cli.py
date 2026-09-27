#!/usr/bin/env python3
"""Canonical CLI shim — prefer ``python3 -m adb_toolkit``.

Older root CLIs lived here; see ``legacy/cli/``.
"""

from adb_toolkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
