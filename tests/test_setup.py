#!/usr/bin/env python3
"""Smoke test for setup.py (does not require adb)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SetupScriptTests(unittest.TestCase):
    def test_setup_py_runs(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "setup.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Exit 0 even when adb is missing (warn-only); fails only on Python/tree issues.
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("python3 server.py", proc.stdout)
        self.assertIn("http://127.0.0.1:8000/", proc.stdout)
        self.assertIn("adb_toolkit imports cleanly", proc.stdout)

    def test_setup_ts_exists(self):
        self.assertTrue((ROOT / "setup.ts").is_file())
        self.assertTrue((ROOT / ".env.example").is_file())


if __name__ == "__main__":
    unittest.main()
