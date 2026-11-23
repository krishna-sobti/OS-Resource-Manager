#!/usr/bin/env bash
# Usage: log_summary.sh <logfile>   -> KEY=VALUE counts of log levels per module
set -u
file="${1:-}"
if [ -z "$file" ]; then echo "usage: $0 <logfile>" >&2; exit 2; fi
if [ ! -f "$file" ]; then echo "log file not found: $file" >&2; exit 1; fi
echo "TOTAL_LINES=$(wc -l < "$file" | tr -d ' ')"
echo "INFO=$(grep -c '| INFO ' "$file")"
echo "WARNING=$(grep -c '| WARNING ' "$file")"
echo "ERROR=$(grep -c '| ERROR ' "$file")"
for m in scheduler memory deadlock disk bash; do
  echo "MODULE_${m}=$(grep -c "osim\.${m} " "$file")"
done
