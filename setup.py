#!/usr/bin/env python3
"""Fallback setup script (no Bun required).

Preferred:  bun setup.ts
Fallback:   python3 setup.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8000/"


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def warn(msg: str) -> None:
    print(f"  ! {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)


def check_python() -> bool:
    if sys.version_info < (3, 8):
        fail(
            f"Python 3.8+ required "
            f"(found {sys.version_info.major}.{sys.version_info.minor})"
        )
        return False
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_adb() -> bool:
    adb = shutil.which(os.environ.get("ADB_PATH", "adb"))
    if not adb:
        warn("adb not found on PATH")
        print()
        print("    Install Android platform-tools, then re-run setup:")
        print("      macOS:   brew install android-platform-tools")
        print("      Windows: winget install Google.PlatformTools")
        print("      Debian:  sudo apt install adb")
        print(
            "      Or:      "
            "https://developer.android.com/tools/releases/platform-tools"
        )
        print()
        return False
    try:
        out = subprocess.run(
            [adb, "version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        line = (out.stdout or out.stderr or "adb").strip().splitlines()[0]
        ok(line)
    except (OSError, subprocess.TimeoutExpired) as exc:
        warn(f"adb found but could not run: {exc}")
        return False
    return True


def check_tree() -> bool:
    required = ["server.py", "adb_toolkit/server.py", "static/index.html"]
    good = True
    for rel in required:
        if (ROOT / rel).is_file():
            ok(f"found {rel}")
        else:
            fail(f"missing {rel} — run setup from the repo root")
            good = False
    return good


def ensure_env_example() -> None:
    path = ROOT / ".env.example"
    if path.is_file():
        ok(".env.example already present")
        return
    path.write_text(
        "# Optional overrides for python3 server.py\n"
        "# Copy to .env and export manually, or set in your shell:\n"
        "ADB_TOOLKIT_HOST=127.0.0.1\n"
        "ADB_TOOLKIT_PORT=8000\n"
        "# ADB_PATH=adb\n",
        encoding="utf-8",
    )
    ok("wrote .env.example (optional — server uses stdlib defaults)")


def smoke_import() -> bool:
    try:
        subprocess.run(
            [sys.executable, "-c", "from adb_toolkit.server import main"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=10,
        )
        ok("adb_toolkit imports cleanly")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        fail(f"could not import adb_toolkit: {exc}")
        return False


def main() -> int:
    print("\nAndroid ADB Toolkit — local setup\n")
    python_ok = check_python()
    tree_ok = check_tree()
    import_ok = smoke_import() if python_ok and tree_ok else False
    adb_ok = check_adb()
    ensure_env_example()
    print()

    if not python_ok or not tree_ok or not import_ok:
        fail("Setup incomplete. Fix the errors above, then re-run: python3 setup.py")
        print()
        return 1

    if not adb_ok:
        warn("Setup OK for the server, but connect a device after installing ADB.\n")
    else:
        ok("Environment looks ready\n")

    print("Next steps:\n")
    print("  1. Start the local control panel:")
    print("       python3 server.py\n")
    print(f"  2. Open:  {URL}\n")
    print("  Optional:")
    print("       python3 -m adb_toolkit devices")
    print("       python3 wireless.py --list\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
