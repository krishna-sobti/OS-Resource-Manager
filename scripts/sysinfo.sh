#!/usr/bin/env bash
# Prints live host resource figures as KEY=VALUE lines (parsed by osim/bashbridge.py)
set -u
echo "HOSTNAME=$(hostname)"
echo "KERNEL=$(uname -sr)"
echo "CPU_CORES=$(nproc 2>/dev/null || echo 1)"
read -r l1 l5 l15 _ < /proc/loadavg 2>/dev/null || { l1=0; l5=0; l15=0; }
echo "LOAD_1M=$l1"
echo "LOAD_5M=$l5"
echo "LOAD_15M=$l15"
if [ -r /proc/meminfo ]; then
  total=$(awk '/^MemTotal:/ {print int($2/1024)}' /proc/meminfo)
  avail=$(awk '/^MemAvailable:/ {print int($2/1024)}' /proc/meminfo)
  echo "MEM_TOTAL_MB=$total"
  echo "MEM_AVAILABLE_MB=$avail"
  echo "MEM_USED_PCT=$(awk -v t="$total" -v a="$avail" 'BEGIN{ if (t>0) printf "%.1f", (t-a)*100/t; else print 0 }')"
fi
echo "DISK_ROOT_USED_PCT=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')"
echo "PROCESS_COUNT=$(ps -e --no-headers 2>/dev/null | wc -l)"
