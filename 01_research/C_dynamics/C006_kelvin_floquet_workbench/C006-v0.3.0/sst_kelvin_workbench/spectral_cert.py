"""Spectral-certification utilities for C006 v0.3.0.

The routines in this module are deliberately model-agnostic.  They do not assume
that a complex eigenvalue is a quasinormal mode.  For the C006 temporal generator
we use

    lambda = sigma + i*omega,

so Re(lambda) is growth/decay and Im(lambda) is oscillation frequency in the
circulation-clock time variable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
import math
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.linalg import eig as generalized_eig


def _as_complex(values: Iterable[complex]) -> np.ndarray:
    return np.asarray(list(values), dtype=complex).reshape(-1)


def complex_rows(values: Iterable[complex]) -> list[dict[str, float]]:
    return [{"re": float(z.real), "im": float(z.imag), "abs": float(abs(z))}
            for z in _as_complex(values)]


def normalized_distance(a: complex, b: complex, *, floor: float = 1.0e-12) -> float:
    scale = max(abs(a), abs(b), floor)
    return float(abs(a - b) / scale)


def match_spectra(reference: Sequence[complex], candidate: Sequence[complex]) -> dict:
    """Minimum-cost one-to-one matching in the complex plane.

    The metric is scale-normalized complex distance.  The returned candidate
    ordering follows the reference ordering; this is the basic stable-root
    tracking step used by the v0.3 spectral ladder.
    """
    ref = _as_complex(reference)
    cur = _as_complex(candidate)
    if ref.size == 0 or cur.size == 0:
        return {"matched": [], "unmatched_reference": list(range(ref.size)),
                "unmatched_candidate": list(range(cur.size))}
    cost = np.empty((ref.size, cur.size), dtype=float)
    for i, a in enumerate(ref):
        for j, b in enumerate(cur):
            cost[i, j] = normalized_distance(a, b)
    rr, cc = linear_sum_assignment(cost)
    pairs = sorted((int(i), int(j), float(cost[i, j])) for i, j in zip(rr, cc))
    used_r = {i for i, _, _ in pairs}; used_c = {j for _, j, _ in pairs}
    return {
        "matched": [{"reference_index": i, "candidate_index": j, "relative_distance": d}
                    for i, j, d in pairs],
        "unmatched_reference": [i for i in range(ref.size) if i not in used_r],
        "unmatched_candidate": [j for j in range(cur.size) if j not in used_c],
    }


def track_spectrum(levels: Sequence[dict], *, rel_tol: float = 0.08) -> dict:
    """Track eigenvalue branches across a resolution/parameter ladder.

    Each level is ``{"label": ..., "eigenvalues": array_like}``.  Equal spectrum
    dimension is preferred but not required.  Branch identity is propagated by
    Hungarian matching from one level to the next.
    """
    if not levels:
        return {"ok": False, "reason": "NO_LEVELS", "branches": []}
    first = _as_complex(levels[0]["eigenvalues"])
    branches = [[complex(z)] for z in first]
    current = first.copy()
    step_records = []
    complete = True
    for lev in levels[1:]:
        nxt = _as_complex(lev["eigenvalues"])
        mt = match_spectra(current, nxt)
        reordered = np.full(current.shape, np.nan + 1j*np.nan, dtype=complex)
        shifts = np.full(current.shape, np.inf, dtype=float)
        for p in mt["matched"]:
            i = p["reference_index"]; j = p["candidate_index"]
            reordered[i] = nxt[j]; shifts[i] = p["relative_distance"]
        for i in range(len(branches)):
            branches[i].append(complex(reordered[i]))
        if np.any(~np.isfinite(shifts)):
            complete = False
        step_records.append({
            "label": lev.get("label"),
            "relative_shifts": [float(x) for x in shifts],
            "max_relative_shift": float(np.max(shifts)) if shifts.size else math.inf,
            "median_relative_shift": float(np.median(shifts)) if shifts.size else math.inf,
        })
        current = reordered
    branch_records = []
    persistent = 0
    for i, vals in enumerate(branches):
        diffs = []
        valid = all(np.isfinite(v.real) and np.isfinite(v.imag) for v in vals)
        if valid:
            diffs = [normalized_distance(vals[k], vals[k+1]) for k in range(len(vals)-1)]
            is_persistent = all(d <= rel_tol for d in diffs)
        else:
            is_persistent = False
        persistent += int(is_persistent)
        branch_records.append({
            "branch": i,
            "values": complex_rows(vals),
            "step_relative_shifts": [float(d) for d in diffs],
            "max_relative_shift": float(max(diffs)) if diffs else 0.0,
            "persistent": bool(is_persistent),
        })
    all_shifts = [d for b in branch_records for d in b["step_relative_shifts"]]
    return {
        "ok": bool(complete and persistent == len(branches)),
        "relative_tolerance": float(rel_tol),
        "branch_count": len(branches),
        "persistent_count": int(persistent),
        "persistent_fraction": float(persistent / max(len(branches), 1)),
        "median_relative_shift": float(np.median(all_shifts)) if all_shifts else 0.0,
        "max_relative_shift": float(max(all_shifts)) if all_shifts else 0.0,
        "steps": step_records,
        "branches": branch_records,
    }


def overdamped_census(eigenvalues: Sequence[complex], *, oscillation_fraction_max: float = 0.05,
                       magnitude_floor: float = 1.0e-8) -> dict:
    """Census non-oscillatory temporal-generator modes.

    For lambda=sigma+i*omega, a QNM-like purely imaginary omega maps to a nearly
    real temporal-generator eigenvalue.  We therefore call a mode *overdamped-like*
    only descriptively when |Im lambda|/|lambda| is small.  This is not viscous
    damping and is not promoted to a physical SST claim.
    """
    vals = _as_complex(eigenvalues)
    rows = []
    for i, z in enumerate(vals):
        mag = abs(z)
        frac = abs(z.imag) / max(mag, magnitude_floor)
        flag = bool(mag >= magnitude_floor and frac <= oscillation_fraction_max)
        rows.append({"index": i, "re": float(z.real), "im": float(z.imag),
                     "abs": float(mag), "oscillation_fraction": float(frac),
                     "overdamped_like": flag})
    return {"oscillation_fraction_max": float(oscillation_fraction_max),
            "count": int(sum(r["overdamped_like"] for r in rows)), "modes": rows}


def symmetry_defect(eigenvalues: Sequence[complex]) -> dict:
    """Conjugate and Hamiltonian-quartet closure diagnostics.

    Exact quartet symmetry is *not* assumed for the projected C006 generator.
    This function only quantifies how nearly the finite spectrum contains the
    partners z*, -z, and -z*.
    """
    vals = _as_complex(eigenvalues)
    if vals.size == 0:
        return {"conjugate_max": math.inf, "quartet_max": math.inf, "rows": []}
    rows = []
    conj_ds = []; quartet_ds = []
    for i, z in enumerate(vals):
        def nearest(target: complex) -> float:
            return min(normalized_distance(target, w) for w in vals)
        dc = nearest(np.conjugate(z))
        dm = nearest(-z)
        dmc = nearest(-np.conjugate(z))
        conj_ds.append(dc); quartet_ds.extend([dm, dmc])
        rows.append({"index": i, "re": float(z.real), "im": float(z.imag),
                     "conjugate_partner_defect": float(dc),
                     "minus_partner_defect": float(dm),
                     "minus_conjugate_partner_defect": float(dmc)})
    return {
        "conjugate_max": float(max(conj_ds)),
        "conjugate_rms": float(np.sqrt(np.mean(np.square(conj_ds)))),
        "quartet_max": float(max(quartet_ds)),
        "quartet_rms": float(np.sqrt(np.mean(np.square(quartet_ds)))),
        "rows": rows,
    }



def solve_quadratic_eigenproblem(M0: np.ndarray, M1: np.ndarray, M2: np.ndarray) -> dict:
    """Solve ``(M0 + lambda M1 + lambda^2 M2) x = 0`` by linearization.

    This is a generic numerical utility.  C006 v0.3.0 does not claim that its
    frozen Kelvin generator is itself a quadratic eigenvalue problem; the
    utility is included so that a future SST-derived second-order spectral
    operator can use the same certification layer without changing semantics.
    """
    M0 = np.asarray(M0, dtype=complex)
    M1 = np.asarray(M1, dtype=complex)
    M2 = np.asarray(M2, dtype=complex)
    if M0.ndim != 2 or M0.shape[0] != M0.shape[1] or M1.shape != M0.shape or M2.shape != M0.shape:
        raise ValueError("M0, M1 and M2 must be equal-size square matrices")
    n = M0.shape[0]
    Z = np.zeros((n, n), dtype=complex)
    I = np.eye(n, dtype=complex)
    A = np.block([[Z, I], [-M0, -M1]])
    B = np.block([[I, Z], [Z, M2]])
    vals, vecs = generalized_eig(A, B)
    finite = np.isfinite(vals.real) & np.isfinite(vals.imag)
    vals = vals[finite]
    vecs = vecs[:, finite]
    residuals = []
    for k, lam in enumerate(vals):
        x = vecs[:n, k]
        qx = (M0 + lam*M1 + (lam*lam)*M2) @ x
        scale = (np.linalg.norm(M0) + abs(lam)*np.linalg.norm(M1) + abs(lam)**2*np.linalg.norm(M2)) * max(np.linalg.norm(x), 1e-30)
        residuals.append(float(np.linalg.norm(qx) / max(scale, 1e-30)))
    return {"eigenvalues": vals, "relative_residuals": residuals,
            "max_relative_residual": float(max(residuals)) if residuals else math.inf}


def quadratic_eigenproblem_selftest() -> dict:
    """Implementation self-test with roots -1 and -2 of lambda^2+3lambda+2."""
    r = solve_quadratic_eigenproblem(np.array([[2.0]]), np.array([[3.0]]), np.array([[1.0]]))
    vals = np.sort_complex(r["eigenvalues"])
    target = np.array([-2.0+0j, -1.0+0j])
    mt = match_spectra(target, vals)
    max_root = max((p["relative_distance"] for p in mt["matched"]), default=math.inf)
    ok = bool(len(mt["matched"]) == 2 and max_root < 1e-12 and r["max_relative_residual"] < 1e-12)
    return {"classification": "QUADRATIC_EIGENVALUE_LINEARIZATION_SELFTEST",
            "roots": complex_rows(vals), "max_root_relative_error": float(max_root),
            "max_relative_residual": r["max_relative_residual"], "pass": ok}


def branch_nonmonotonicity(scan_values: Sequence[float], spectra: Sequence[Sequence[complex]]) -> dict:
    """Track branches and flag non-monotonic Re/Im evolution across a parameter scan."""
    if len(scan_values) != len(spectra) or not spectra:
        return {"ok": False, "reason": "INVALID_SCAN"}
    levels = [{"label": float(x), "eigenvalues": s} for x, s in zip(scan_values, spectra)]
    tracked = track_spectrum(levels, rel_tol=math.inf)
    rows = []
    for b in tracked["branches"]:
        vals = np.array([complex(v["re"], v["im"]) for v in b["values"]], dtype=complex)
        def nonmono(x: np.ndarray) -> bool:
            if len(x) < 3: return False
            d = np.diff(x)
            d = d[np.abs(d) > 1e-12]
            return bool(len(d) >= 2 and np.any(d[:-1] * d[1:] < 0))
        rows.append({"branch": b["branch"],
                     "real_nonmonotonic": nonmono(vals.real),
                     "imag_nonmonotonic": nonmono(vals.imag),
                     "values": b["values"]})
    return {"ok": True, "scan_values": [float(x) for x in scan_values],
            "nonmonotonic_real_count": int(sum(r["real_nonmonotonic"] for r in rows)),
            "nonmonotonic_imag_count": int(sum(r["imag_nonmonotonic"] for r in rows)),
            "branches": rows}
