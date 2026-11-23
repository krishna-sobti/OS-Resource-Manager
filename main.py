#!/usr/bin/env python3
"""OSim - integrated OS resource-management simulator (entry point).

Usage:
    python3 main.py            interactive menu
    python3 main.py demo       run every module on the bundled datasets
    python3 main.py demo --large   use the larger generated datasets
"""
import argparse
import os
import sys

from osim import bashbridge, deadlock, disk, memory, report, scheduler, validation
from osim.logger import LOG_FILE, get_logger
from osim.validation import ValidationError

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
log = get_logger("osim.main")
TRANSCRIPT = []


def emit(text=""):
    print(text)
    TRANSCRIPT.append(str(text))


def banner(text):
    emit("\n" + "=" * 70)
    emit(f" {text}")
    emit("=" * 70)


# ---------------------------------------------------------------- scheduling
def show_scheduling(procs, quantum=2, charts=True):
    banner("MODULE 1 - CPU SCHEDULING")
    emit(report.table(["PID", "Arrival", "Burst", "Priority"],
                      [(p.pid, p.arrival, p.burst, p.priority) for p in procs], "Input dataset"))
    results = scheduler.run_all(procs, quantum)
    for r in results:
        emit(f"\n{r['name']}  Gantt: {scheduler.gantt_text(r)}")
        emit(report.table(["PID", "CT", "TAT", "WT", "RT"],
                          [(x["pid"], x["completion"], x["turnaround"], x["waiting"], x["response"])
                           for x in r["rows"]]))
    emit(report.table(["Algorithm", "Avg WT", "Avg TAT", "Avg RT", "CPU %", "Throughput"],
                      [(r["name"], f"{r['avg_waiting']:.2f}", f"{r['avg_turnaround']:.2f}",
                        f"{r['avg_response']:.2f}", f"{r['cpu_utilisation']:.1f}",
                        f"{r['throughput']:.3f}") for r in results], "\nAlgorithm comparison"))
    best = min(results, key=lambda r: r["avg_waiting"])
    emit(f"Observation: {best['name']} gives the lowest average waiting time ({best['avg_waiting']:.2f}).")
    if charts:
        labels = [r["name"] for r in results]
        report.grouped_chart(labels, {"Avg waiting": [r["avg_waiting"] for r in results],
                                      "Avg turnaround": [r["avg_turnaround"] for r in results],
                                      "Avg response": [r["avg_response"] for r in results]},
                             "Scheduling comparison", "Time units", "scheduling_comparison.png")
        report.gantt_chart(results[3], "gantt_round_robin.png")
        emit("Charts saved: outputs/scheduling_comparison.png, outputs/gantt_round_robin.png")
    return results


# -------------------------------------------------------------------- memory
def show_memory(refs, frames=3, charts=True):
    banner("MODULE 2 - MEMORY MANAGEMENT")
    emit(f"Reference string ({len(refs)} refs): {' '.join(map(str, refs[:30]))}{' ...' if len(refs) > 30 else ''}")
    results = memory.compare_replacement(refs, frames)
    emit(report.table(["Algorithm", "Frames", "Faults", "Hits", "Fault rate"],
                      [(r["name"], r["frames"], r["faults"], r["hits"], f"{r['fault_rate']:.1%}")
                       for r in results], f"\nPage replacement ({frames} frames)"))
    emit("\nLRU trace (first 10 refs):")
    for page, mem, fault in memory.lru(refs, frames)["trace"][:10]:
        emit(f"  ref {page:>3} -> frames {mem!s:<18} {'FAULT' if fault else 'hit'}")
    max_f = min(8, len(set(refs)))
    xs = list(range(1, max_f + 1))
    series = {n: [getattr(memory, f)(refs, k)["faults"] for k in xs]
              for n, f in (("FIFO", "fifo"), ("LRU", "lru"), ("Optimal", "optimal"))}
    emit(report.table(["Frames"] + list(series), [[k] + [series[n][i] for n in series] for i, k in enumerate(xs)],
                      "\nPage faults vs. frame count"))
    fifo_f = series["FIFO"]
    if any(fifo_f[i + 1] > fifo_f[i] for i in range(len(fifo_f) - 1)):
        emit("Observation: FIFO shows Belady's anomaly on this string (more frames -> more faults).")
    if charts:
        report.line_chart(xs, series, "Page faults vs frames", "Frames", "Faults", "page_faults.png")
        emit("Chart saved: outputs/page_faults.png")

    blocks, reqs = [100, 500, 200, 300, 600], [212, 417, 112, 426]
    emit(f"\nContiguous allocation  blocks={blocks}  requests={reqs}")
    rows = []
    for s in ("first", "best", "worst"):
        a = memory.allocate(blocks, reqs, s)
        rows.append((f"{s}-fit", a["placement"], a["external_fragmentation"], len(a["unplaced"])))
    emit(report.table(["Strategy", "(size, block#)", "Leftover", "Unplaced"], rows))
    return results


