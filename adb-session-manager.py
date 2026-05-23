#!/usr/bin/env python3
"""
ADB Session Manager
Track concurrent ADB sessions, profile connected devices,
export session data to JSON for analytics.
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path


class ADBSessionManager:
    def __init__(self):
        self.sessions = []
        self.timestamp = datetime.now().isoformat()

    def list_devices(self):
        """Get all connected ADB devices."""
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Error listing devices: {e}", file=sys.stderr)
            return None

    def get_device_info(self, device_id):
        """Profile a single device."""
        info = {
            "device_id": device_id,
            "model": self._get_prop(device_id, "ro.product.model"),
            "android_version": self._get_prop(device_id, "ro.build.version.release"),
            "api_level": self._get_prop(device_id, "ro.build.version.sdk"),
            "manufacturer": self._get_prop(device_id, "ro.product.manufacturer"),
            "connected_at": self.timestamp,
        }
        return info

    def _get_prop(self, device_id, prop_name):
        """Get Android system property via ADB."""
        try:
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "getprop", prop_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "error"

    def capture_sessions(self):
        """Capture all active ADB sessions."""
        devices_output = self.list_devices()
        if not devices_output:
            return

        lines = devices_output.split("\n")
        for line in lines:
            if not line.strip() or line.startswith("List"):
                continue
            parts = line.split()
            if len(parts) > 0:
                device_id = parts[0]
                if device_id != "offline":
                    device_info = self.get_device_info(device_id)
                    self.sessions.append(device_info)

    def export_json(self, output_file=None):
        """Export session data to JSON."""
        data = {
            "timestamp": self.timestamp,
            "session_count": len(self.sessions),
            "devices": self.sessions,
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✅ Session data exported to {output_file}")
        else:
            print(json.dumps(data, indent=2))

        return data

    def print_summary(self):
        """Print human-readable session summary."""
        print(f"🔌 ADB Session Manager — {self.timestamp}")
        print(f"📱 Connected devices: {len(self.sessions)}\n")
        for session in self.sessions:
            print(f"  • {session['device_id']}")
            print(f"    Model: {session['model']}")
            print(f"    Android: {session['android_version']} (API {session['api_level']})")
            print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ADB Session Manager")
    parser.add_argument(
        "--export", type=str, help="Export session data to JSON file"
    )
    parser.add_argument("--summary", action="store_true", help="Print summary")
    args = parser.parse_args()

    manager = ADBSessionManager()
    manager.capture_sessions()

    if args.export:
        manager.export_json(args.export)
    else:
        manager.print_summary()

    if args.summary:
        manager.print_summary()


if __name__ == "__main__":
    main()
