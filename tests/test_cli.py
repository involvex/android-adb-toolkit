#!/usr/bin/env python3
"""CLI parser / dispatch tests (mocked ADB)."""

from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from adb_toolkit import cli
from adb_toolkit.adb import AdbError, AdbResult


class CliDispatchTests(unittest.TestCase):
    @mock.patch("adb_toolkit.cli.adb_lib.list_devices")
    def test_devices_json(self, list_mock):
        list_mock.return_value = [
            {
                "serial": "emulator-5554",
                "status": "device",
                "connection": "usb",
                "model": "Emu",
            }
        ]
        code = cli.main(["devices", "--json"])
        self.assertEqual(code, 0)

    @mock.patch("adb_toolkit.cli.adb_lib.get_device_info")
    def test_info(self, info_mock):
        info_mock.return_value = {
            "serial": "emulator-5554",
            "model": "Pixel",
            "android": "14",
            "api": "34",
            "battery": 80,
            "battery_status": "charging",
            "brand": "google",
            "build": "AP2A",
        }
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            code = cli.main(["info"])
        self.assertEqual(code, 0)
        self.assertIn("model: Pixel", buf.getvalue())

    @mock.patch("adb_toolkit.cli.adb_lib.shell_command")
    def test_shell(self, shell_mock):
        shell_mock.return_value = AdbResult("ok", "", 0)
        code = cli.main(["shell", "echo", "ok"])
        self.assertEqual(code, 0)
        shell_mock.assert_called_once()
        self.assertEqual(shell_mock.call_args[0][0], "echo ok")

    @mock.patch("adb_toolkit.cli.adb_lib.list_devices", side_effect=AdbError("missing", code="adb_missing"))
    def test_devices_adb_missing(self, _list):
        code = cli.main(["devices"])
        self.assertEqual(code, 1)

    def test_help_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