# ------------------------------------------------------------------ deadlock
def show_deadlock(data):
    banner("MODULE 3 - DEADLOCK AVOIDANCE / DETECTION")
    av, al, mx = data["available"], data["allocation"], data["max"]
    need = deadlock.need_matrix(al, mx)
    emit(report.table(["Proc", "Allocation", "Max", "Need"],
                      [(f"P{i}", al[i], mx[i], need[i]) for i in range(len(al))],
                      f"Available = {av}"))
    safe, seq, steps = deadlock.safety_check(av, al, mx)
    emit(f"\nSafe state: {safe}   Safe sequence: {' -> '.join(seq) if safe else 'none'}")
    for p, work in steps:
        emit(f"  {p} finishes, Work = {work}")
    emit("\nResource-request tests:")
    for pid, req in ((1, [1, 0, 2]), (4, [3, 3, 0]), (0, [0, 2, 0]), (1, [9, 9, 9])):
        ok, msg = deadlock.request_resources(av, al, mx, pid, req)
        emit(f"  P{pid} requests {req}: {msg}")
    dead = deadlock.detect_deadlock([0, 0, 0],
                                    [[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1], [0, 0, 2]],
                                    [[0, 0, 0], [2, 0, 2], [0, 0, 1], [1, 0, 0], [0, 0, 2]])
    emit(f"\nDetection scenario (extra request by P2): deadlocked = {dead or 'none'}")


# ------------------------------------------------------------------- storage
def show_disk(head, max_cyl, reqs, charts=True):
    banner("MODULE 4 - STORAGE / DISK SCHEDULING")
    emit(f"Head={head}  Cylinders=0..{max_cyl}  Queue={reqs if len(reqs) <= 12 else str(reqs[:12]) + '...'}")
    results = disk.compare(head, max_cyl, reqs)
    emit(report.table(["Algorithm", "Total head movement", "Service order (first 10)"],
                      [(r["name"], r["movement"], r["order"][:10]) for r in results]))
    best = min(results, key=lambda r: r["movement"])
    emit(f"Observation: {best['name']} minimises head movement ({best['movement']} cylinders).")
    if charts:
        report.bar_chart([r["name"] for r in results], [r["movement"] for r in results],
                         "Disk scheduling - total head movement", "Cylinders", "disk_movement.png")
        emit("Chart saved: outputs/disk_movement.png")
    return results


# ----------------------------------------------------------- Bash integration
def show_system():
    banner("BASH INTEGRATION - live system figures (scripts/sysinfo.sh)")
    ok, info = bashbridge.system_info()
    if not ok:
        emit(f"[WARN] Bash helper unavailable: {info}")
        return
    emit(report.table(["Metric", "Value"], list(info.items())))


def show_log_summary():
    banner("BASH INTEGRATION - activity log summary (scripts/log_summary.sh)")
    ok, info = bashbridge.log_summary(LOG_FILE)
    if not ok:
        emit(f"[WARN] {info}")
        return
    emit(report.table(["Field", "Count"], list(info.items())))


