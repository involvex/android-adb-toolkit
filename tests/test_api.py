#!/usr/bin/env python3
"""Lightweight HTTP API tests using the stdlib server (mocked ADB)."""

from __future__ import annotations

import io
import json
import threading
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from adb_toolkit.adb import AdbResult
from adb_toolkit.server import create_server


class ApiServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = create_server("127.0.0.1", 0)
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get_json(self, path: str):
        with urlopen(self.base + path, timeout=5) as resp:
            return json.loads(resp.read().decode()), resp.status

    def post_json(self, path: str, body: dict):
        req = Request(
            self.base + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()), resp.status

    def test_health(self):
        data, status = self.get_json("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertIn("adb_available", data)

    @mock.patch("adb_toolkit.server.adb_lib.list_devices")
    def test_devices(self, list_mock):
        list_mock.return_value = [
            {"serial": "emulator-5554", "status": "device", "model": "Emu", "connection": "usb"}
        ]
        data, status = self.get_json("/api/devices")
        self.assertEqual(status, 200)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["devices"][0]["serial"], "emulator-5554")

    @mock.patch("adb_toolkit.server.adb_lib.shell_command")
    def test_shell(self, shell_mock):
        shell_mock.return_value = AdbResult("hello", "", 0)
        data, status = self.post_json(
            "/api/device/emulator-5554/shell",
            {"command": "echo hello"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["stdout"], "hello")

    def test_unknown_route(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get_json("/api/nope")
        self.assertEqual(ctx.exception.code, 404)
        body = json.loads(ctx.exception.read().decode())
        self.assertEqual(body["error"], "not_found")

    @mock.patch("adb_toolkit.server.adb_lib.run_adb")
    def test_logcat_snapshot(self, run_mock):
        run_mock.return_value = AdbResult("I/Test: hello\nW/Test: warn", "", 0)
        data, status = self.get_json(
            "/api/device/emulator-5554/logcat?lines=20&level=I"
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data["lines"]), 2)
        args = run_mock.call_args[0][0]
        self.assertEqual(args[0], "logcat")
        self.assertIn("-d", args)

    @mock.patch("adb_toolkit.server.adb_lib.terminate_process")
    @mock.patch("adb_toolkit.server.adb_lib.open_logcat_stream")
    @mock.patch("adb_toolkit.server.adb_lib.adb_available", return_value=True)
    def test_logcat_stream_sse(self, _avail, open_mock, term_mock):
        proc = mock.Mock()
        proc.stdout = io.StringIO("I/Demo: line one\nI/Demo: line two\n")
        proc.stderr = io.StringIO("")
        proc.poll.return_value = 0
        open_mock.return_value = proc

        with urlopen(
            self.base + "/api/device/emulator-5554/logcat/stream?level=I",
            timeout=5,
        ) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))
            body = resp.read().decode()

        self.assertIn("event: status", body)
        self.assertIn('"state":"started"', body)
        self.assertIn("event: line", body)
        self.assertIn("line one", body)
        self.assertIn("line two", body)
        self.assertIn('"state":"ended"', body)
        open_mock.assert_called_once()
        term_mock.assert_called_once_with(proc)

    @mock.patch("adb_toolkit.server.adb_lib.adb_available", return_value=True)
    def test_logcat_stream_rejects_bad_level(self, _avail):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(
                self.base + "/api/device/emulator-5554/logcat/stream?level=NOPE",
                timeout=5,
            )
        self.assertEqual(ctx.exception.code, 400)
        body = json.loads(ctx.exception.read().decode())
        self.assertEqual(body["error"], "invalid_param")

    @mock.patch("adb_toolkit.server.adb_lib.open_logcat_stream")
    @mock.patch("adb_toolkit.server.adb_lib.adb_available", return_value=True)
    def test_logcat_stream_invalid_serial(self, _avail, open_mock):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(
                self.base + "/api/device/bad%3Bserial/logcat/stream",
                timeout=5,
            )
        self.assertEqual(ctx.exception.code, 400)
        open_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
