#!/usr/bin/env python3
"""
ADB Session Manager
Track, manage, and profile concurrent ADB connections
Purpose: Monitor multiple Android device sessions, port forwarding, and active operations
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class ADBSession:
    device_id: str
    status: str
    model: str
    android_version: str
    battery_level: int
    connection_type: str  # usb, wireless
    active_ports: List[int]
    last_activity: float

class ADBSessionManager:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.sessions: Dict[str, ADBSession] = {}

    def discover_devices(self) -> List[str]:
        """Discover all connected ADB devices"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if '\t' in line:
                    device_id = line.split('\t')[0].strip()
                    if device_id:
                        devices.append(device_id)
            if self.verbose:
                print(f"🔍 Discovered {len(devices)} device(s)")
            return devices
        except FileNotFoundError:
            print("❌ ADB not found. Please install Android SDK Platform Tools")
            sys.exit(1)

    def get_device_info(self, device_id: str) -> Dict:
        """Get detailed device information"""
        try:
            props = {}
            for prop in ['ro.build.product', 'ro.build.version.release', 'battery_level']:
                result = subprocess.run(
                    ['adb', '-s', device_id, 'shell', f'getprop {prop}'],
                    capture_output=True, text=True, timeout=5
                )
                props[prop] = result.stdout.strip()
            
            # Get battery level
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'dumpsys battery'],
                capture_output=True, text=True, timeout=5
            )
            battery = 0
            for line in result.stdout.split('\n'):
                if 'level:' in line:
                    battery = int(line.split(':')[1].strip())
            
            return {
                'model': props.get('ro.build.product', 'Unknown'),
                'android_version': props.get('ro.build.version.release', 'Unknown'),
                'battery': battery
            }
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Failed to get device info: {e}")
            return {'model': 'Unknown', 'android_version': 'Unknown', 'battery': 0}

    def get_active_ports(self, device_id: str) -> List[int]:
        """Get list of active port forwards for device"""
        try:
            result = subprocess.run(['adb', 'forward', '--list'], capture_output=True, text=True)
            ports = []
            for line in result.stdout.split('\n'):
                if device_id in line:
                    # Parse: "emulator-5554 tcp:5555 tcp:5555"
                    parts = line.split()
                    if len(parts) >= 3:
                        port = parts[1].replace('tcp:', '')
                        if port.isdigit():
                            ports.append(int(port))
            return ports
        except:
            return []

    def scan_sessions(self) -> None:
        """Scan all connected devices and build session info"""
        devices = self.discover_devices()
        current_time = time.time()

        for device_id in devices:
            info = self.get_device_info(device_id)
            ports = self.get_active_ports(device_id)
            
            # Determine connection type
            conn_type = "wireless" if ":" in device_id else "usb"
            
            session = ADBSession(
                device_id=device_id,
                status="connected",
                model=info['model'],
                android_version=info['android_version'],
                battery_level=info['battery'],
                connection_type=conn_type,
                active_ports=ports,
                last_activity=current_time
            )
            
            self.sessions[device_id] = session

    def print_summary(self) -> None:
        """Print formatted session summary"""
        print("\n🔌 ADB Session Summary")
        print("=" * 80)
        
        if not self.sessions:
            print("No devices connected")
            return

        for device_id, session in self.sessions.items():
            print(f"\n📱 {session.model} ({device_id})")
            print(f"   Status:        {session.status}")
            print(f"   Android:       {session.android_version}")
            print(f"   Battery:       {session.battery_level}%")
            print(f"   Connection:    {session.connection_type}")
            if session.active_ports:
                print(f"   Ports:         {', '.join(map(str, session.active_ports))}")

    def export_json(self, filepath: str) -> None:
        """Export session data as JSON"""
        data = {device: asdict(session) for device, session in self.sessions.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Session data exported to {filepath}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ADB Session Manager")
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-j', '--json', help='Export sessions to JSON file')
    args = parser.parse_args()

    manager = ADBSessionManager(verbose=args.verbose)
    manager.scan_sessions()
    manager.print_summary()
    
    if args.json:
        manager.export_json(args.json)

if __name__ == '__main__':
    main()
