"""Python <-> Bash integration: runs helper shell scripts and parses their output."""
import os
import shutil
import subprocess

from .logger import get_logger

log = get_logger("osim.bash")
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def run_script(name, *args, timeout=15):
    """Run scripts/<name> with bash. Returns (ok, stdout_or_error)."""
    bash = shutil.which("bash")
    path = os.path.join(SCRIPT_DIR, name)
    if bash is None:
        return False, "bash is not available on this system (use WSL/Git-Bash on Windows)"
    if not os.path.isfile(path):
        return False, f"script not found: {path}"
    try:
        proc = subprocess.run([bash, path, *map(str, args)], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.error("script %s timed out", name)
        return False, f"{name} timed out after {timeout}s"
    if proc.returncode != 0:
        log.error("script %s failed rc=%d: %s", name, proc.returncode, proc.stderr.strip())
        return False, proc.stderr.strip() or f"{name} exited with {proc.returncode}"
    log.info("script %s ok", name)
    return True, proc.stdout


def parse_kv(text):
    """Parse KEY=VALUE lines emitted by the shell scripts."""
    data = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def system_info():
    ok, out = run_script("sysinfo.sh")
    return (True, parse_kv(out)) if ok else (False, out)


def log_summary(logfile):
    ok, out = run_script("log_summary.sh", logfile)
    return (True, parse_kv(out)) if ok else (False, out)
