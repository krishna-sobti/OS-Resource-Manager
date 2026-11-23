"""Input validation helpers + dataset loaders (invalid/boundary input handling)."""
import csv
import json
import os


class ValidationError(ValueError):
    """Raised when user input or a dataset is invalid."""


def positive_int(value, name="value", minimum=1, maximum=10**6):
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be an integer, got {value!r}")
    if number < minimum or number > maximum:
        raise ValidationError(f"{name} must be between {minimum} and {maximum}, got {number}")
    return number


def int_list(text, name="list", minimum=0, maximum=10**6, allow_empty=False):
    parts = str(text).replace(",", " ").split()
    if not parts and not allow_empty:
        raise ValidationError(f"{name} must not be empty")
    return [positive_int(p, name, minimum, maximum) for p in parts]


def _require_file(path):
    if not os.path.isfile(path):
        raise ValidationError(f"File not found: {path}")


def load_processes(path):
    from .scheduler import Process
    _require_file(path)
    procs, seen = [], set()
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        needed = {"pid", "arrival", "burst"}
        if not reader.fieldnames or not needed.issubset(set(reader.fieldnames)):
            raise ValidationError(f"CSV needs columns {sorted(needed)} (+ optional priority)")
        for line, row in enumerate(reader, start=2):
            pid = (row["pid"] or "").strip()
            if not pid:
                raise ValidationError(f"line {line}: empty pid")
            if pid in seen:
                raise ValidationError(f"line {line}: duplicate pid {pid}")
            seen.add(pid)
            arrival = positive_int(row["arrival"], f"line {line} arrival", 0)
            burst = positive_int(row["burst"], f"line {line} burst", 1)
            prio = positive_int(row.get("priority") or 0, f"line {line} priority", 0)
            procs.append(Process(pid, arrival, burst, prio))
    if not procs:
        raise ValidationError("process file contains no rows")
    return procs


def load_page_refs(path):
    _require_file(path)
    with open(path, encoding="utf-8") as fh:
        return int_list(fh.read(), "page reference", 0, 10**4)


def load_disk_requests(path):
    _require_file(path)
    with open(path, encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    if len(lines) < 3:
        raise ValidationError("disk file needs: head, max_cylinder, then request list")
    head = positive_int(lines[0], "head", 0)
    max_cyl = positive_int(lines[1], "max cylinder", 1)
    reqs = int_list(lines[2], "request", 0, max_cyl)
    if head > max_cyl:
        raise ValidationError("head position exceeds max cylinder")
    return head, max_cyl, reqs


def load_banker(path):
    _require_file(path)
    with open(path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON: {exc}")
    for key in ("available", "allocation", "max"):
        if key not in data:
            raise ValidationError(f"missing key '{key}' in banker file")
    validate_matrices(data["available"], data["allocation"], data["max"])
    return data


def validate_matrices(available, allocation, maximum):
    m = len(available)
    if m == 0 or len(allocation) == 0 or len(allocation) != len(maximum):
        raise ValidationError("matrices must be non-empty and the same height")
    for i, (a, mx) in enumerate(zip(allocation, maximum)):
        if len(a) != m or len(mx) != m:
            raise ValidationError(f"row {i} width differs from resource count {m}")
        if any(x < 0 for x in a + mx):
            raise ValidationError(f"row {i} contains negative values")
        if any(x > y for x, y in zip(a, mx)):
            raise ValidationError(f"row {i}: allocation exceeds declared maximum")
    if any(x < 0 for x in available):
        raise ValidationError("available contains negative values")
