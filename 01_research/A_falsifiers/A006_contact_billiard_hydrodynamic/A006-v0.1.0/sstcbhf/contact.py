from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal import find_peaks
from scipy.interpolate import CubicSpline

from .geometry import CurveGeometry, PeriodicCurve
from .util import signed_circular_delta, circular_distance


@dataclass
class ContactMapResult:
    s: np.ndarray
    branch_a: np.ndarray
    branch_b: np.ndarray
    branch_a_lift: np.ndarray
    branch_b_lift: np.ndarray
    pt_a: np.ndarray
    pt_b: np.ndarray
    orth_a: np.ndarray
    orth_b: np.ndarray
    completeness_fraction: float
    thickness_contact_median: float
    thickness_contact_min: float
    branch_winding_a: int
    branch_winding_b: int
    inverse_residual_rms: float


class PeriodicLiftMap:
    """Degree-one periodic lift f(s+1)=f(s)+w with cubic interpolation."""

    def __init__(self, s: np.ndarray, values_lift: np.ndarray, winding: int | None = None):
        s = np.asarray(s, dtype=float)
        y = np.asarray(values_lift, dtype=float)
        if len(s) != len(y):
            raise ValueError("s and values lengths differ")
        if winding is None:
            winding = int(round((y[-1] - y[0]) + (y[1] - y[0])))
            if winding == 0:
                winding = 1
        self.winding = int(winding)
        self.s0 = float(s[0])
        # Interpolate the periodic part g(s)=f(s)-w s.  This enforces both
        # value and derivative continuity at the branch cut.
        g = y - self.winding * s
        self._spline = CubicSpline(
            np.r_[s, 1.0],
            np.r_[g, g[0]],
            bc_type="periodic",
        )

    def __call__(self, x: np.ndarray | float) -> np.ndarray:
        x_arr = np.asarray(x, dtype=float)
        q = x_arr - np.floor(x_arr)
        return self._spline(q) + self.winding * x_arr

    def derivative(self, x: np.ndarray | float) -> np.ndarray:
        x_arr = np.asarray(x, dtype=float)
        q = x_arr - np.floor(x_arr)
        return self._spline(q, 1) + self.winding

    def mod(self, x: np.ndarray | float) -> np.ndarray:
        return np.mod(self(x), 1.0)


def _pt_objective(curve: PeriodicCurve, p: np.ndarray, t: float) -> float:
    q = curve.eval(t)
    tangent, *_ = curve.frame(t)
    chord = p - q
    norm = float(np.linalg.norm(chord))
    if norm <= 1e-14:
        return 1e12
    sin_theta = float(np.linalg.norm(np.cross(tangent, chord / norm)))
    return 0.5 * norm / max(sin_theta, 1e-10)


