from __future__ import annotations

from collections import defaultdict
from typing import Any

from .io import ffloat


def rel_change(a: float, b: float, floor: float = 1e-300) -> float:
    return abs(b - a) / max(abs(a), abs(b), floor)


def convergence_audit(rows: list[dict[str, str]], rel_tol: float) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        grouped[(r["knot"], r["mode_id"])].append(r)
    out = []
    metrics = ["omega_rad_s", "coupling_norm", "gap_eV"]
    for (knot, mode_id), rr in sorted(grouped.items()):
        rr.sort(key=lambda r: ffloat(r, "resolution", 0.0) or 0.0)
        if len(rr) < 2:
            out.append({"knot": knot, "mode_id": mode_id, "status": "INDETERMINATE", "reason": "need >=2 resolutions"})
            continue
        prev, last = rr[-2], rr[-1]
        changes = {}
        failed = []
        for m in metrics:
            a, b = ffloat(prev, m), ffloat(last, m)
            if a is None or b is None:
                continue
            rc = rel_change(a, b)
            changes[m] = rc
            if rc > rel_tol:
                failed.append(m)
        status = "PASS" if changes and not failed else ("FAIL" if failed else "INDETERMINATE")
        out.append({"knot": knot, "mode_id": mode_id, "status": status, "relative_changes": changes, "failed_metrics": failed})
    return out
