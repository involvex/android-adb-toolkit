#!/usr/bin/env python3
import subprocess, time, sys
def adb(cmd):
    return subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True).stdout.strip()
pkg = sys.argv[1] if len(sys.argv) > 1 else "com.android.systemui"
print(f"\n[Memory Monitor] {pkg}\n")
for _ in range(10):
    mem = adb(f"dumpsys meminfo {pkg} | grep TOTAL | awk '{{print $2}}'")
    try:
        mb = int(mem) / 1024
        print(f"  {mb:.1f} MB")
    except: pass
    time.sleep(2)
