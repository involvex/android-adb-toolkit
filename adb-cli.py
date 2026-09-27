#!/usr/bin/env python3
"""Deprecated shim — use ``python3 -m adb_toolkit`` (or ``python3 cli.py``).

Previous implementation: ``legacy/cli/adb-cli.py``.
"""

import sys
import warnings

warnings.warn(
    "adb-cli.py is deprecated; use: python3 -m adb_toolkit",
    DeprecationWarning,
    stacklevel=1,
)
print(
    "NOTE: adb-cli.py is deprecated. Prefer: python3 -m adb_toolkit <command>\n",
    file=sys.stderr,
)
from adb_toolkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
