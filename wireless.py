#!/usr/bin/env python3
"""
wireless.py — Manage wireless ADB connections (CLI helper).

Usage:
  python3 wireless.py --list
  python3 wireless.py --connect 192.168.1.20 --port 5555
  python3 wireless.py --pair 192.168.1.20 --port 37123 --code 123456
  python3 wireless.py --disconnect 192.168.1.20:5555
"""

from __future__ import annotations

import argparse
import sys

from adb_toolkit import adb as adb_lib


def list_devices() -> None:
    try:
        devices = adb_lib.list_devices()
    except adb_lib.AdbError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        if exc.details:
            print(exc.details, file=sys.stderr)
        sys.exit(1)

    if not devices:
        print("No devices connected.")
        return

    print(f"\nConnected devices ({len(devices)}):")
    for dev in devices:
        icon = "wireless" if dev.get("connection") == "wireless" else "usb"
        model = dev.get("model") or ""
        print(f"  [{icon}] {dev['serial']}  {dev['status']}  {model}")


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wireless ADB manager")
    parser.add_argument("--pair", metavar="IP", help="Pair with device IP")
    parser.add_argument("--connect", metavar="IP", help="Connect to paired device")
    parser.add_argument("--disconnect", metavar="TARGET", help="Disconnect target or all")
    parser.add_argument("--list", action="store_true", help="List devices")
    parser.add_argument("--port", type=int, default=5555, help="Connect/pair port")
    parser.add_argument("--code", help="6-digit pairing code (for --pair)")
    args = parser.parse_args(argv)

    try:
        if args.pair:
            code = args.code
            if not code:
                code = input("Enter 6-digit pairing code: ").strip()
            result = adb_lib.wireless_pair(args.pair, args.port, code)
            print(result.output or f"exit {result.returncode}")
            return 0 if result.ok or "successfully" in result.output.lower() else 1
        if args.connect:
            result = adb_lib.wireless_connect(args.connect, args.port)
            print(result.output or f"exit {result.returncode}")
            return 0 if result.ok or "connected" in result.output.lower() else 1
        if args.disconnect is not None:
            target = args.disconnect
            result = adb_lib.wireless_disconnect(target)
            print(result.output or "disconnected")
            return 0
        list_devices()
        return 0
    except adb_lib.AdbError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        if exc.details:
            print(exc.details, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
