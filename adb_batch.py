#!/usr/bin/env python3
"""adb_batch.py -- Run ADB commands on multiple devices in parallel
Queue up tasks (install, uninstall, push, shell) for all connected devices
"""
import subprocess, threading, argparse, time

def get_devices():
    r = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = []
    for line in r.stdout.splitlines()[1:]:
        if 'device' in line and 'offline' not in line:
            serial = line.split()[0]
            devices.append(serial)
    return devices

def run_task(serial, cmd, task_name):
    """Run ADB command on a single device"""
    try:
        result = subprocess.run(['adb', '-s', serial, 'shell'] + cmd.split(),
                              capture_output=True, text=True, timeout=30)
        status = "✅" if result.returncode == 0 else "❌"
        print(f"{status} [{serial}] {task_name}: {result.stdout[:50]}")
    except Exception as e:
        print(f"❌ [{serial}] {task_name}: {e}")

def batch_task(task, *args):
    """Run task on all connected devices in parallel"""
    devices = get_devices()
    threads = []
    
    print(f"📱 Running on {len(devices)} device(s)\n")
    
    for serial in devices:
        t = threading.Thread(target=run_task, args=(serial, task, ' '.join(str(a) for a in args)))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cmd', required=True, help='ADB shell command')
    parser.add_argument('--list-devices', action='store_true')
    args = parser.parse_args()
    
    if args.list_devices:
        devices = get_devices()
        for d in devices:
            print(f"  • {d}")
    else:
        batch_task(args.cmd)
