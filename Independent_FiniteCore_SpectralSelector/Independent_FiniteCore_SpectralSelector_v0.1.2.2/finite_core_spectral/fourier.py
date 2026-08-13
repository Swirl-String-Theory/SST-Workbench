from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .core import _backend, validate_config


@dataclass(frozen=True)
class FourierSettings:
    max_m: int = 12
    symmetry_order: int = 4
    low_mode_leakage_max: float = 0.10
    sector_leakage_max: float = 1e-8
    dominant_mode_weight_min: float = 0.50
    branch_overlap_min: float = 0.80
    candidate_abs_m_min: int = 2


def validate_fourier_settings(settings: FourierSettings, n_nodes: int) -> FourierSettings:
    if settings.max_m < 2:
        raise ValueError("max_m must be >= 2")
    if n_nodes <= 2 * settings.max_m:
        raise ValueError("n_nodes must exceed 2*max_m so signed Fourier modes are unique")
    if settings.symmetry_order < 1:
        raise ValueError("symmetry_order must be >=1")
    for name, x in [
        ("low_mode_leakage_max", settings.low_mode_leakage_max),
        ("sector_leakage_max", settings.sector_leakage_max),
        ("dominant_mode_weight_min", settings.dominant_mode_weight_min),
        ("branch_overlap_min", settings.branch_overlap_min),
    ]:
        if not (0.0 <= x <= 1.0):
            raise ValueError(f"{name} must lie in [0,1]")
    return settings


def signed_modes(max_m: int) -> list[int]:
    return list(range(-int(max_m), int(max_m) + 1))


def _low_fourier_basis(n_nodes: int, modes: list[int]) -> np.ndarray:
    theta = 2.0 * np.pi * np.arange(n_nodes, dtype=float) / float(n_nodes)
    U = np.zeros((2 * n_nodes, 2 * len(modes)), dtype=complex)
    inv = 1.0 / math.sqrt(float(n_nodes))
    for k, m in enumerate(modes):
        phase = np.exp(1j * float(m) * theta) * inv
        U[0::2, 2 * k] = phase
        U[1::2, 2 * k + 1] = phase
    return U


def _normalize_columns(v: np.ndarray) -> np.ndarray:
    out = np.asarray(v, dtype=complex).copy()
    norms = np.linalg.norm(out, axis=0)
    norms = np.where(norms > 0, norms, 1.0)
    out /= norms
    return out


