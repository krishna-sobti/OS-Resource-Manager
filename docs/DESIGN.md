# Phase 1 - System Design and Planning

## Problem statement
Operating systems must share CPU, memory, and disks among competing processes. Choosing the right policy
changes waiting time, page-fault rate, and disk head movement. OSim simulates the main policies on identical
datasets so they can be compared quantitatively.

## Modular architecture
```
                         main.py (menu / demo)
                               |
     +-------------+-----------+-----------+-------------+
 scheduler.py   memory.py   deadlock.py   disk.py    bashbridge.py --> scripts/*.sh
     |             |            |            |             |
     +-------------+-----+------+------------+-------------+
                         |
          validation.py (all input)   logger.py (logs/osim.log)
                         |
                    report.py (tables + charts -> outputs/)
```

## Workflow
`load/validate input -> run algorithms on the same dataset -> compute metrics -> print tables -> save charts
-> log every action -> Bash summarises the log`.

## Data design
| Module | Structure | Notes |
|---|---|---|
| Scheduling | `Process(pid, arrival, burst, priority)` frozen dataclass; Gantt = `[(pid, start, end)]`; result dict with per-process rows | idle gaps recorded as `IDLE` |
| Memory | reference list, frame list, trace `[(page, frames, fault)]` | LRU keeps MRU at the end |
| Deadlock | matrices as `list[list[int]]` (Available, Allocation, Max, Need = Max - Allocation) | validated before use |
| Disk | head, max cylinder, request list; result = service order + total movement | |

## Metrics
Completion, turnaround (CT - arrival), waiting (TAT - burst), response (first run - arrival), CPU utilisation,
throughput; page faults / hits / fault rate; head movement; unplaced requests & fragmentation.

## Implementation plan
1. Validation + logging foundation -> 2. Scheduler -> 3. Memory -> 4. Deadlock -> 5. Disk ->
6. Reporting/charts -> 7. Bash scripts + bridge -> 8. Menu/demo -> 9. Tests -> 10. Docs.
