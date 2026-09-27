#!/usr/bin/env python3
"""Deprecated shim — use tools/adb-session-manager.py."""
import runpy
import sys
import warnings

warnings.warn(
    "Use tools/adb-session-manager.py",
    DeprecationWarning,
    stacklevel=1,
)
sys.argv[0] = "tools/adb-session-manager.py"
runpy.run_path("tools/adb-session-manager.py", run_name="__main__")
