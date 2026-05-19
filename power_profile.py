#!/usr/bin/env python3
"""
power_profile.py - Real-time power profiler via ADB
Tracks CPU, GPU, and display power drain per component
Usage: python3 power_profile.py [--duration 60] [--interval 2]
"""
import subprocess, time, sys, argparse

def adb(cmd):
    r = subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True)
    return r.stdout.strip()

def get_power_draw():
    """Get instantaneous power draw from battery stats"""
    raw = adb("dumpsys batteryproperties 2>/dev/null || dumpsys battery")
    for line in raw.splitlines():
        if "current" in line.lower() and "ma" in line.lower():
            import re
            m = re.search(r'(\d+)\s*m?a', line, re.IGNORECASE)
            if m:
                return int(m.group(1))
    return 0

def get_cpu_freq():
    """Get current CPU frequency in MHz"""
    try:
        freq_khz = int(adb("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"))
        return freq_khz // 1000
    except:
        return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=60, help="Profile duration in seconds")
    parser.add_argument("--interval", type=float, default=2, help="Sample interval in seconds")
    args = parser.parse_args()
    
    print(f"\n⚡ Android Power Profiler ({args.duration}s)\n")
    print(f"{'Time':<8} {'Current (mA)':<15} {'CPU MHz':<10} {'Trend'}")
    print("─" * 50)
    
    samples = []
    start = time.time()
    
    while time.time() - start < args.duration:
        current = get_power_draw()
        cpu = get_cpu_freq()
        samples.append(current)
        
        trend = "↑" if len(samples) > 1 and current > samples[-2] else "↓"
        elapsed = int(time.time() - start)
        print(f"{elapsed:<8} {current:<15} {cpu:<10} {trend}")
        
        time.sleep(args.interval)
    
    avg = sum(samples) // len(samples) if samples else 0
    print("\n" + "─" * 50)
    print(f"Average power: {avg} mA")
    print(f"Peak: {max(samples) if samples else 0} mA")
    print(f"Min: {min(samples) if samples else 0} mA")

if __name__ == "__main__":
    main()
