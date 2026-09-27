#!/usr/bin/env python3
"""Lightweight HTTP API tests using the stdlib server (mocked ADB)."""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