def _candidate_minima(geom: CurveGeometry, i: int, exclusion: int, max_candidates: int = 8):
    n = len(geom.points)
    p = geom.points[i]
    d = p - geom.points
    dist = np.linalg.norm(d, axis=1)
    idx = np.arange(n)
    cyc = np.minimum((idx - i) % n, (i - idx) % n)
    mask = cyc > exclusion
    pt = np.full(n, np.inf)
    valid = np.where(mask)[0]
    chords = d[valid]
    norms = np.maximum(dist[valid], 1e-15)
    e = chords / norms[:, None]
    sin_theta = np.linalg.norm(np.cross(geom.tangents[valid], e), axis=1)
    pt[valid] = 0.5 * norms / np.maximum(sin_theta, 1e-10)
    local, _ = find_peaks(-np.where(np.isfinite(pt), pt, np.nanmax(pt[np.isfinite(pt)]) * 10.0), distance=max(2, exclusion // 2))
    local = local[np.isfinite(pt[local])]
    if len(local) < 2:
        local = valid[np.argsort(pt[valid])[:max_candidates]]
    else:
        local = local[np.argsort(pt[local])[:max_candidates]]
    return local, pt


def _refine_candidate(curve: PeriodicCurve, geom: CurveGeometry, i: int, j: int):
    n = len(geom.points)
    p = geom.points[i]
    center = j / n
    half = 1.5 / n
    result = minimize_scalar(lambda x: _pt_objective(curve, p, x % 1.0), bounds=(center - half, center + half), method="bounded", options={"xatol": 1e-12})
    t = float(result.x % 1.0)
    q = curve.eval(t)
    tangent_t, *_ = curve.frame(t)
    chord = p - q
    dist = float(np.linalg.norm(chord))
    e = chord / max(dist, 1e-15)
    orth = float(np.sqrt((e @ geom.tangents[i]) ** 2 + (e @ tangent_t) ** 2))
    pt = _pt_objective(curve, p, t)
    return t, pt, orth


def _unwrap_near(value: float, reference: float) -> float:
    return value + round(reference - value)


def _track_two_branches(candidates: list[list[tuple[float, float, float]]]):
    n = len(candidates)
    out1 = np.empty(n)
    out2 = np.empty(n)
    pt1 = np.empty(n)
    pt2 = np.empty(n)
    or1 = np.empty(n)
    or2 = np.empty(n)
    first = sorted(candidates[0], key=lambda x: x[0])[:2]
    (out1[0], pt1[0], or1[0]), (out2[0], pt2[0], or2[0]) = first
    for i in range(1, n):
        cands = candidates[i]
        if len(cands) < 2:
            out1[i] = out1[i - 1]
            out2[i] = out2[i - 1]
            pt1[i] = pt1[i - 1]
            pt2[i] = pt2[i - 1]
            or1[i] = or1[i - 1]
            or2[i] = or2[i - 1]
            continue
        best = None
        for a_idx in range(len(cands)):
            for b_idx in range(len(cands)):
                if a_idx == b_idx:
                    continue
                a = cands[a_idx]
                b = cands[b_idx]
                au = _unwrap_near(a[0], out1[i - 1])
                bu = _unwrap_near(b[0], out2[i - 1])
                cost = (au - out1[i - 1]) ** 2 + (bu - out2[i - 1]) ** 2
                if best is None or cost < best[0]:
                    best = (cost, au, bu, a, b)
        assert best is not None
        _, au, bu, a, b = best
        out1[i], out2[i] = au, bu
        pt1[i], or1[i] = a[1], a[2]
        pt2[i], or2[i] = b[1], b[2]
    return out1, out2, pt1, pt2, or1, or2


def extract_contact_map(
    geom: CurveGeometry,
    exclusion_fraction: float = 0.03,
    candidates_per_point: int = 6,
) -> ContactMapResult:
    n = len(geom.points)
    curve = PeriodicCurve(geom.points)
    exclusion = max(3, int(round(exclusion_fraction * n)))
    candidates: list[list[tuple[float, float, float]]] = []
    complete = 0
    for i in range(n):
        idxs, _ = _candidate_minima(geom, i, exclusion, candidates_per_point)
        refined = [_refine_candidate(curve, geom, i, int(j)) for j in idxs]
        refined.sort(key=lambda x: x[1] * (1.0 + 5.0 * x[2] * x[2]))
        selected: list[tuple[float, float, float]] = []
        for cand in refined:
            if all(circular_distance(cand[0], other[0]) > 2.0 / n for other in selected):
                selected.append(cand)
            if len(selected) == 2:
                break
        if len(selected) >= 2:
            complete += 1
        while len(selected) < 2:
            fallback = selected[0] if selected else (float((i + n // 3) % n) / n, np.nan, np.nan)
            selected.append(fallback)
        candidates.append(selected)
    a_lift, b_lift, pt_a, pt_b, orth_a, orth_b = _track_two_branches(candidates)
    winding_a = int(round((a_lift[-1] - a_lift[0]) + np.median(np.diff(a_lift))))
    winding_b = int(round((b_lift[-1] - b_lift[0]) + np.median(np.diff(b_lift))))
    if winding_a == 0:
        winding_a = 1
    if winding_b == 0:
        winding_b = 1
    s = geom.s
    map_a = PeriodicLiftMap(s, a_lift, winding_a)
    map_b = PeriodicLiftMap(s, b_lift, winding_b)
    # Choose the inverse pairing residual in both directions.
    inv1 = circular_distance(map_b.mod(map_a.mod(s)), s)
    inv2 = circular_distance(map_a.mod(map_b.mod(s)), s)
    inverse_rms = float(np.sqrt(np.mean(np.r_[inv1, inv2] ** 2)))
    pts = np.r_[pt_a[np.isfinite(pt_a)], pt_b[np.isfinite(pt_b)]]
    return ContactMapResult(
        s=s,
        branch_a=np.mod(a_lift, 1.0),
        branch_b=np.mod(b_lift, 1.0),
        branch_a_lift=a_lift,
        branch_b_lift=b_lift,
        pt_a=pt_a,
        pt_b=pt_b,
        orth_a=orth_a,
        orth_b=orth_b,
        completeness_fraction=complete / n,
        thickness_contact_median=float(np.nanmedian(pts)),
        thickness_contact_min=float(np.nanmin(pts)),
        branch_winding_a=winding_a,
        branch_winding_b=winding_b,
        inverse_residual_rms=inverse_rms,
    )
