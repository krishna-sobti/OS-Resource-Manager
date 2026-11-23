# Capstone Report - OSim: Integrated OS Resource-Management Simulator

## 1. Objective
Design one Python-and-Bash application that simulates scheduling, memory, deadlock and storage management and
presents clear analytical results (see `docs/DESIGN.md` for architecture and data design).

## 2. Implementation summary
Four OS modules (scheduling, memory, deadlock, storage) share one validation layer, one logger and one reporting
module, and are driven from a single menu (`main.py`). Bash scripts report live host metrics (`sysinfo.sh`) and
summarise the activity log (`log_summary.sh`); Python calls them with `subprocess`, with timeout and error handling.

## 3. Results (sample datasets; full traces in `outputs/`)
**CPU scheduling** - 6 processes:

| Algorithm | Avg waiting | Avg turnaround | Avg response |
|---|---|---|---|
| FCFS | 13.17 | 18.83 | 13.17 |
| SJF | 10.00 | 15.67 | 10.00 |
| SRTF | **8.50** | **14.17** | 5.67 |
| RR (q=3) | 17.83 | 23.50 | 5.67 |
| Priority | 12.67 | 18.33 | 12.67 |

On the 40-process dataset SRTF (120.4) and SJF (120.9) again beat FCFS (183.4); Round Robin has the worst waiting
time (252.9) but the best response time (46.3 versus 119.9 for SRTF).

**Memory** - classic 20-reference string, 3 frames: FIFO 15 faults, LRU 12, Optimal 9. On the 300-reference
locality-biased string with 4 frames: FIFO 145, LRU 144, Optimal 110. Best-fit placed all four requests in the
allocation experiment, while first-fit and worst-fit left the 426 request unplaced.

**Deadlock** - the 5-process / 3-resource state is safe with sequence P1 -> P3 -> P4 -> P0 -> P2. A request by P1 for
(1,0,2) is granted; P4 asking for (3,3,0) is denied because it would be unsafe; a request above the declared maximum
is rejected. The detection scenario reports P1-P4 deadlocked.

**Storage** - head 53, queue of 8: FCFS 640, SSTF 236, SCAN 331, C-SCAN 382, LOOK 299 cylinders. On the 40-request
queue FCFS needs 7023 versus about 890 for SSTF/LOOK.

## 4. Technical observations
* Shortest-job policies minimise waiting but can starve long jobs (P3 waits longest under SJF/SRTF); Round Robin trades
  higher waiting time for fair, fast first response.
* LRU approaches Optimal when references show locality; FIFO is slightly worse and can exhibit Belady's anomaly
  (verified in the test suite: 9 faults with 3 frames, 10 with 4 on the classic string).
* Seek-optimising algorithms (SSTF/LOOK/SCAN) cut head movement by roughly 63% (small queue) to 87% (40-request queue) versus FCFS; SSTF can starve distant
  requests, SCAN/C-SCAN give bounded waiting.
* Banker's algorithm avoids deadlock by refusing requests that leave no safe sequence, at the cost of delaying requests.

## 5. Testing and reliability
31 automated tests (`outputs/test_results.txt`) cover valid, invalid and boundary cases: known textbook results,
empty/duplicate/negative/non-numeric input, zero quantum or frames, malformed CSV/JSON, missing files, head outside the
disk, single-process and single-frame boundaries, and garbage typed into the menu. Invalid input never crashes the
program - it is rejected with a message and logged (`logs/osim.log`: INFO/WARNING/ERROR counts shown by the Bash
log summarizer). Evidence: `outputs/invalid_input_trace.txt`.

## 6. Limitations / future work
Context-switch cost, multi-level feedback queues, multiple-instance resource graphs, and a GUI are not modelled.

## 7. Originality
All algorithms, the validation layer, the Python-Bash bridge, datasets and tests were written for this project.
