from __future__ import annotations

"""Self-contained canonical curve and finite-core dynamics operators for A059 v0.2.0.

The generated curves are canonical mathematical probes, not replacements for upstream
E011 source geometries. Every promoted result states this evidence boundary.

Braid data are fixed presentations for the selected low-crossing knots/links. All
single-knot probes, including the torus ladder, use the same closed-braid geometry
constructor so that the family test is not simply 'analytic torus formula vs braid'.
"""

import itertools, math
from typing import Iterable
import numpy as np

# Canonical braid presentations. Positive/negative integers denote sigma_i^{+/-1}.
# Torus ladder T(2,q) uses the standard 2-braid sigma_1^q.
KNOT_BRAIDS: dict[str, tuple[int, list[int]]] = {
    "3_1": (2, [1, 1, 1]),
    "5_1": (2, [1, 1, 1, 1, 1]),
    "7_1": (2, [1, 1, 1, 1, 1, 1, 1]),
    "5_2": (3, [-1, -1, -1, -2, 1, -2]),
    "6_1": (4, [-1, -1, -2, 1, 3, -2, 3]),
    "7_2": (4, [-1, -1, -1, -2, 1, -2, -3, 2, -3]),
    "8_1": (5, [-1, -1, -2, 1, -2, -3, 2, 4, -3, 4]),
    # symmetry controls
    "4_1": (3, [1, -2, 1, -2]),
    "8_17": (3, [-1, -1, 2, -1, 2, -1, 2, 2]),
}

BORROMEAN_BRAID = (3, [-1, 2, -1, 2, -1, 2])
UNLINK_CONTROL_BRAID = (3, [1, -1, 2, -2, 1, -1])  # braid-reduces to identity

FAMILY_A = ["3_1", "5_1", "7_1"]
FAMILY_B = ["5_2", "6_1", "7_2", "8_1"]
SYMMETRY_CONTROLS = ["4_1", "8_17"]


def _unit(x: np.ndarray, eps: float = 1e-15) -> np.ndarray:
    n = float(np.linalg.norm(x))
    return x / max(n, eps)


def closed_braid(
    n_strands: int,
    word: Iterable[int],
    samples_per_generator: int = 20,
    x_spacing: float = 1.0,
    crossing_amplitude: float = 0.34,
    closure_y: float = 3.6,
    closure_margin: float = 1.0,
    closure_samples: int = 20,
) -> list[np.ndarray]:
    """Construct the standard closure of a braid as closed polygonal components."""
    word = list(word)
    m = len(word)
    xs = (np.arange(n_strands, dtype=float) - (n_strands - 1) / 2.0) * x_spacing
    paths: list[list[np.ndarray]] = [[] for _ in range(n_strands)]
    pos_of_label = list(range(n_strands))
    label_at_pos = list(range(n_strands))
    for lab in range(n_strands):
        paths[lab].append(np.array([xs[lab], 0.0, 0.0], float))

    for k, g in enumerate(word):
        i = abs(int(g)) - 1
        if i < 0 or i >= n_strands - 1:
            raise ValueError(f"invalid braid generator {g} for {n_strands} strands")
        sign = 1.0 if g > 0 else -1.0
        left_lab = label_at_pos[i]
        right_lab = label_at_pos[i + 1]
        for q in range(1, samples_per_generator + 1):
            u = q / samples_per_generator
            z = k + u
            for lab in range(n_strands):
                p = pos_of_label[lab]
                x = xs[p]
                y = 0.0
                if lab == left_lab:
                    x = (1 - u) * xs[i] + u * xs[i + 1]
                    y = sign * crossing_amplitude * math.sin(math.pi * u)
                elif lab == right_lab:
                    x = (1 - u) * xs[i + 1] + u * xs[i]
                    y = -sign * crossing_amplitude * math.sin(math.pi * u)
                paths[lab].append(np.array([x, y, z], float))
        label_at_pos[i], label_at_pos[i + 1] = label_at_pos[i + 1], label_at_pos[i]
        pos_of_label[left_lab], pos_of_label[right_lab] = i + 1, i

    perm = pos_of_label[:]  # initial strand label -> top position
    closures: list[np.ndarray] = []
    for p in range(n_strands):
        x = xs[p]
        y_far = closure_y + 0.33 * p
        pts: list[np.ndarray] = []
        # top-outward bend
        for u in np.linspace(0, 1, closure_samples, endpoint=False)[1:]:
            s = math.sin(math.pi * u / 2)
            pts.append(np.array([x, y_far * s, m + closure_margin * s]))
        pts.append(np.array([x, y_far, m + closure_margin]))
        # external return leg
        for u in np.linspace(0, 1, closure_samples, endpoint=False)[1:]:
            pts.append(np.array([x, y_far, m + closure_margin - (m + 2 * closure_margin) * u]))
        pts.append(np.array([x, y_far, -closure_margin]))
        # bottom inward bend
        for u in np.linspace(0, 1, closure_samples + 1)[1:]:
            pts.append(np.array([x, y_far * math.cos(math.pi * u / 2), -closure_margin + closure_margin * u]))
        closures.append(np.asarray(pts, float))

    seen: set[int] = set()
    components: list[np.ndarray] = []
    for start in range(n_strands):
        if start in seen:
            continue
        cycle: list[int] = []
        lab = start
        while lab not in seen:
            seen.add(lab)
            cycle.append(lab)
            lab = perm[lab]
        points: list[list[float]] = []
        for j, lab in enumerate(cycle):
            strand = np.asarray(paths[lab])
            points.extend((strand if j == 0 else strand[1:]).tolist())
            points.extend(closures[perm[lab]].tolist())
        components.append(np.asarray(points, float))
    return components


