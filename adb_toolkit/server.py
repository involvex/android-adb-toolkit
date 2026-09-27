"""HTTP API + static UI server for the Android ADB Toolkit.

Usage:
    python3 -m adb_toolkit.server
    python3 server.py

Binds to 127.0.0.1:8000 by default (override with --host / --port).
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__
from . import adb as adb_lib

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

DEVICE_PATH_RE = re.compile(
    r"^/api/device/(?P<serial>[^/]+)(?:/(?P<action>[\w-]+))?$"
)


def json_error(code: str, message: str, status: int = 400, details: str = "") -> Tuple[dict, int]:
    body = {"error": code, "message": message, "status": status}
    if details:
        body["details"] = details
    return body, status


class ToolkitHandler(BaseHTTPRequestHandler):
    server_version = f"ADBToolkit/{__version__}"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # —— helpers ————————————————————————————————————————————————

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, indent=2, default=str).encode("utf-8")
        self._send(status, payload, "application/json; charset=utf-8")

    def send_error_json(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: str = "",
    ) -> None:
        body, status = json_error(code, message, status, details)
        self.send_json(body, status)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise adb_lib.AdbError(
                "Invalid JSON body",
                code="invalid_json",
                details=str(exc),
            ) from exc
        if not isinstance(data, dict):
            raise adb_lib.AdbError("JSON body must be an object", code="invalid_json")
        return data

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    # —— routing ————————————————————————————————————————————————

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        try:
            self._handle_get()
        except adb_lib.AdbError as exc:
            status = 404 if exc.code in ("device_not_found", "no_device") else 500
            if exc.code in ("invalid_serial", "invalid_param", "invalid_json"):
                status = 400
            if exc.code == "adb_missing":
                status = 503
            self.send_error_json(exc.code, exc.message, status, exc.details)
        except Exception as exc:  # noqa: BLE001 — last-resort API guard
            traceback.print_exc()
            self.send_error_json("internal_error", str(exc), 500)

    def do_POST(self) -> None:
        try:
            self._handle_post()
        except adb_lib.AdbError as exc:
            status = 404 if exc.code in ("device_not_found", "no_device") else 500
            if exc.code in ("invalid_serial", "invalid_param", "invalid_json"):
                status = 400
            if exc.code == "adb_missing":
                status = 503
            self.send_error_json(exc.code, exc.message, status, exc.details)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self.send_error_json("internal_error", str(exc), 500)

    def _handle_get(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            return self._serve_static("index.html")
        if path.startswith("/static/"):
            return self._serve_static(path[len("/static/") :])

        if path == "/api/health":
            return self.send_json(
                {
                    "status": "ok",
                    "version": __version__,
                    "adb_available": adb_lib.adb_available(),
                }
            )

        if path == "/api/devices":
            devices = adb_lib.list_devices()
            return self.send_json({"devices": devices, "count": len(devices)})

        match = DEVICE_PATH_RE.match(path)
        if match:
            serial = unquote(match.group("serial"))
            action = match.group("action")
            return self._device_get(serial, action, qs)

        if path == "/api/wireless/status":
            devices = adb_lib.list_devices()
            return self.send_json(
                {
                    "devices": devices,
                    "wireless": [d for d in devices if d.get("connection") == "wireless"],
                }
            )

        self.send_error_json("not_found", f"No route for {path}", 404)

    def _handle_post(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/wireless/connect":
            data = self.read_json()
            host = str(data.get("host", "")).strip()
            port = int(data.get("port", 5555))
            result = adb_lib.wireless_connect(host, port)
            return self.send_json(
                {
                    "success": result.ok or "connected" in result.output.lower(),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            )

        if path == "/api/wireless/pair":
            data = self.read_json()
            host = str(data.get("host", "")).strip()
            port = int(data.get("port", 0))
            code = str(data.get("pairing_code", data.get("code", ""))).strip()
            if not port:
                raise adb_lib.AdbError(
                    "Pairing port is required",
                    code="invalid_param",
                )
            result = adb_lib.wireless_pair(host, port, code)
            return self.send_json(
                {
                    "success": result.ok or "successfully" in result.output.lower(),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            )

        if path == "/api/wireless/disconnect":
            data = self.read_json()
            target = str(data.get("target", data.get("host", ""))).strip()
            result = adb_lib.wireless_disconnect(target)
            return self.send_json(
                {
                    "success": True,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            )

        match = DEVICE_PATH_RE.match(path)
        if match:
            serial = unquote(match.group("serial"))
            action = match.group("action")
            return self._device_post(serial, action)

        self.send_error_json("not_found", f"No route for {path}", 404)

    def _device_get(self, serial: str, action: Optional[str], qs: dict) -> None:
        if action is None or action == "info":
            info = adb_lib.get_device_info(serial)
            return self.send_json(info)

        if action == "packages":
            pkg_type = (qs.get("type") or ["user"])[0]
            packages = adb_lib.list_packages(serial, pkg_type)
            return self.send_json(
                {"packages": packages, "count": len(packages), "type": pkg_type}
            )

        if action == "screenshot":
            png = adb_lib.screencap_png(serial)
            fmt = (qs.get("format") or ["json"])[0]
            if fmt == "png":
                return self._send(200, png, "image/png")
            encoded = base64.b64encode(png).decode("ascii")
            return self.send_json(
                {"image_base64": encoded, "format": "png", "bytes": len(png)}
            )

        if action == "logcat":
            # Snapshot (not a live stream) — keeps the endpoint usable without WS.
            count = int((qs.get("lines") or ["100"])[0])
            count = max(1, min(count, 2000))
            result = adb_lib.run_adb(
                ["logcat", "-d", "-t", str(count)],
                serial=serial,
                timeout=20,
            )
            return self.send_json(
                {
                    "lines": result.stdout.splitlines(),
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            )

        if action == "files":
            path = (qs.get("path") or ["/sdcard"])[0]
            # Restrict to absolute paths without nulls; shell-safe via argv.
            if not path.startswith("/") or "\x00" in path:
                raise adb_lib.AdbError("Invalid path", code="invalid_param")
            result = adb_lib.run_adb(
                ["shell", "ls", "-la", path],
                serial=serial,
                timeout=20,
            )
            return self.send_json(
                {
                    "path": path,
                    "listing": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            )

        self.send_error_json("not_found", f"Unknown action: {action}", 404)

    def _device_post(self, serial: str, action: Optional[str]) -> None:
        if action == "shell":
            data = self.read_json()
            command = str(data.get("command", data.get("cmd", "")))
            timeout = float(data.get("timeout", adb_lib.DEFAULT_TIMEOUT))
            timeout = max(1.0, min(timeout, 120.0))
            result = adb_lib.shell_command(command, serial=serial, timeout=timeout)
            return self.send_json(
                {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "success": result.ok,
                }
            )

        if action == "tap":
            data = self.read_json()
            result = adb_lib.tap(serial, int(data["x"]), int(data["y"]))
            return self.send_json({"success": result.ok, "stderr": result.stderr})

        if action == "swipe":
            data = self.read_json()
            result = adb_lib.swipe(
                serial,
                int(data["x1"]),
                int(data["y1"]),
                int(data["x2"]),
                int(data["y2"]),
                int(data.get("duration", 300)),
            )
            return self.send_json({"success": result.ok, "stderr": result.stderr})

        if action == "text":
            data = self.read_json()
            text = str(data.get("input", data.get("text", "")))
            result = adb_lib.input_text(serial, text)
            return self.send_json({"success": result.ok, "stderr": result.stderr})

        if action == "key":
            data = self.read_json()
            result = adb_lib.keyevent(serial, int(data["code"]))
            return self.send_json({"success": result.ok, "stderr": result.stderr})

        if action == "uninstall":
            data = self.read_json()
            package = str(data.get("package", ""))
            result = adb_lib.uninstall_package(serial, package)
            return self.send_json(
                {
                    "success": result.ok,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )

        if action == "clear":
            data = self.read_json()
            package = str(data.get("package", ""))
            result = adb_lib.clear_package(serial, package)
            return self.send_json(
                {
                    "success": result.ok,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )

        if action == "install":
            # Prefer raw APK body with Content-Type application/vnd.android.package-archive
            # or application/octet-stream; also accept JSON {skipped}.
            content_type = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            if content_type in (
                "application/vnd.android.package-archive",
                "application/octet-stream",
                "application/apk",
            ):
                data = self.read_body()
                if not data:
                    raise adb_lib.AdbError("Empty APK upload", code="invalid_param")
                path = adb_lib.save_temp_upload(data, ".apk")
                try:
                    result = adb_lib.install_apk(serial, path)
                finally:
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
                return self.send_json(
                    {
                        "success": result.ok,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                )
            raise adb_lib.AdbError(
                "Send APK as raw body with Content-Type application/octet-stream",
                code="invalid_param",
            )

        self.send_error_json("not_found", f"Unknown action: {action}", 404)

    def _serve_static(self, rel: str) -> None:
        # Prevent path traversal.
        rel = rel.lstrip("/")
        if ".." in rel.split("/"):
            return self.send_error_json("forbidden", "Invalid path", 403)
        target = (STATIC_DIR / rel).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())):
            return self.send_error_json("forbidden", "Invalid path", 403)
        if not target.is_file():
            return self.send_error_json("not_found", "File not found", 404)
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self._send(200, data, ctype)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), ToolkitHandler)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Android ADB Toolkit web server")
    parser.add_argument(
        "--host",
        default=os.environ.get("ADB_TOOLKIT_HOST", "127.0.0.1"),
        help="Bind address (default: 127.0.0.1 — local only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ADB_TOOLKIT_PORT", "8000")),
        help="Port (default: 8000)",
    )
    args = parser.parse_args(argv)

    if not STATIC_DIR.is_dir():
        print(f"Warning: static UI directory missing: {STATIC_DIR}", file=sys.stderr)

    server = create_server(args.host, args.port)
    print(f"Android ADB Toolkit v{__version__}")
    print(f"Open: http://{args.host}:{args.port}/")
    print(f"API:  http://{args.host}:{args.port}/api/health")
    print(f"ADB:  {'found' if adb_lib.adb_available() else 'NOT FOUND in PATH'}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
