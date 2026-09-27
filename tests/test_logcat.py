#!/usr/bin/env python3
"""Tests for logcat argument building and process helpers."""

from __future__ import annotations

import io
import subprocess
import unittest
from unittest import mock

from adb_toolkit import adb as adb_lib
from adb_toolkit.adb import AdbError, AdbResult


class LogcatArgsTests(unittest.TestCase):
    def test_default_level_filter(self):
        args = adb_lib.build_logcat_args(level="I")
        self.assertEqual(args[0], "logcat")
        self.assertIn("*:I", args)
        self.assertIn("-v", args)

    def test_tag_filter_silences_others(self):
        args = adb_lib.build_logcat_args(level="D", tag="ActivityManager")
        self.assertIn("ActivityManager:D", args)
        self.assertIn("*:S", args)

    def test_rejects_bad_level(self):
        with self.assertRaises(AdbError) as ctx:
            adb_lib.build_logcat_args(level="VERBOSE")
        self.assertEqual(ctx.exception.code, "invalid_param")

    def test_rejects_bad_tag(self):
        with self.assertRaises(AdbError):
            adb_lib.build_logcat_args(tag="bad tag;rm")

    def test_pid_filter(self):
        args = adb_lib.build_logcat_args(pid=4321, level="W")
        self.assertIn("--pid", args)
        self.assertIn("4321", args)
        self.assertIn("*:W", args)

    def test_dump_with_lines(self):
        args = adb_lib.build_logcat_args(dump=True, lines=50, level="V")
        self.assertIn("-d", args)
        self.assertIn("-t", args)
        self.assertIn("50", args)


class PackagePidTests(unittest.TestCase):
    @mock.patch("adb_toolkit.adb.run_adb")
    def test_resolve_pid(self, run_mock):
        run_mock.return_value = AdbResult("1234", "", 0)
        self.assertEqual(adb_lib.resolve_package_pid("emu", "com.example.app"), 1234)

    @mock.patch("adb_toolkit.adb.run_adb")
    def test_resolve_pid_missing(self, run_mock):
        run_mock.return_value = AdbResult("", "", 1)
        with self.assertRaises(AdbError) as ctx:
            adb_lib.resolve_package_pid("emu", "com.missing")
        self.assertEqual(ctx.exception.code, "process_not_found")


class OpenLogcatStreamTests(unittest.TestCase):
    @mock.patch("adb_toolkit.adb.adb_available", return_value=True)
    @mock.patch("adb_toolkit.adb.subprocess.Popen")
    def test_opens_without_shell(self, popen_mock, _avail):
        proc = mock.Mock()
        popen_mock.return_value = proc
        result = adb_lib.open_logcat_stream("emulator-5554", level="I", tag="Test")
        self.assertIs(result, proc)
        args, kwargs = popen_mock.call_args
        cmd = args[0]
        self.assertEqual(cmd[:3], ["adb", "-s", "emulator-5554"])
        self.assertEqual(cmd[3], "logcat")
        self.assertFalse(kwargs.get("shell"))
        self.assertIs(kwargs.get("stdout"), subprocess.PIPE)

    @mock.patch("adb_toolkit.adb.adb_available", return_value=True)
    @mock.patch("adb_toolkit.adb.resolve_package_pid", return_value=99)
    @mock.patch("adb_toolkit.adb.subprocess.Popen")
    def test_package_uses_pid(self, popen_mock, _pid, _avail):
        popen_mock.return_value = mock.Mock()
        adb_lib.open_logcat_stream("serial", package="com.foo", level="V")
        cmd = popen_mock.call_args[0][0]
        self.assertIn("--pid", cmd)
        self.assertIn("99", cmd)

    def test_terminate_process(self):
        proc = mock.Mock()
        # Still running once, then exited after SIGTERM.
        proc.poll.side_effect = [None, 0, 0, 0]
        proc.stdout = io.StringIO()
        proc.stderr = io.StringIO()
        adb_lib.terminate_process(proc, grace=0.2)
        proc.send_signal.assert_called()


if __name__ == "__main__":
    unittest.main()