def chaikin_closed(P: np.ndarray, iterations: int = 2) -> np.ndarray:
    P = np.asarray(P, float)
    for _ in range(iterations):
        Q = np.roll(P, -1, axis=0)
        A = 0.75 * P + 0.25 * Q
        B = 0.25 * P + 0.75 * Q
        out = np.empty((2 * len(P), 3), float)
        out[0::2] = A
        out[1::2] = B
        P = out
    return P


def resample_closed(P: np.ndarray, n: int) -> np.ndarray:
    P = np.asarray(P, float)
    if len(P) < 3:
        raise ValueError("closed curve needs >=3 points")
    if np.linalg.norm(P[-1] - P[0]) < 1e-12:
        P = P[:-1]
    Q = np.roll(P, -1, axis=0)
    ds = np.linalg.norm(Q - P, axis=1)
    L = float(ds.sum())
    if not math.isfinite(L) or L <= 0:
        raise ValueError("degenerate curve")
    cum = np.r_[0.0, np.cumsum(ds)]
    targets = np.linspace(0.0, L, n, endpoint=False)
    out = np.empty((n, 3), float)
    for j, s in enumerate(targets):
        i = int(np.searchsorted(cum, s, side="right") - 1)
        i = min(max(i, 0), len(P) - 1)
        u = (s - cum[i]) / max(ds[i], 1e-15)
        out[j] = (1 - u) * P[i] + u * P[(i + 1) % len(P)]
    return out


def normalize_curve(P: np.ndarray, n: int = 192) -> np.ndarray:
    P = chaikin_closed(P, 2)
    P = resample_closed(P, n)
    P = P - P.mean(axis=0)
    L = float(np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1).sum())
    return P * (2 * math.pi / max(L, 1e-15))


def canonical_knot(topology_id: str, n: int = 192) -> np.ndarray:
    strands, word = KNOT_BRAIDS[topology_id]
    comps = closed_braid(strands, word)
    if len(comps) != 1:
        raise RuntimeError(f"{topology_id}: expected one closed component, got {len(comps)}")
    return normalize_curve(comps[0], n)


def normalize_components(comps: list[np.ndarray], n_each: int = 96) -> list[np.ndarray]:
    arr = [resample_closed(chaikin_closed(c, 2), n_each) for c in comps]
    allp = np.vstack(arr)
    center = allp.mean(axis=0)
    arr = [p - center for p in arr]
    lens = [float(np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1).sum()) for p in arr]
    scale = 2 * math.pi / max(float(np.mean(lens)), 1e-15)
    return [p * scale for p in arr]


def tangents(P: np.ndarray) -> np.ndarray:
    D = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    N = np.linalg.norm(D, axis=1)
    return D / np.maximum(N[:, None], 1e-15)