# ---------------------------------------------------------------------- demo
def demo(large=False):
    suffix = "_large" if large else ""
    log.info("demo started (large=%s)", large)
    procs = validation.load_processes(os.path.join(DATA, f"processes{suffix}.csv"))
    show_scheduling(procs, quantum=3)
    refs = validation.load_page_refs(os.path.join(DATA, f"page_refs{suffix}.txt"))
    show_memory(refs, frames=4 if large else 3)
    show_deadlock(validation.load_banker(os.path.join(DATA, "banker.json")))
    head, max_cyl, reqs = validation.load_disk_requests(os.path.join(DATA, f"disk_requests{suffix}.txt"))
    show_disk(head, max_cyl, reqs)
    show_system()
    show_log_summary()
    os.makedirs(os.path.join(ROOT, "outputs"), exist_ok=True)
    name = "demo_trace_large.txt" if large else "demo_trace.txt"
    with open(os.path.join(ROOT, "outputs", name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(TRANSCRIPT) + "\n")
    log.info("demo finished")


# ---------------------------------------------------------------- interactive
def ask(prompt, parser):
    while True:
        try:
            return parser(input(prompt))
        except ValidationError as exc:
            print(f"  [!] {exc}")
            log.warning("invalid input: %s", exc)


def custom_processes():
    n = ask("Number of processes (1-20): ", lambda s: validation.positive_int(s, "count", 1, 20))
    procs = []
    for i in range(1, n + 1):
        a = ask(f"  P{i} arrival time: ", lambda s: validation.positive_int(s, "arrival", 0, 1000))
        b = ask(f"  P{i} burst time: ", lambda s: validation.positive_int(s, "burst", 1, 1000))
        p = ask(f"  P{i} priority (lower = higher): ", lambda s: validation.positive_int(s, "priority", 0, 100))
        procs.append(scheduler.Process(f"P{i}", a, b, p))
    return procs


def choose_source(label):
    ans = input(f"{label}: [d]efault sample / [c]ustom input? ").strip().lower()
    return "c" if ans.startswith("c") else "d"


def menu():
    options = """
 1) CPU scheduling          5) System info (Bash)
 2) Memory management       6) Activity-log summary (Bash)
 3) Deadlock (Banker's)     7) Run full demo
 4) Disk scheduling         0) Exit"""
    while True:
        print("\n===== OSim - OS Resource Manager =====" + options)
        choice = input("Select: ").strip()
        try:
            if choice == "1":
                procs = custom_processes() if choose_source("Processes") == "c" else \
                    validation.load_processes(os.path.join(DATA, "processes.csv"))
                q = ask("Round-robin quantum [2]: ", lambda s: validation.positive_int(s or 2, "quantum", 1, 100))
                show_scheduling(procs, q)
            elif choice == "2":
                if choose_source("Reference string") == "c":
                    refs = ask("Pages (space separated): ", lambda s: validation.int_list(s, "page", 0, 9999))
                else:
                    refs = validation.load_page_refs(os.path.join(DATA, "page_refs.txt"))
                frames = ask("Frames [3]: ", lambda s: validation.positive_int(s or 3, "frames", 1, 100))
                show_memory(refs, frames)
            elif choice == "3":
                show_deadlock(validation.load_banker(os.path.join(DATA, "banker.json")))
            elif choice == "4":
                if choose_source("Disk queue") == "c":
                    mc = ask("Max cylinder: ", lambda s: validation.positive_int(s, "max cylinder", 1, 100000))
                    head = ask("Head position: ", lambda s: validation.positive_int(s, "head", 0, mc))
                    reqs = ask("Requests: ", lambda s: validation.int_list(s, "request", 0, mc))
                else:
                    head, mc, reqs = validation.load_disk_requests(os.path.join(DATA, "disk_requests.txt"))
                show_disk(head, mc, reqs)
            elif choice == "5":
                show_system()
            elif choice == "6":
                show_log_summary()
            elif choice == "7":
                demo()
            elif choice == "0":
                print("Goodbye.")
                return
            else:
                print("  [!] Please choose a number from the menu.")
                log.warning("invalid menu choice %r", choice)
        except ValidationError as exc:
            print(f"  [!] {exc}")
            log.error("validation failure: %s", exc)
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted - exiting.")
            return


def main(argv=None):
    parser = argparse.ArgumentParser(description="Integrated OS resource-management simulator")
    parser.add_argument("mode", nargs="?", choices=["menu", "demo"], default="menu")
    parser.add_argument("--large", action="store_true", help="use larger generated datasets (demo)")
    args = parser.parse_args(argv)
    try:
        demo(args.large) if args.mode == "demo" else menu()
    except ValidationError as exc:
        log.error("fatal validation error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
