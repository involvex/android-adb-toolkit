#!/usr/bin/env python3
"""
Android Device State Analyzer
Generates comprehensive device diagnostics via ADB
"""
import subprocess
import json
import sys
from datetime import datetime

def run_adb(cmd):
    """Run ADB command and return output"""
    try:
        result = subprocess.run(['adb'] + cmd.split(), capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        return f"Error: {e}"

def get_device_info():
    """Gather comprehensive device state"""
    info = {
        'timestamp': datetime.now().isoformat(),
        'device': run_adb('shell getprop ro.serialno'),
        'model': run_adb('shell getprop ro.model'),
        'android_version': run_adb('shell getprop ro.build.version.release'),
        'api_level': run_adb('shell getprop ro.build.version.sdk'),
        'kernel_version': run_adb('shell uname -r'),
        'battery': run_adb('shell dumpsys battery | grep -E "level|status|temp"'),
        'memory': run_adb('shell cat /proc/meminfo | head -5'),
        'disk_usage': run_adb('shell df -h /data'),
        'running_services': run_adb('shell dumpsys activity services | grep -c "Service"'),
        'foreground_app': run_adb('shell dumpsys window | grep mCurrentFocus'),
        'adb_root': 'Enabled' if run_adb('shell id | grep root') else 'Disabled',
    }
    return info

def analyze_boot_time():
    """Get device uptime and last reboot time"""
    uptime = run_adb('shell uptime')
    return {'uptime': uptime}

def check_security_state():
    """Check security-relevant properties"""
    state = {
        'adb_enabled': 'Yes' if run_adb('shell settings get global adb_enabled') == '1' else 'No',
        'usb_debugging': 'Yes' if run_adb('shell getprop ro.debuggable') == '1' else 'No',
        'selinux_status': run_adb('shell getenforce'),
        'secure_boot': run_adb('shell getprop ro.secure'),
    }
    return state

if __name__ == '__main__':
    print(json.dumps({
        'device': get_device_info(),
        'boot': analyze_boot_time(),
        'security': check_security_state(),
    }, indent=2))