def principal_axis(P: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = P - P.mean(axis=0)
    C = X.T @ X / len(X)
    vals, vecs = np.linalg.eigh(C)
    n = vecs[:, 0]
    j = int(np.argmax(np.abs(n)))
    if n[j] < 0:
        n = -n
    e1 = vecs[:, 2] - n * np.dot(vecs[:, 2], n)
    e1 = _unit(e1)
    e2 = _unit(np.cross(n, e1))
    return _unit(n), e1, e2


def _rodrigues(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    axis = _unit(axis)
    c, s = math.cos(angle), math.sin(angle)
    return v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)


def bishop_frame(P: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    T = tangents(P)
    n_axis, _, _ = principal_axis(P)
    n0 = n_axis - T[0] * np.dot(n_axis, T[0])
    if np.linalg.norm(n0) < 1e-7:
        ref = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(ref, T[0])) > 0.9:
            ref = np.array([0.0, 1.0, 0.0])
        n0 = ref - T[0] * np.dot(ref, T[0])
    n0 = _unit(n0)
    normals = [n0]
    for i in range(len(P) - 1):
        a, b = T[i], T[i + 1]
        cross = np.cross(a, b)
        nc = float(np.linalg.norm(cross))
        dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
        nn = normals[-1]
        if nc > 1e-12:
            nn = _rodrigues(nn, cross / nc, math.atan2(nc, dot))
        nn = _unit(nn - b * np.dot(nn, b))
        normals.append(nn)
    normals = np.asarray(normals)
    # close the transport once to measure holonomy
    a, b = T[-1], T[0]
    cross = np.cross(a, b)
    nc = float(np.linalg.norm(cross))
    dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
    n_end = normals[-1]
    if nc > 1e-12:
        n_end = _rodrigues(n_end, cross / nc, math.atan2(nc, dot))
    n_end = _unit(n_end - b * np.dot(n_end, b))
    delta = math.atan2(float(np.dot(T[0], np.cross(n0, n_end))), float(np.dot(n0, n_end)))
    # distribute the closure defect to obtain a periodic projection frame
    corrected = []
    for i, nn in enumerate(normals):
        nn = _rodrigues(nn, T[i], -delta * i / len(P))
        corrected.append(_unit(nn - T[i] * np.dot(nn, T[i])))
    N = np.asarray(corrected)
    B = np.cross(T, N)
    return T, N, B, delta / (2 * math.pi)


def velocity_field_from_curve(P: np.ndarray, X: np.ndarray, gamma: float = 1.0, core: float = 0.08) -> np.ndarray:
    P = np.asarray(P, float)
    X = np.asarray(X, float)
    Q = np.roll(P, -1, axis=0)
    dl = Q - P
    mid = 0.5 * (Q + P)
    out = np.zeros_like(X, float)
    for a in range(0, len(X), 128):
        xx = X[a:a + 128, None, :]
        r = xx - mid[None, :, :]
        den = (np.sum(r * r, axis=2) + core * core) ** 1.5
        out[a:a + 128] = gamma / (4 * math.pi) * np.sum(np.cross(dl[None, :, :], r) / den[:, :, None], axis=1)
    return out


def velocity_on_curve(P: np.ndarray, gamma: float = 1.0, core: float = 0.08) -> np.ndarray:
    P = np.asarray(P, float)
    Q = np.roll(P, -1, axis=0)
    dl = Q - P
    mid = 0.5 * (Q + P)
    out = np.zeros_like(P)
    M = len(P)
    for i in range(M):
        r = P[i] - mid
        den = (np.sum(r * r, axis=1) + core * core) ** 1.5
        mask = np.ones(M, dtype=bool)
        mask[i] = False
        mask[(i - 1) % M] = False
        out[i] = gamma / (4 * math.pi) * np.sum(np.cross(dl[mask], r[mask]) / den[mask, None], axis=0)
    return out


def reduced_dynamic_operator(
    P: np.ndarray,
    n: int = 72,
    core: float = 0.08,
    epsilon: float = 0.003,
    harmonics: tuple[int, ...] = (2, 3),
    gamma: float = 1.0,
) -> tuple[np.ndarray, dict[str, float], np.ndarray]:
    P = resample_closed(P, n)
    P = P - P.mean(axis=0)
    L = float(np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1).sum())
    P = P * (2 * math.pi / max(L, 1e-15))
    T, N, B, frame_h = bishop_frame(P)
    theta = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
    basis: list[np.ndarray] = []
    for k in harmonics:
        for vec in (N, B):
            for trig in (np.cos, np.sin):
                F = vec * trig(k * theta)[:, None]
                F = F / max(float(np.sqrt(np.mean(np.sum(F * F, axis=1)))), 1e-15)
                basis.append(F)
    basis = np.asarray(basis)
    v0 = velocity_on_curve(P, gamma=gamma, core=core)
    u0 = v0 - T * np.sum(v0 * T, axis=1)[:, None]
    d = len(basis)
    J = np.zeros((d, d), float)
    for j, F in enumerate(basis):
        vp = velocity_on_curve(P + epsilon * F, gamma=gamma, core=core)
        vm = velocity_on_curve(P - epsilon * F, gamma=gamma, core=core)
        du = (vp - vm) / (2 * epsilon)
        du = du - T * np.sum(du * T, axis=1)[:, None]
        for i, G in enumerate(basis):
            J[i, j] = float(np.mean(np.sum(G * du, axis=1)))
    eig = np.linalg.eigvals(J)
    jf = float(np.linalg.norm(J, ord="fro"))
    en = eig / max(jf, 1e-30)
    features = {
        "base_normal_rms": float(np.sqrt(np.mean(np.sum(u0 * u0, axis=1)))),
        "frame_holonomy_turns": float(frame_h),
        "J_fro": jf,
        "eig_max_real_norm": float(np.max(en.real)),
        "eig_min_real_norm": float(np.min(en.real)),
        "eig_imag_rms_norm": float(np.sqrt(np.mean(en.imag ** 2))),
        "eig_abs_max_norm": float(np.max(np.abs(en))),
        "eig_osc_fraction": float(np.mean(np.abs(en.imag) > 1e-7)),
    }
    return J, features, eig