def _initial_sort(eig: np.ndarray, vec: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.lexsort((eig.imag, eig.real, np.abs(eig)))
    return eig[order], vec[:, order]


def _track(prev_vec: np.ndarray | None, eig: np.ndarray, vec: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[float]]:
    cur = _normalize_columns(vec)
    if prev_vec is None:
        e, v = _initial_sort(eig, cur)
        return e, v, [1.0] * len(e)
    prev = _normalize_columns(prev_vec)
    overlap = np.abs(prev.conj().T @ cur) ** 2
    unused = set(range(cur.shape[1]))
    chosen: list[int] = []
    scores: list[float] = []
    for i in range(prev.shape[1]):
        if not unused:
            break
        j = max(unused, key=lambda k: float(overlap[i, k]))
        unused.remove(j)
        chosen.append(j)
        scores.append(float(overlap[i, j]))
    chosen.extend(sorted(unused))
    if len(scores) < len(chosen):
        scores.extend([0.0] * (len(chosen) - len(scores)))
    return eig[chosen], cur[:, chosen], scores


def _mode_weights(vec: np.ndarray, sector_modes: list[int]) -> dict[int, float]:
    w: dict[int, float] = {}
    for k, m in enumerate(sector_modes):
        w[int(m)] = float(abs(vec[2 * k]) ** 2 + abs(vec[2 * k + 1]) ** 2)
    s = sum(w.values())
    if s > 0:
        w = {m: x / s for m, x in w.items()}
    return w


def _entropy(weights: dict[int, float]) -> float:
    vals = [x for x in weights.values() if x > 0]
    if len(vals) <= 1:
        return 0.0
    return float(-sum(x * math.log(x) for x in vals) / math.log(len(vals)))


def project_low_fourier(J: np.ndarray, n_nodes: int, settings: FourierSettings) -> dict[str, Any]:
    settings = validate_fourier_settings(settings, n_nodes)
    modes = signed_modes(settings.max_m)
    U = _low_fourier_basis(n_nodes, modes)
    A = U.conj().T @ J @ U
    JU = J @ U
    denom = max(float(np.linalg.norm(JU, ord="fro")), 1e-300)
    projection_residual = JU - U @ A
    low_mode_leakage = float(np.linalg.norm(projection_residual, ord="fro") / denom)

    # In a cubic periodic lattice the exact in-plane symmetry is C4, not SO(2).
    # Therefore modes may mix only inside m mod symmetry_order sectors when the
    # discretisation respects that symmetry. This metric tests that statement.
    totalA = max(float(np.linalg.norm(A, ord="fro")), 1e-300)
    c4_bad2 = 0.0
    for i, mi in enumerate(modes):
        ri = mi % settings.symmetry_order
        rows = slice(2 * i, 2 * i + 2)
        for j, mj in enumerate(modes):
            if (mj % settings.symmetry_order) != ri:
                cols = slice(2 * j, 2 * j + 2)
                c4_bad2 += float(np.linalg.norm(A[rows, cols], ord="fro") ** 2)
    c4_leakage = math.sqrt(c4_bad2) / totalA

    mode_blocks = []
    for i, m in enumerate(modes):
        sl = slice(2 * i, 2 * i + 2)
        block = A[sl, sl]
        colnorm = max(float(np.linalg.norm(A[:, sl], ord="fro")), 1e-300)
        diag_fraction = float(np.linalg.norm(block, ord="fro") / colnorm)
        ee = np.linalg.eigvals(block)
        mode_blocks.append({
            "m": int(m),
            "diagonal_fraction": diag_fraction,
            "block_eigenvalues": [[float(z.real), float(z.imag)] for z in ee],
        })

    sectors: dict[int, dict[str, Any]] = {}
    for r in range(settings.symmetry_order):
        sector_mode_indices = [i for i, m in enumerate(modes) if (m % settings.symmetry_order) == r]
        sector_modes = [modes[i] for i in sector_mode_indices]
        coord: list[int] = []
        for i in sector_mode_indices:
            coord.extend([2 * i, 2 * i + 1])
        coord_arr = np.asarray(coord, dtype=int)
        S = A[np.ix_(coord_arr, coord_arr)]
        allcols = A[:, coord_arr]
        other = np.ones(A.shape[0], dtype=bool)
        other[coord_arr] = False
        sector_denom = max(float(np.linalg.norm(allcols, ord="fro")), 1e-300)
        sector_leakage = float(np.linalg.norm(allcols[other, :], ord="fro") / sector_denom)
        sectors[r] = {
            "residue": int(r),
            "modes": [int(m) for m in sector_modes],
            "matrix": S,
            "sector_leakage_fraction": sector_leakage,
        }

    return {
        "modes": modes,
        "basis": U,
        "operator": A,
        "low_mode_projection_leakage": low_mode_leakage,
        "c4_symmetry_leakage": float(c4_leakage),
        "mode_blocks": mode_blocks,
        "sectors": sectors,
    }


def jacobians_at_q(
    cfg: dict[str, Any],
    q: float,
    *,
    force_python: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
    use_c4_accel: bool = False,
):
    """Compatibility helper for one q point.

    v0.1.2.2's campaign path avoids this helper so the q-independent self
    Jacobian can be cached once per scan.  The public helper remains available
    for diagnostics and older scripts.
    """
    c = validate_config(cfg)
    b, bname = _backend(force_python, force_build, build_verbose)
    cell = math.exp(float(q))
    c4_ok = bool(use_c4_accel and c["n_nodes"] % 4 == 0 and hasattr(b, "ring_normal_jacobian_c4"))
    jac = b.ring_normal_jacobian_c4 if c4_ok else b.ring_normal_jacobian
    Jself = np.asarray(
        jac(c["n_nodes"], c["ring_radius_over_core"], cell, 0, c["fd_eps_over_core"], c["core_model"], c["threads"], False),
        dtype=float,
    )
    if c["image_shell"] > 0:
        Jint = np.asarray(
            jac(c["n_nodes"], c["ring_radius_over_core"], cell, c["image_shell"], c["fd_eps_over_core"], c["core_model"], c["threads"], True),
            dtype=float,
        )
    else:
        Jint = np.zeros_like(Jself)
    metrics = dict(b.ring_base_metrics(c["n_nodes"], c["ring_radius_over_core"], cell, c["image_shell"], c["core_model"]))
    return c, bname, Jself, Jint, metrics


def fourier_scan(
    cfg: dict[str, Any],
    settings: FourierSettings = FourierSettings(),
    *,
    force_python: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
    progress: bool = True,
    use_c4_accel: bool = True,
    audit_c4_accel: bool = True,
) -> dict[str, Any]:
    c = validate_config(cfg)
    validate_fourier_settings(settings, c["n_nodes"])
    q = c["q_min"]
    qs: list[float] = []
    while q <= c["q_max"] + 0.5 * c["q_step"]:
        qs.append(round(q, 12))
        q += c["q_step"]

    # Load/build the backend once per scan rather than once per q point.
    b, bname = _backend(force_python, force_build, build_verbose)
    c4_accel_used = bool(
        use_c4_accel
        and settings.symmetry_order == 4
        and c["n_nodes"] % 4 == 0
        and hasattr(b, "ring_normal_jacobian_c4")
    )
    jac = b.ring_normal_jacobian_c4 if c4_accel_used else b.ring_normal_jacobian
    audit_fn = getattr(b, "ring_c4_symmetry_audit", None)

    # The shell=0 self operator is independent of periodic cell size.  v0.1.2.1
    # recomputed it at every q; cache it once without changing its definition.
    cell_ref = math.exp(float(qs[0]))
    Jself = np.asarray(
        jac(
            c["n_nodes"], c["ring_radius_over_core"], cell_ref, 0,
            c["fd_eps_over_core"], c["core_model"], c["threads"], False,
        ),
        dtype=float,
    )
    self_c4_audit = 0.0
    if c4_accel_used and audit_c4_accel and audit_fn is not None:
        self_c4_audit = float(dict(audit_fn(
            c["n_nodes"], c["ring_radius_over_core"], cell_ref, 0,
            c["fd_eps_over_core"], c["core_model"], False,
        )).get("relative_error", 0.0))

    rows: list[dict[str, Any]] = []
    sector_rows: list[dict[str, Any]] = []
    branch_history: list[dict[str, Any]] = []
    prev_sector_vecs: dict[int, np.ndarray | None] = {r: None for r in range(settings.symmetry_order)}

    for iq, q in enumerate(qs, 1):
        cell = math.exp(float(q))
        if c["image_shell"] > 0:
            Jint = np.asarray(
                jac(
                    c["n_nodes"], c["ring_radius_over_core"], cell, c["image_shell"],
                    c["fd_eps_over_core"], c["core_model"], c["threads"], True,
                ),
                dtype=float,
            )
        else:
            Jint = np.zeros_like(Jself)
        metrics = dict(b.ring_base_metrics(
            c["n_nodes"], c["ring_radius_over_core"], cell, c["image_shell"], c["core_model"]
        ))
        interaction_c4_audit = 0.0
        if c4_accel_used and audit_c4_accel and audit_fn is not None and c["image_shell"] > 0:
            interaction_c4_audit = float(dict(audit_fn(
                c["n_nodes"], c["ring_radius_over_core"], cell, c["image_shell"],
                c["fd_eps_over_core"], c["core_model"], True,
            )).get("relative_error", 0.0))

        J = Jself + Jint
        proj = project_low_fourier(J, c["n_nodes"], settings)
        projected_c4 = float(proj["c4_symmetry_leakage"])
        effective_c4 = max(projected_c4, self_c4_audit, interaction_c4_audit)
        global_eig = np.linalg.eigvals(J)
        global_order = np.argsort(np.abs(global_eig))
        k_neutral = min(max(c["neutral_modes"], 0), len(global_eig)-1)
        global_non = global_eig[global_order[k_neutral:]]
        global_gap = float(np.min(np.abs(global_non))) if len(global_non) else float("nan")
        global_sigma = float(np.max(global_eig.real))
        global_unstable = int(np.sum(global_eig.real > c["eig_zero_tol"]))
        equilibrium_ok = bool(float(metrics["relative_shape_residual"]) <= c["residual_max"])
        quality_ok = bool(
            proj["low_mode_projection_leakage"] <= settings.low_mode_leakage_max
            and effective_c4 <= settings.sector_leakage_max
            and equilibrium_ok
        )
        row = {
            "q": float(q),
            "cell_over_core": cell,
            "backend": bname,
            "n_nodes": c["n_nodes"],
            "image_shell": c["image_shell"],
            "fd_eps_over_core": c["fd_eps_over_core"],
            "max_m": settings.max_m,
            "symmetry_order": settings.symmetry_order,
            "c4_acceleration_used": c4_accel_used,
            "self_jacobian_cached": True,
            "global_spectral_abscissa_reference": global_sigma,
            "global_gap_after_neutral_reference": global_gap,
            "global_unstable_count_reference": global_unstable,
            "low_mode_projection_leakage": proj["low_mode_projection_leakage"],
            "c4_symmetry_leakage_projected": projected_c4,
            "c4_symmetry_audit_self": self_c4_audit,
            "c4_symmetry_audit_interaction": interaction_c4_audit,
            "c4_symmetry_leakage": effective_c4,
            "relative_shape_residual": float(metrics["relative_shape_residual"]),
            "equilibrium_gate_ok": equilibrium_ok,
            "fourier_quality_gate_ok": quality_ok,
        }
        rows.append(row)

        hist_q: dict[str, Any] = {"q": float(q), "sectors": {}}
        for r in range(settings.symmetry_order):
            sec = proj["sectors"][r]
            S = sec["matrix"]
            eig_raw, vec_raw = np.linalg.eig(S)
            eig, vec, overlaps = _track(prev_sector_vecs[r], eig_raw, vec_raw)
            prev_sector_vecs[r] = vec
            sec_hist = []
            sec_modes = list(sec["modes"])
            for branch, z in enumerate(eig):
                weights = _mode_weights(vec[:, branch], sec_modes)
                dom_m = max(weights, key=weights.get)
                dom_w = float(weights[dom_m])
                abs_weights: dict[int, float] = {}
                for m, w in weights.items():
                    abs_weights[abs(int(m))] = abs_weights.get(abs(int(m)), 0.0) + float(w)
                dom_abs_m = max(abs_weights, key=abs_weights.get)
                dom_abs_w = float(abs_weights[dom_abs_m])
                rec = {
                    "q": float(q),
                    "cell_over_core": cell,
                    "sector": int(r),
                    "branch": int(branch),
                    "eig_real": float(z.real),
                    "eig_imag": float(z.imag),
                    "eig_abs": float(abs(z)),
                    "overlap_prev": float(overlaps[branch]),
                    "dominant_m": int(dom_m),
                    "dominant_m_weight": dom_w,
                    "dominant_abs_m": int(dom_abs_m),
                    "dominant_abs_m_weight": dom_abs_w,
                    "mode_entropy": _entropy(weights),
                    "sector_leakage_fraction": float(sec["sector_leakage_fraction"]),
                    "low_mode_projection_leakage": float(proj["low_mode_projection_leakage"]),
                    "c4_symmetry_leakage": effective_c4,
                    "c4_acceleration_used": c4_accel_used,
                    "equilibrium_gate_ok": equilibrium_ok,
                    "fourier_quality_gate_ok": quality_ok,
                }
                sector_rows.append(rec)
                sec_hist.append({**rec, "mode_weights": {str(k): float(v) for k, v in weights.items()}})
            hist_q["sectors"][str(r)] = sec_hist
        branch_history.append(hist_q)
        if progress:
            print(
                f"[{iq:03d}/{len(qs):03d}] q={q:.5f} L/a={cell:.6g} "
                f"lowLeak={row['low_mode_projection_leakage']:.3e} C4leak={effective_c4:.3e} "
                f"residual={row['relative_shape_residual']:.3e} quality={int(quality_ok)} "
                f"accel={'C4' if c4_accel_used else 'full'}"
            )

    candidates = detect_fourier_candidates(sector_rows, rows, settings)
    return {
        "config": c,
        "dimensionless_only": True,
        "fourier_settings": settings.__dict__,
        "performance": {
            "c4_acceleration_used": c4_accel_used,
            "c4_audit_enabled": bool(c4_accel_used and audit_c4_accel),
            "self_jacobian_cached": True,
            "expected_native_jacobian_column_reduction": 4 if c4_accel_used else 1,
        },
        "rows": rows,
        "sector_rows": sector_rows,
        "branch_history": branch_history,
        "candidates": candidates,
    }


def detect_fourier_candidates(sector_rows: list[dict[str, Any]], rows: list[dict[str, Any]], settings: FourierSettings) -> list[dict[str, Any]]:
    by_key: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for r in sector_rows:
        by_key.setdefault((int(r["sector"]), int(r["branch"])), []).append(r)
    out: list[dict[str, Any]] = []
    for (sector, branch), vals in by_key.items():
        vals = sorted(vals, key=lambda x: x["q"])
        # Same tracked branch: real-part zero crossing.
        for a, b in zip(vals, vals[1:]):
            if not (a["fourier_quality_gate_ok"] and b["fourier_quality_gate_ok"]):
                continue
            if min(a["dominant_abs_m"], b["dominant_abs_m"]) < settings.candidate_abs_m_min:
                continue
            if min(a["dominant_abs_m_weight"], b["dominant_abs_m_weight"]) < settings.dominant_mode_weight_min:
                continue
            if b["overlap_prev"] < settings.branch_overlap_min:
                continue
            if a["eig_real"] == 0.0 or a["eig_real"] * b["eig_real"] < 0.0:
                if a["eig_real"] == 0.0:
                    qroot = a["q"]
                else:
                    qroot = a["q"] + (b["q"] - a["q"]) * (-a["eig_real"]) / (b["eig_real"] - a["eig_real"])
                out.append({
                    "kind": "fourier_sector_marginal_transition",
                    "sector": sector,
                    "branch": branch,
                    "dominant_abs_m": int(a["dominant_abs_m"] if a["dominant_abs_m_weight"] >= b["dominant_abs_m_weight"] else b["dominant_abs_m"]),
                    "q": float(qroot),
                    "cell_over_core": math.exp(float(qroot)),
                    "q_bracket": [a["q"], b["q"]],
                    "overlap": b["overlap_prev"],
                    "quality_gate": True,
                })
        # Branch-local |lambda| minima, using both adjacent overlaps and fixed m identity.
        for i in range(1, len(vals) - 1):
            l, m, r = vals[i - 1], vals[i], vals[i + 1]
            if not (m["fourier_quality_gate_ok"] and l["fourier_quality_gate_ok"] and r["fourier_quality_gate_ok"]):
                continue
            if m["dominant_abs_m"] < settings.candidate_abs_m_min or m["dominant_abs_m_weight"] < settings.dominant_mode_weight_min:
                continue
            if min(m["overlap_prev"], r["overlap_prev"]) < settings.branch_overlap_min:
                continue
            if m["eig_abs"] < l["eig_abs"] and m["eig_abs"] < r["eig_abs"]:
                depth = m["eig_abs"] / max(min(l["eig_abs"], r["eig_abs"]), 1e-300)
                if depth < 0.95:
                    out.append({
                        "kind": "fourier_sector_isolated_abs_minimum",
                        "sector": sector,
                        "branch": branch,
                        "dominant_abs_m": int(m["dominant_abs_m"]),
                        "dominant_abs_m_weight": float(m["dominant_abs_m_weight"]),
                        "q": float(m["q"]),
                        "cell_over_core": float(m["cell_over_core"]),
                        "eig_abs": float(m["eig_abs"]),
                        "eig_real": float(m["eig_real"]),
                        "eig_imag": float(m["eig_imag"]),
                        "depth_ratio": float(depth),
                        "overlap_prev": float(m["overlap_prev"]),
                        "overlap_next": float(r["overlap_prev"]),
                        "quality_gate": True,
                    })
    return sorted(out, key=lambda x: (x["q"], x["kind"], x["sector"], x["branch"]))
