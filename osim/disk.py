"""Module 4 - Storage: disk-scheduling algorithms."""
from .logger import get_logger
from .validation import ValidationError

log = get_logger("osim.disk")


def _check(head, max_cyl, reqs):
    if not reqs:
        raise ValidationError("request queue is empty")
    if not 0 <= head <= max_cyl:
        raise ValidationError("head must lie within the disk")
    if any(r < 0 or r > max_cyl for r in reqs):
        raise ValidationError("request outside disk range")


def _out(name, head, order):
    pos, total = head, 0
    for cyl in order:
        total += abs(cyl - pos)
        pos = cyl
    log.info("%s: movement=%d", name, total)
    return {"name": name, "order": order, "movement": total}


def fcfs(head, max_cyl, reqs):
    _check(head, max_cyl, reqs)
    return _out("FCFS", head, list(reqs))


def sstf(head, max_cyl, reqs):
    _check(head, max_cyl, reqs)
    pending, pos, order = list(reqs), head, []
    while pending:
        nxt = min(pending, key=lambda r: (abs(r - pos), r))
        pending.remove(nxt); order.append(nxt); pos = nxt
    return _out("SSTF", head, order)


def _split(head, reqs):
    return sorted(r for r in reqs if r < head), sorted(r for r in reqs if r >= head)


def scan(head, max_cyl, reqs, direction="up"):
    _check(head, max_cyl, reqs)
    lower, upper = _split(head, reqs)
    if direction == "up":
        order = upper + ([max_cyl] if lower else []) + lower[::-1]
    else:
        order = lower[::-1] + ([0] if upper else []) + upper
    return _out("SCAN", head, [c for c in order])


def cscan(head, max_cyl, reqs):
    _check(head, max_cyl, reqs)
    lower, upper = _split(head, reqs)
    order = upper + ([max_cyl, 0] if lower else []) + lower
    return _out("C-SCAN", head, order)


def look(head, max_cyl, reqs, direction="up"):
    _check(head, max_cyl, reqs)
    lower, upper = _split(head, reqs)
    order = upper + lower[::-1] if direction == "up" else lower[::-1] + upper
    return _out("LOOK", head, order)


def compare(head, max_cyl, reqs):
    return [fcfs(head, max_cyl, reqs), sstf(head, max_cyl, reqs), scan(head, max_cyl, reqs),
            cscan(head, max_cyl, reqs), look(head, max_cyl, reqs)]