def geometric_axis_winding(P: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    c = P.mean(axis=0)
    n, e1, e2 = principal_axis(P)
    X = P - c
    ang = np.arctan2(X @ e2, X @ e1)
    diffs = np.angle(np.exp(1j * (np.roll(ang, -1) - ang)))
    w = float(diffs.sum() / (2 * math.pi))
    if w < 0:
        n = -n
        e2 = -e2
        ang = np.arctan2(X @ e2, X @ e1)
        diffs = np.angle(np.exp(1j * (np.roll(ang, -1) - ang)))
        w = float(diffs.sum() / (2 * math.pi))
    return w, n, e1, e2


def straight_core_field(X: np.ndarray, center: np.ndarray, axis: np.ndarray, gamma: float = 1.0, core: float = 0.06) -> np.ndarray:
    axis = _unit(axis)
    R = X - center
    perp = R - np.outer(R @ axis, axis)
    r2 = np.sum(perp * perp, axis=1)
    return gamma / (2 * math.pi) * np.cross(np.broadcast_to(axis, perp.shape), perp) / (r2[:, None] + core * core)


def period_and_charge_coupling(P: np.ndarray, n: int = 96, self_core: float = 0.08, probe_core: float = 0.06) -> dict[str, float]:
    P = resample_closed(P, n)
    P = P - P.mean(axis=0)
    L = float(np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1).sum())
    P = P * (2 * math.pi / max(L, 1e-15))
    winding, axis, _, _ = geometric_axis_winding(P)
    center = P.mean(axis=0)
    mids = 0.5 * (P + np.roll(P, -1, axis=0))
    dl = np.roll(P, -1, axis=0) - P
    v_probe_mid = straight_core_field(mids, center, axis, +1.0, probe_core)
    period = float(np.sum(np.sum(v_probe_mid * dl, axis=1)))
    v_self = velocity_on_curve(P, +1.0, self_core)
    v_probe = straight_core_field(P, center, axis, +1.0, probe_core)
    ds = np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1)
    numerator = float(np.sum(np.sum(v_self * v_probe, axis=1) * ds))
    den = math.sqrt(max(float(np.sum(np.sum(v_self * v_self, axis=1) * ds)), 0.0) * max(float(np.sum(np.sum(v_probe * v_probe, axis=1) * ds)), 0.0))
    q_dyn = numerator / max(den, 1e-30)
    return {
        "axis_winding": winding,
        "period_integral": period,
        "period_error_to_winding": abs(period - winding),
        "dynamic_cross_response": q_dyn,
    }


def gauss_linking(P: np.ndarray, Q: np.ndarray) -> float:
    P = np.asarray(P, float); Q = np.asarray(Q, float)
    p1 = np.roll(P, -1, axis=0); q1 = np.roll(Q, -1, axis=0)
    dp = p1 - P; dq = q1 - Q
    mp = 0.5 * (P + p1); mq = 0.5 * (Q + q1)
    total = 0.0
    for i in range(len(dp)):
        r = mp[i] - mq
        num = np.einsum("ij,ij->i", np.cross(dp[i], dq), r)
        den = np.linalg.norm(r, axis=1) ** 3 + 1e-30
        total += float(np.sum(num / den))
    return total / (4 * math.pi)


