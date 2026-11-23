# OSim - Integrated OS Resource-Management Simulator (Python + Bash)

One application that simulates five operating-system resource-management functions and reports
the results as tables and charts. Python implements the algorithms; Bash scripts collect live
system figures and summarise the activity log, and Python calls them through `osim/bashbridge.py`.

| Module | File | What it simulates |
|---|---|---|
| Process scheduling | `osim/scheduler.py` | FCFS, SJF, SRTF, Round Robin, Priority |
| Memory management | `osim/memory.py` | FIFO / LRU / Optimal page replacement, first/best/worst-fit allocation |
| Deadlock | `osim/deadlock.py` | Banker's safety + request algorithm, deadlock detection |
| Storage | `osim/disk.py` | FCFS, SSTF, SCAN, C-SCAN, LOOK disk scheduling |
| Reporting | `osim/report.py` | ASCII tables, bar/line/Gantt charts (matplotlib) |
| Bash integration | `scripts/*.sh`, `osim/bashbridge.py` | `sysinfo.sh`, `log_summary.sh`, `run_all.sh` |

## Requirements
* Python 3.8+ and Bash (Linux / macOS / WSL / Git-Bash)
* `pip install matplotlib` (optional - without it only the charts are skipped)

## How to run
```bash
cd os_resource_manager
pip install matplotlib          # optional, for charts

python3 main.py                 # interactive menu
python3 main.py demo            # all modules on the sample datasets
python3 main.py demo --large    # all modules on the 40-process / 300-reference datasets
python3 -m unittest discover -s tests -v     # 31 test cases
bash scripts/run_all.sh         # tests + demo + log summary in one go
```

## Menu
```
1) CPU scheduling        5) System info (Bash)
2) Memory management     6) Activity-log summary (Bash)
3) Deadlock (Banker's)   7) Run full demo
4) Disk scheduling       0) Exit
```
Options 1, 2 and 4 accept either the bundled sample data (`d`) or custom input (`c`).

## Input files (`data/`)
| File | Format |
|---|---|
| `processes.csv`, `processes_large.csv` | `pid,arrival,burst,priority` (header required) |
| `page_refs.txt`, `page_refs_large.txt` | space-separated page numbers |
| `disk_requests*.txt` | head, max cylinder, request list (`#` lines are comments) |
| `banker.json` | `available`, `allocation`, `max` matrices |

## Output / evidence (`outputs/`, `logs/`)
`demo_trace.txt`, `demo_trace_large.txt` (full output traces) - `scheduling_comparison.png`,
`gantt_round_robin.png`, `page_faults.png`, `disk_movement.png` (charts) - `test_results.txt`,
`invalid_input_trace.txt` (testing evidence) - `logs/osim.log` (activity log).

**Screenshots:** run `python3 main.py demo` and `python3 main.py` yourself and capture the terminal
for your submission (put them in a `screenshots/` folder).

## Project layout
```
main.py            menu + demo orchestration
osim/              scheduler, memory, deadlock, disk, report, validation, logger, bashbridge
scripts/           sysinfo.sh, log_summary.sh, run_all.sh
data/              sample + large datasets
tests/test_all.py  31 unit/integration tests
docs/DESIGN.md     phase-1 planning: architecture, data design, plan
REPORT.md          concise project report
```
