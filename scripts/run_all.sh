#!/usr/bin/env bash
# One-shot: tests -> full demo -> log summary
set -e
cd "$(dirname "$0")/.."
echo "== 1/3 Running unit tests =="
python3 -m unittest discover -s tests -v
echo "== 2/3 Running integrated demo =="
python3 main.py demo
echo "== 3/3 Log summary (Bash) =="
bash scripts/log_summary.sh logs/osim.log