def rotation_from_to(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = _unit(np.asarray(a, float)); b = _unit(np.asarray(b, float))
    v = np.cross(a, b); c = float(np.clip(np.dot(a, b), -1.0, 1.0)); s = float(np.linalg.norm(v))
    if s < 1e-12:
        if c > 0:
            return np.eye(3)
        ref = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(ref, a)) > 0.9:
            ref = np.array([0.0, 1.0, 0.0])
        k = _unit(np.cross(a, ref))
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        return np.eye(3) + 2 * K @ K
    k = v / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + K * s + K @ K * (1 - c)


def three_core_container(kind: str, n_each: int = 84) -> list[np.ndarray]:
    if kind == "CANDIDATE":
        strands, word = BORROMEAN_BRAID
    elif kind == "UNLINK_CONTROL":
        strands, word = UNLINK_CONTROL_BRAID
    else:
        raise ValueError(kind)
    comps = normalize_components(closed_braid(strands, word, samples_per_generator=22, closure_y=4.0), n_each)
    normals = []
    for p in comps:
        w, n, _, _ = geometric_axis_winding(p)
        if w < 0:
            n = -n
        normals.append(n)
    mean_n = _unit(np.sum(normals, axis=0))
    R = rotation_from_to(mean_n, np.array([0.0, 0.0, 1.0]))
    return [p @ R.T for p in comps]


def winding_about_z(P: np.ndarray) -> float:
    c = P.mean(axis=0)
    a = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])
    return float(np.angle(np.exp(1j * (np.roll(a, -1) - a))).sum() / (2 * math.pi))


def fibonacci_sphere(n: int, radius: float) -> np.ndarray:
    i = np.arange(n, dtype=float)
    phi = (1 + math.sqrt(5.0)) / 2.0
    z = 1.0 - 2.0 * (i + 0.5) / n
    theta = 2 * math.pi * i / phi
    rr = np.sqrt(np.maximum(0.0, 1 - z * z))
    return radius * np.c_[rr * np.cos(theta), rr * np.sin(theta), z]


def container_field_metrics(comps: list[np.ndarray], probe_scale: float = 2.0, n_probe: int = 480, filament_core: float = 0.06, axis_core: float = 0.08) -> dict[str, object]:
    allp = np.vstack(comps)
    center = allp.mean(axis=0)
    radius = float(np.max(np.linalg.norm(allp - center, axis=1))) * probe_scale
    X = center + fibonacci_sphere(n_probe, radius)
    zaxis = np.array([0.0, 0.0, 1.0])
    fields = []
    periods = []
    windings = []
    for p in comps:
        c = p.mean(axis=0)
        vf = velocity_field_from_curve(p, X, gamma=+1.0, core=filament_core)
        vc = straight_core_field(X, c, zaxis, gamma=+1.0, core=axis_core)
        fields.append(vf + vc)
        windings.append(winding_about_z(p))
        mids = 0.5 * (p + np.roll(p, -1, axis=0))
        dl = np.roll(p, -1, axis=0) - p
        vm = straight_core_field(mids, c, zaxis, gamma=+1.0, core=axis_core)
        periods.append(float(np.sum(np.sum(vm * dl, axis=1))))
    Eself = [float(np.mean(np.sum(v * v, axis=1))) for v in fields]
    total = np.sum(np.asarray(fields), axis=0)
    Etotal = float(np.mean(np.sum(total * total, axis=1)))
    Ecross = Etotal - float(sum(Eself))
    links = [gauss_linking(comps[i], comps[j]) for i, j in itertools.combinations(range(3), 2)]
    pair_corr = []
    for i, j in itertools.combinations(range(3), 2):
        pair_corr.append(float(np.mean(np.sum(fields[i] * fields[j], axis=1)) / max(math.sqrt(Eself[i] * Eself[j]), 1e-30)))
    return {
        "pairwise_gauss_linking": links,
        "own_core_windings": windings,
        "own_core_periods": periods,
        "self_field_energies": Eself,
        "total_field_energy": Etotal,
        "cross_field_energy": Ecross,
        "pair_field_correlations": pair_corr,
    }
