"""Module 5 - Reporting: ASCII tables and PNG charts."""
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")


def table(headers, rows, title=None):
    rows = [[str(c) for c in r] for r in rows]
    widths = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    fmt = lambda cells: "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"
    out = ([title] if title else []) + [line, fmt(headers), line] + [fmt(r) for r in rows] + [line]
    return "\n".join(out)


def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        return None


def bar_chart(labels, values, title, ylabel, filename):
    plt = _plt()
    if plt is None:
        return None
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color="#3b6ea8")
    ax.bar_label(bars, fmt="%.2f", fontsize=8)
    ax.set_title(title); ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return path


def grouped_chart(labels, series, title, ylabel, filename):
    """series: {name: [values per label]}"""
    plt = _plt()
    if plt is None:
        return None
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    width = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, (name, vals) in enumerate(series.items()):
        ax.bar([i + k * width for i in range(len(labels))], vals, width, label=name)
    ax.set_xticks([i + width * (len(series) - 1) / 2 for i in range(len(labels))])
    ax.set_xticklabels(labels)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return path


def gantt_chart(result, filename):
    plt = _plt()
    if plt is None:
        return None
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    pids = sorted({g[0] for g in result["gantt"] if g[0] != "IDLE"})
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(pids) + 1.5))
    for pid, s, e in result["gantt"]:
        if pid != "IDLE":
            ax.barh(pids.index(pid), e - s, left=s, edgecolor="white")
    ax.set_yticks(range(len(pids))); ax.set_yticklabels(pids)
    ax.set_xlabel("Time"); ax.set_title(f"Gantt chart - {result['name']}")
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return path


def line_chart(xs, series, title, xlabel, ylabel, filename):
    plt = _plt()
    if plt is None:
        return None
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    fig, ax = plt.subplots(figsize=(7, 4))
    for name, ys in series.items():
        ax.plot(xs, ys, marker="o", label=name)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=120); plt.close(fig)
    return path
