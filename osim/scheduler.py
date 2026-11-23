"""Module 1 - CPU scheduling: FCFS, SJF, SRTF, Round Robin, Priority."""
from collections import deque
from dataclasses import dataclass

from .logger import get_logger
from .validation import ValidationError, positive_int

log = get_logger("osim.scheduler")


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0


def _merge(gantt):
    merged = []
    for pid, s, e in gantt:
        if merged and merged[-1][0] == pid and merged[-1][2] == s:
            merged[-1] = (pid, merged[-1][1], e)
        else:
            merged.append((pid, s, e))
    return merged


def _result(name, procs, gantt, comp, first):
    rows = []
    for p in procs:
        tat = comp[p.pid] - p.arrival
        rows.append({"pid": p.pid, "arrival": p.arrival, "burst": p.burst,
                     "completion": comp[p.pid], "turnaround": tat,
                     "waiting": tat - p.burst, "response": first[p.pid] - p.arrival})
    n = len(rows)
    total_time = max(r["completion"] for r in rows) - min(p.arrival for p in procs)
    busy = sum(p.burst for p in procs)
    res = {"name": name, "gantt": _merge(gantt), "rows": rows,
           "avg_waiting": sum(r["waiting"] for r in rows) / n,
           "avg_turnaround": sum(r["turnaround"] for r in rows) / n,
           "avg_response": sum(r["response"] for r in rows) / n,
           "cpu_utilisation": 100.0 * busy / total_time if total_time else 100.0,
           "throughput": n / total_time if total_time else float(n)}
    log.info("%s finished: avg_wait=%.2f avg_tat=%.2f", name, res["avg_waiting"], res["avg_turnaround"])
    return res


def _check(procs):
    if not procs:
        raise ValidationError("no processes supplied")
    if len({p.pid for p in procs}) != len(procs):
        raise ValidationError("duplicate process ids")


def _nonpreemptive(name, procs, key):
    _check(procs)
    pending = list(procs)
    time, gantt, comp, first = 0, [], {}, {}
    while pending:
        ready = [p for p in pending if p.arrival <= time]
        if not ready:
            nxt = min(p.arrival for p in pending)
            gantt.append(("IDLE", time, nxt))
            time = nxt
            continue
        p = min(ready, key=key)
        pending.remove(p)
        first[p.pid] = time
        gantt.append((p.pid, time, time + p.burst))
        time += p.burst
        comp[p.pid] = time
    return _result(name, procs, gantt, comp, first)


def fcfs(procs):
    return _nonpreemptive("FCFS", procs, lambda p: (p.arrival, p.pid))


def sjf(procs):
    return _nonpreemptive("SJF", procs, lambda p: (p.burst, p.arrival, p.pid))


def priority(procs):
    return _nonpreemptive("Priority", procs, lambda p: (p.priority, p.arrival, p.pid))


def srtf(procs):
    _check(procs)
    rem = {p.pid: p.burst for p in procs}
    time, done, gantt, comp, first = 0, 0, [], {}, {}
    while done < len(procs):
        ready = [p for p in procs if p.arrival <= time and rem[p.pid] > 0]
        if not ready:
            nxt = min(p.arrival for p in procs if rem[p.pid] > 0)
            gantt.append(("IDLE", time, nxt))
            time = nxt
            continue
        p = min(ready, key=lambda q: (rem[q.pid], q.arrival, q.pid))
        first.setdefault(p.pid, time)
        gantt.append((p.pid, time, time + 1))
        rem[p.pid] -= 1
        time += 1
        if rem[p.pid] == 0:
            comp[p.pid] = time
            done += 1
    return _result("SRTF", procs, gantt, comp, first)


def round_robin(procs, quantum=2):
    _check(procs)
    quantum = positive_int(quantum, "time quantum", 1, 1000)
    order = sorted(procs, key=lambda p: (p.arrival, p.pid))
    rem = {p.pid: p.burst for p in procs}
    queue, idx, time, done = deque(), 0, 0, 0
    gantt, comp, first = [], {}, {}
    while done < len(procs):
        while idx < len(order) and order[idx].arrival <= time:
            queue.append(order[idx]); idx += 1
        if not queue:
            nxt = order[idx].arrival
            gantt.append(("IDLE", time, nxt)); time = nxt
            continue
        p = queue.popleft()
        first.setdefault(p.pid, time)
        run = min(quantum, rem[p.pid])
        gantt.append((p.pid, time, time + run))
        time += run
        rem[p.pid] -= run
        while idx < len(order) and order[idx].arrival <= time:
            queue.append(order[idx]); idx += 1
        if rem[p.pid] > 0:
            queue.append(p)
        else:
            comp[p.pid] = time
            done += 1
    return _result(f"RR(q={quantum})", procs, gantt, comp, first)


def run_all(procs, quantum=2):
    """Run every algorithm on the same dataset for comparison."""
    return [fcfs(procs), sjf(procs), srtf(procs), round_robin(procs, quantum), priority(procs)]


def gantt_text(result):
    return " ".join(f"|{pid} {s}-{e}" for pid, s, e in result["gantt"]) + "|"
