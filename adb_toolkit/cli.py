#!/usr/bin/env python3
"""Canonical Python CLI for Android ADB Toolkit.

Usage:
    python3 -m adb_toolkit devices
    python3 -m adb_toolkit info
    python3 -m adb_toolkit packages --type user
    python3 -m adb_toolkit shell "getprop ro.product.model"
    python3 -m adb_toolkit screenshot -o screen.png
    python3 -m adb_toolkit install app.apk

For the web UI: ``python3 server.py``
For wireless helpers: ``python3 wireless.py --list``
For the optional Node CLI: see ``cli/README.md``
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import __version__
from . import adb as adb_lib


def _print_error(exc: adb_lib.AdbError) -> int:
    print(f"Error: {exc.message}", file=sys.stderr)
    if exc.details:
        print(exc.details, file=sys.stderr)
    return 1


def cmd_devices(args: argparse.Namespace) -> int:
    try:
        devices = adb_lib.list_devices()
    except adb_lib.AdbError as exc:
        return _print_error(exc)
    if args.json:
        print(json.dumps(devices, indent=2))
        return 0
    if not devices:
        print("No devices connected.")
        return 0
    for dev in devices:
        conn = dev.get("connection", "?")
        model = dev.get("model") or ""
        print(f"{dev['serial']}\t{dev['status']}\t{conn}\t{model}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    try:
        info = adb_lib.get_device_info(args.serial)
    except adb_lib.AdbError as exc:
        return _print_error(exc)
    if args.json:
        print(json.dumps(info, indent=2))
        return 0
    for key in (
        "serial",
        "model",
        "brand",
        "android",
        "api",
        "build",
        "battery",
        "battery_status",
    ):
        if key in info and info[key] is not None:
            print(f"{key}: {info[key]}")
    return 0


def cmd_packages(args: argparse.Namespace) -> int:
    try:
        packages = adb_lib.list_packages(args.serial, args.type)
    except adb_lib.AdbError as exc:
        return _print_error(exc)
    if args.json:
        print(json.dumps(packages, indent=2))
        return 0
    for pkg in packages:
        print(pkg)
    print(f"\n{len(packages)} packages", file=sys.stderr)
    return 0


def cmd_shell(args: argparse.Namespace) -> int:
    parts = list(args.shell_args or [])
    if parts[:1] == ["--"]:
        parts = parts[1:]
    command = " ".join(parts).strip()
    if not command:
        print("Error: shell requires a command", file=sys.stderr)
        return 2
    try:
        result = adb_lib.shell_command(command, serial=args.serial)
    except adb_lib.AdbError as exc:
        return _print_error(exc)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def cmd_screenshot(args: argparse.Namespace) -> int:
    try:
        data = adb_lib.screencap_png(args.serial)
    except adb_lib.AdbError as exc:
        return _print_error(exc)
    out = args.output or "screenshot.png"
    with open(out, "wb") as fh:
        fh.write(data)
    print(f"Saved {out} ({len(data)} bytes)")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    try:
        result = adb_lib.install_apk(args.serial, args.apk)
    except adb_lib.AdbError as exc:
        return _print_error(exc)
    print(result.stdout or result.stderr or f"exit {result.returncode}")
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adb_toolkit",
        description="Android ADB Toolkit CLI (safe subprocess helpers)",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "-s",
        "--serial",
        help="Device serial (USB or IP:port)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_devices = sub.add_parser("devices", help="List connected devices")
    p_devices.add_argument("--json", action="store_true", help="JSON output")
    p_devices.set_defaults(func=cmd_devices)

    p_info = sub.add_parser("info", help="Show device info")
    p_info.add_argument("--json", action="store_true", help="JSON output")
    p_info.set_defaults(func=cmd_info)

    p_pkgs = sub.add_parser("packages", help="List packages")
    p_pkgs.add_argument(
        "--type",
        choices=("user", "system", "all"),
        default="user",
        help="Package set (default: user)",
    )
    p_pkgs.add_argument("--json", action="store_true", help="JSON output")
    p_pkgs.set_defaults(func=cmd_packages)

    p_shell = sub.add_parser("shell", help="Run a device shell command")
    p_shell.add_argument(
        "shell_args",
        nargs=argparse.REMAINDER,
        help="Shell command (quote as one argument if needed)",
    )
    p_shell.set_defaults(func=cmd_shell)

    p_shot = sub.add_parser("screenshot", help="Capture a PNG screenshot")
    p_shot.add_argument("-o", "--output", default="screenshot.png")
    p_shot.set_defaults(func=cmd_screenshot)

    p_install = sub.add_parser("install", help="Install an APK")
    p_install.add_argument("apk", help="Path to APK")
    p_install.set_defaults(func=cmd_install)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
