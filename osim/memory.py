"""Module 2 - Memory management: page replacement + contiguous allocation."""
from .logger import get_logger
from .validation import ValidationError, positive_int

log = get_logger("osim.memory")


def _check(refs, frames):
    if not refs:
        raise ValidationError("page reference string is empty")
    return positive_int(frames, "frame count", 1, 1000)


def _finish(name, refs, faults, trace, frames):
    n = len(refs)
    log.info("%s: frames=%d refs=%d faults=%d", name, frames, n, faults)
    return {"name": name, "frames": frames, "faults": faults, "hits": n - faults,
            "fault_rate": faults / n, "trace": trace}


def fifo(refs, frames):
    frames = _check(refs, frames)
    mem, trace, faults = [], [], 0
    for page in refs:
        fault = page not in mem
        if fault:
            faults += 1
            if len(mem) == frames:
                mem.pop(0)
            mem.append(page)
        trace.append((page, list(mem), fault))
    return _finish("FIFO", refs, faults, trace, frames)


def lru(refs, frames):
    frames = _check(refs, frames)
    mem, trace, faults = [], [], 0          # most recently used at the end
    for page in refs:
        fault = page not in mem
        if fault:
            faults += 1
            if len(mem) == frames:
                mem.pop(0)
        else:
            mem.remove(page)
        mem.append(page)
        trace.append((page, list(mem), fault))
    return _finish("LRU", refs, faults, trace, frames)


def optimal(refs, frames):
    frames = _check(refs, frames)
    mem, trace, faults = [], [], 0
    for i, page in enumerate(refs):
        fault = page not in mem
        if fault:
            faults += 1
            if len(mem) == frames:
                future = refs[i + 1:]
                victim = max(mem, key=lambda p: future.index(p) if p in future else len(future) + 1)
                mem[mem.index(victim)] = page
            else:
                mem.append(page)
        trace.append((page, list(mem), fault))
    return _finish("Optimal", refs, faults, trace, frames)


def compare_replacement(refs, frames):
    return [fifo(refs, frames), lru(refs, frames), optimal(refs, frames)]


def allocate(blocks, requests, strategy="first"):
    """Contiguous allocation. strategy in {first, best, worst}."""
    if strategy not in ("first", "best", "worst"):
        raise ValidationError("strategy must be first, best or worst")
    if not blocks or not requests:
        raise ValidationError("blocks and requests must be non-empty")
    if any(b <= 0 for b in blocks) or any(r <= 0 for r in requests):
        raise ValidationError("sizes must be positive")
    free = list(blocks)
    placement = []
    for size in requests:
        fits = [i for i, b in enumerate(free) if b >= size]
        if not fits:
            placement.append((size, None))
            continue
        if strategy == "first":
            idx = fits[0]
        elif strategy == "best":
            idx = min(fits, key=lambda i: free[i])
        else:
            idx = max(fits, key=lambda i: free[i])
        free[idx] -= size
        placement.append((size, idx))
    unplaced = [s for s, i in placement if i is None]
    log.info("allocation %s-fit: unplaced=%d leftover=%d", strategy, len(unplaced), sum(free))
    return {"strategy": strategy, "placement": placement, "remaining": free,
            "external_fragmentation": sum(free), "unplaced": unplaced,
            "largest_hole": max(free)}
