#!/usr/bin/env python3
"""Unit tests for adb_toolkit.adb helpers (mocked subprocess)."""

from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from adb_toolkit import adb as adb_lib
from adb_toolkit.adb import AdbError, AdbResult


def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(
        args=["adb"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class ValidateSerialTests(unittest.TestCase):
    def test_accepts_emulator_and_wireless(self):
        self.assertEqual(adb_lib.validate_serial("emulator-5554"), "emulator-5554")
        self.assertEqual(
            adb_lib.validate_serial("192.168.1.10:5555"),
            "192.168.1.10:5555",
        )

    def test_rejects_injection(self):
        with self.assertRaises(AdbError) as ctx:
            adb_lib.validate_serial("device; rm -rf /")
        self.assertEqual(ctx.exception.code, "invalid_serial")


class RunAdbTests(unittest.TestCase):
    @mock.patch("adb_toolkit.adb.adb_available", return_value=True)
    @mock.patch("adb_toolkit.adb.subprocess.run")
    def test_builds_argv_without_shell(self, run_mock, _avail):
        run_mock.return_value = _completed("ok")
        result = adb_lib.run_adb(["devices"], serial="emulator-5554")
        self.assertTrue(result.ok)
        args, kwargs = run_mock.call_args
        self.assertEqual(args[0][:4], ["adb", "-s", "emulator-5554", "devices"])
        self.assertFalse(kwargs.get("shell"))

    @mock.patch("adb_toolkit.adb.adb_available", return_value=False)
    def test_missing_adb(self, _avail):
        with self.assertRaises(AdbError) as ctx:
            adb_lib.run_adb(["devices"])
        self.assertEqual(ctx.exception.code, "adb_missing")

    @mock.patch("adb_toolkit.adb.adb_available", return_value=True)
    @mock.patch("adb_toolkit.adb.subprocess.run", side_effect=subprocess.TimeoutExpired("adb", 1))
    def test_timeout(self, _run, _avail):
        with self.assertRaises(AdbError) as ctx:
            adb_lib.run_adb(["shell", "sleep", "99"], timeout=1)
        self.assertEqual(ctx.exception.code, "timeout")


class ListDevicesTests(unittest.TestCase):
    @mock.patch("adb_toolkit.adb.run_adb")
    def test_parses_devices_l(self, run_mock):
        run_mock.return_value = AdbResult(
            stdout=(
                "List of devices attached\n"
                "emulator-5554          device product:sdk_gphone model:sdk_gphone_x86 device:generic transport_id:1\n"
                "192.168.1.5:5555       device product:phone model:Pixel_7 device:panther\n"
                "offline-device         offline\n"
            ),
            stderr="",
            returncode=0,
        )
        devices = adb_lib.list_devices()
        self.assertEqual(len(devices), 3)
        self.assertEqual(devices[0]["serial"], "emulator-5554")
        self.assertEqual(devices[0]["connection"], "usb")
        self.assertEqual(devices[1]["connection"], "wireless")
        self.assertEqual(devices[1]["model"], "Pixel 7")


class ShellCommandTests(unittest.TestCase):
    @mock.patch("adb_toolkit.adb.run_adb")
    def test_rejects_empty(self, run_mock):
        with self.assertRaises(AdbError):
            adb_lib.shell_command("  ")
        run_mock.assert_not_called()

    @mock.patch("adb_toolkit.adb.run_adb")
    def test_passes_single_shell_arg(self, run_mock):
        run_mock.return_value = AdbResult("Pixel", "", 0)
        adb_lib.shell_command("getprop ro.product.model", serial="abc")
        run_mock.assert_called_once_with(
            ["shell", "getprop ro.product.model"],
            serial="abc",
            timeout=adb_lib.DEFAULT_TIMEOUT,
        )


class PackageValidationTests(unittest.TestCase):
    def test_bad_package(self):
        with self.assertRaises(AdbError):
            adb_lib.uninstall_package(None, "com.foo; reboot")


class WirelessValidationTests(unittest.TestCase):
    def test_bad_host(self):
        with self.assertRaises(AdbError):
            adb_lib.wireless_connect("1.2.3.4;evil", 5555)

    def test_bad_pairing_code(self):
        with self.assertRaises(AdbError):
            adb_lib.wireless_pair("1.2.3.4", 37123, "12ab56")


class GetDeviceInfoTests(unittest.TestCase):
    @mock.patch("adb_toolkit.adb.run_adb")
    @mock.patch("adb_toolkit.adb.get_prop")
    @mock.patch("adb_toolkit.adb.list_devices")
    def test_info_happy_path(self, list_mock, prop_mock, run_mock):
        list_mock.return_value = [
            {"serial": "emulator-5554", "status": "device", "model": "Emu", "connection": "usb"}
        ]
        prop_mock.side_effect = lambda serial, prop, timeout=10: {
            "ro.product.model": "Pixel",
            "ro.product.brand": "Google",
            "ro.build.version.release": "14",
            "ro.build.version.sdk": "34",
            "ro.build.display.id": "AP2A",
            "ro.product.manufacturer": "Google",
        }[prop]
        run_mock.return_value = AdbResult(
            "level: 80\nstatus: 2\n",
            "",
            0,
        )
        info = adb_lib.get_device_info("emulator-5554")
        self.assertEqual(info["model"], "Pixel")
        self.assertEqual(info["battery"], 80)
        self.assertEqual(info["battery_status"], "charging")

    @mock.patch("adb_toolkit.adb.list_devices", return_value=[])
    def test_no_device(self, _list):
        with self.assertRaises(AdbError) as ctx:
            adb_lib.get_device_info()
        self.assertEqual(ctx.exception.code, "no_device")


if __name__ == "__main__":
    unittest.main()
