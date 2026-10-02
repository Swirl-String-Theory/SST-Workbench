from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from .io import ffloat


def spectroscopy_bound(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        grouped[r["observable_id"]].append(r)
    out = []
    for obs, rr in sorted(grouped.items()):
        bound = 0.0
        limit = None
        for r in rr:
            lam = abs(ffloat(r, "lambda_abs", 0.0) or 0.0)
            p = max(0.0, ffloat(r, "occupation", 0.0) or 0.0)
            de = abs(ffloat(r, "delta_energy_eV", 0.0) or 0.0)
            bound += lam * p * de
            l = ffloat(r, "empirical_limit_eV")
            if l is not None:
                limit = l if limit is None else min(limit, l)
        status = "INDETERMINATE" if limit is None else ("FAIL" if bound > limit else "PASS")
        out.append({"observable_id": obs, "predicted_bound_eV": bound, "empirical_limit_eV": limit, "status": status})
    return out


def orientation_Q(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        grouped[r["knot"]].append(r)
    out = []
    for knot, rr in sorted(grouped.items()):
        acc = np.zeros((3, 3), dtype=float)
        wsum = 0.0
        for r in rr:
            t = np.asarray([ffloat(r, "tx", 0.0), ffloat(r, "ty", 0.0), ffloat(r, "tz", 0.0)], dtype=float)
            norm = float(np.linalg.norm(t))
            if norm == 0:
                continue
            t /= norm
            w = ffloat(r, "weight", 1.0) or 1.0
            acc += w * np.outer(t, t)
            wsum += w
        if wsum == 0:
            out.append({"knot": knot, "status": "INDETERMINATE"})
            continue
        q = acc / wsum - np.eye(3) / 3.0
        out.append({"knot": knot, "Q": q.tolist(), "Q_frobenius": float(np.linalg.norm(q))})
    return out


def kinetic_stress(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        grouped[r["knot"]].append(r)
    out = []
    for knot, rr in sorted(grouped.items()):
        acc = np.zeros((3, 3), dtype=float)
        wsum = 0.0
        n = None
        mass = None
        for r in rr:
            m = ffloat(r, "M_kg")
            if m is None or m <= 0:
                continue
            c = np.asarray([ffloat(r, "cx", 0.0), ffloat(r, "cy", 0.0), ffloat(r, "cz", 0.0)], dtype=float)
            w = ffloat(r, "weight", 1.0) or 1.0
            acc += w * np.outer(c, c) / m
            wsum += w
            mass = m
            nr = ffloat(r, "number_density_m3")
            if nr is not None:
                n = nr
        if wsum == 0 or n is None:
            out.append({"knot": knot, "status": "INDETERMINATE", "reason": "need momenta, mass and number_density_m3"})
            continue
        pi = n * acc / wsum
        out.append({"knot": knot, "M_kg": mass, "Pi_Pa": pi.tolist(), "p_knot_Pa": float(np.trace(pi) / 3.0)})
    return out
