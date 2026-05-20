#!/usr/bin/env python3
"""Push multiple files to multiple devices in parallel"""
import subprocess, sys, pathlib, concurrent.futures

def push_file(device, src, dst):
    result = subprocess.run(
        ['adb', '-s', device, 'push', src, dst],
        capture_output=True, text=True
    )
    return (device, src, result.returncode == 0)

src_files = sys.argv[1:-1] if len(sys.argv) > 2 else ['./build.apk']
dest = sys.argv[-1] if len(sys.argv) > 1 else '/data/local/tmp/'

devices_out = subprocess.run(['adb', 'devices', '-l'], 
                            capture_output=True, text=True).stdout
devices = [l.split()[0] for l in devices_out.splitlines()[1:] if 'device' in l]

print(f"Pushing {len(src_files)} file(s) to {len(devices)} device(s)")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futures = []
    for dev in devices:
        for src in src_files:
            futures.append(ex.submit(push_file, dev, src, dest))
    
    for future in concurrent.futures.as_completed(futures):
        dev, src, ok = future.result()
        icon = '✓' if ok else '✗'
        print(f"  {icon} {dev}: {src}")
