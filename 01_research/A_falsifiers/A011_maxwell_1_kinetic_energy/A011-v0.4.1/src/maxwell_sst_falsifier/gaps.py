from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from .io import ffloat


def classify_amplitude_scans(rows: list[dict[str, str]], abs_gap_floor_eV: float, rel_intercept_tol: float) -> list[dict[str, Any]]:
    """Classify whether an excitation branch extrapolates to a finite energy intercept.

    This is a numerical diagnostic, not proof of a quantum/discrete gap. A finite
    intercept is reported as a *candidate activation threshold*. A branch whose
    energy tends continuously to zero invalidates any claimed positive gap for
    that same coordinate/branch.
    """
    grouped: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        amp = ffloat(row, "amplitude")
        de = ffloat(row, "delta_energy_eV")
        if amp is None or de is None:
            continue
        grouped[(row["knot"], row["mode_id"])].append((amp, de))

    out: list[dict[str, Any]] = []
    for (knot, mode_id), pts in sorted(grouped.items()):
        pts = sorted(pts, key=lambda x: abs(x[0]))
        if len(pts) < 3:
            out.append({"knot": knot, "mode_id": mode_id, "status": "INDETERMINATE", "reason": "need >=3 amplitude points"})
            continue
        # Use lower-amplitude half, minimum 3 points, to target A->0 behavior.
        n = max(3, (len(pts) + 1) // 2)
        small = pts[:n]
        x = np.asarray([a * a for a, _ in small], dtype=float)
        y = np.asarray([e for _, e in small], dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        yhat = slope * x + intercept
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
        scale = max(float(np.median(np.abs(y))), abs_gap_floor_eV)
        threshold = max(abs_gap_floor_eV, rel_intercept_tol * scale)
        if intercept <= threshold:
            status = "CONTINUOUS_TO_ZERO"
        else:
            status = "FINITE_INTERCEPT_CANDIDATE"
        out.append({
            "knot": knot,
            "mode_id": mode_id,
            "status": status,
            "intercept_eV": float(intercept),
            "slope_eV_per_amp2": float(slope),
            "r2": r2,
            "decision_threshold_eV": threshold,
            "n_small_amplitude_points": n,
        })
    return out
