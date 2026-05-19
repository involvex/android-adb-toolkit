#!/usr/bin/env python3
"""
thermal_monitor.py -- Real-time thermal monitoring for Android devices
Shows CPU/GPU temps, throttling state, and thermal zones
Usage: python3 thermal_monitor.py [--interval 1]
"""
import subprocess, time, argparse, os
from datetime import datetime

def adb(cmd):
    r = subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True)
    return r.stdout.strip()

def get_thermal_zones():
    """Get all thermal zones and their temps"""
    out = adb("cat /sys/class/thermal/thermal_zone*/temp")
    zones = adb("ls -1 /sys/class/thermal/thermal_zone*/type | xargs -I {} sh -c 'cat {}'")
    
    temps = []
    zone_names = zones.splitlines()
    for i, temp_str in enumerate(out.splitlines()):
        try:
            temp_c = int(temp_str) / 1000
            name = zone_names[i] if i < len(zone_names) else f"Zone{i}"
            temps.append((name, temp_c))
        except:
            pass
    
    return temps

def get_throttling():
    """Check if device is thermal throttling"""
    out = adb("dumpsys thermal")
    return "throttling" in out.lower() and "severe" in out.lower()

def get_freq():
    """Get current CPU frequency"""
    out = adb("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    try:
        freq_khz = int(out)
        return freq_khz // 1000  # Convert to MHz
    except:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=1, help="Update interval in seconds")
    args = parser.parse_args()

    print("\n🌡️  Thermal Monitor — press Ctrl+C to stop\n")

    try:
        while True:
            os.system("clear" if os.name != "nt" else "cls")
            
            print(f"🌡️  Thermal Monitor — {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 50)
            
            zones = get_thermal_zones()
            throttling = get_throttling()
            freq = get_freq()
            
            print("\nTemperature Zones:")
            for name, temp in zones[:8]:  # Show top 8 zones
                icon = "🔥" if temp > 45 else "⚠️ " if temp > 35 else "✓"
                bar_len = int(temp / 5)
                bar = "█" * bar_len + "░" * (15 - bar_len)
                print(f"  {icon} {name:<20} {temp:5.1f}°C [{bar}]")
            
            if freq:
                print(f"\nCPU Frequency: {freq} MHz")
            
            status = "🔥 THROTTLING" if throttling else "✓ Normal"
            print(f"\nThermal Status: {status}")
            
            print(f"\nRefresh every {args.interval}s | Ctrl+C to stop")
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n\nStopped.")

if __name__ == "__main__":
    main()
