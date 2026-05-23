#!/bin/bash
# ADB Device Performance Monitor
# Real-time monitoring: CPU, memory, battery, thermal, FPS
# Usage: ./adb-device-monitor.sh [--interval 5] [--duration 60]

INTERVAL=${INTERVAL:-2}
DURATION=${DURATION:-30}

while [[ $# -gt 0 ]]; do
  case $1 in
    --interval) INTERVAL=$2; shift 2 ;;
    --duration) DURATION=$2; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if ! command -v adb &>/dev/null; then
  echo "ERROR: adb not found. Install Android SDK Platform Tools."
  exit 1
fi

echo "========================================="
echo "ADB Device Performance Monitor"
echo "========================================="
echo "Interval: ${INTERVAL}s | Duration: ${DURATION}s"
echo ""

ELAPSED=0
while [ $ELAPSED -lt $DURATION ]; do
  echo "[$(date '+%H:%M:%S')] CPU & Memory:"
  
  # CPU info
  CPU_LOAD=$(adb shell cat /proc/loadavg 2>/dev/null | awk '{print $1, $2, $3}')
  echo "  Load: $CPU_LOAD"
  
  # Memory info
  MEM=$(adb shell cat /proc/meminfo 2>/dev/null | head -2)
  TOTAL=$(echo "$MEM" | grep MemTotal | awk '{print $2}')
  FREE=$(echo "$MEM" | grep MemFree | awk '{print $2}')
  USED=$((TOTAL - FREE))
  PERCENT=$((USED * 100 / TOTAL))
  echo "  Memory: ${USED}KB / ${TOTAL}KB (${PERCENT}%)"
  
  # Battery
  BATTERY=$(adb shell dumpsys battery 2>/dev/null | grep "level:" | awk '{print $2}')
  TEMP=$(adb shell dumpsys battery 2>/dev/null | grep "temperature:" | awk '{print $2}')
  echo "  Battery: ${BATTERY}% | Temp: ${TEMP}°C"
  
  # Thermal zone
  THERMAL=$(adb shell cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | head -c 2)
  if [ -n "$THERMAL" ]; then
    echo "  Thermal Zone 0: ${THERMAL}°C"
  fi
  
  # Top processes by CPU
  echo "  Top processes (CPU):"
  adb shell ps aux 2>/dev/null | awk 'NR>1 {print $2, $8}' | sort -k2 -rn | head -3 | while read pid cpu; do
    name=$(adb shell ps aux 2>/dev/null | awk -v p="$pid" '$2==p {print $NF}')
    echo "    $name (CPU: ${cpu}%)"
  done
  
  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
  echo ""
done

echo "Monitor finished."
