"""Module 3 - Deadlock: Banker's algorithm (avoidance) + detection."""
from .logger import get_logger
from .validation import ValidationError, validate_matrices

log = get_logger("osim.deadlock")


def need_matrix(allocation, maximum):
    return [[mx - al for mx, al in zip(mrow, arow)] for mrow, arow in zip(maximum, allocation)]


def safety_check(available, allocation, maximum):
    """Return (is_safe, safe_sequence, steps)."""
    validate_matrices(available, allocation, maximum)
    need = need_matrix(allocation, maximum)
    work, n = list(available), len(allocation)
    finished, seq, steps = [False] * n, [], []
    progress = True
    while progress:
        progress = False
        for i in range(n):
            if not finished[i] and all(nd <= w for nd, w in zip(need[i], work)):
                work = [w + a for w, a in zip(work, allocation[i])]
                finished[i] = True
                seq.append(f"P{i}")
                steps.append((f"P{i}", list(work)))
                progress = True
    safe = all(finished)
    log.info("safety check: safe=%s sequence=%s", safe, seq)
    return safe, seq, steps


def request_resources(available, allocation, maximum, pid, request):
    """Banker's resource-request algorithm. Returns (granted, message)."""
    n, m = len(allocation), len(available)
    if not 0 <= pid < n:
        raise ValidationError(f"process index must be 0..{n - 1}")
    if len(request) != m or any(r < 0 for r in request):
        raise ValidationError(f"request must be {m} non-negative integers")
    need = need_matrix(allocation, maximum)
    if any(r > nd for r, nd in zip(request, need[pid])):
        return False, "DENIED: request exceeds the process's declared maximum need"
    if any(r > a for r, a in zip(request, available)):
        return False, "DENIED (wait): resources not currently available"
    new_avail = [a - r for a, r in zip(available, request)]
    new_alloc = [list(row) for row in allocation]
    new_alloc[pid] = [a + r for a, r in zip(new_alloc[pid], request)]
    safe, seq, _ = safety_check(new_avail, new_alloc, maximum)
    if safe:
        msg = "GRANTED: system stays safe, sequence " + " -> ".join(seq)
        log.info("request P%d %s granted", pid, request)
        return True, msg
    log.warning("request P%d %s denied - would be unsafe", pid, request)
    return False, "DENIED: granting would leave the system in an UNSAFE state"


def detect_deadlock(available, allocation, request):
    """Detection with a request matrix. Returns list of deadlocked process names."""
    n = len(allocation)
    work, finish = list(available), [all(x == 0 for x in allocation[i]) for i in range(n)]
    changed = True
    while changed:
        changed = False
        for i in range(n):
            if not finish[i] and all(r <= w for r, w in zip(request[i], work)):
                work = [w + a for w, a in zip(work, allocation[i])]
                finish[i] = True
                changed = True
    dead = [f"P{i}" for i in range(n) if not finish[i]]
    log.info("deadlock detection: %s", dead or "none")
    return dead
