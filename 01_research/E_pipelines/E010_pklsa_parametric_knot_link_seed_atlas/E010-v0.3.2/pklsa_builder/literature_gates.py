from __future__ import annotations

import math
from typing import Any

import numpy as np

IDEAL_TREFOIL_ROPELENGTH_RADIUS = 32.742934477
IDEAL_TREFOIL_ROPELENGTH_DIAMETER = IDEAL_TREFOIL_ROPELENGTH_RADIUS / 2.0


def _finite(x: Any) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except Exception:
        return False


def _gate(status: str, *, hard: bool, source: str, rationale: str, **payload: Any) -> dict[str, Any]:
    return {
        "status": status,
        "hard": bool(hard),
        "source": source,
        "rationale": rationale,
        **payload,
    }


def signed_frenet_metrics(sample: dict[str, Any]) -> dict[str, Any]:
    """Orientation-sensitive Frenet diagnostics on one periodic sample.

    The integral quadrature is performed with polygonal edge lengths as ds weights.
    These are numerical observables, not topological invariants.
    """
    p = np.asarray(sample["points"], float)
    tau = np.asarray(sample["tau"], float)
    kappa = np.asarray(sample["kappa"], float)
    t = np.asarray(sample["tangent_raw"], float)
    t /= np.maximum(np.linalg.norm(t, axis=1)[:, None], 1e-300)

    edge = np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1)
    tau_next = np.roll(tau, -1)
    kap_next = np.roll(kappa, -1)
    finite_tau = np.isfinite(tau) & np.isfinite(tau_next) & np.isfinite(edge)
    finite_kap = np.isfinite(kappa) & np.isfinite(kap_next) & np.isfinite(edge)

    tau_integral = float(np.sum(0.5 * (tau[finite_tau] + tau_next[finite_tau]) * edge[finite_tau])) if np.any(finite_tau) else None
    kappa_total = float(np.sum(0.5 * (kappa[finite_kap] + kap_next[finite_kap]) * edge[finite_kap])) if np.any(finite_kap) else None

    dots = np.einsum("ij,ij->i", t, np.roll(t, -1, axis=0))
    turn = np.arccos(np.clip(dots, -1.0, 1.0))
    max_turn = float(np.nanmax(turn)) if len(turn) else None
    subcurve_curvature = 0.5 * (kappa + kap_next) * edge
    finite_subcurve = np.isfinite(subcurve_curvature)
    max_subcurve_curvature = float(np.nanmax(subcurve_curvature[finite_subcurve])) if np.any(finite_subcurve) else None

    finite_abs_tau = np.abs(tau[np.isfinite(tau)])
    if len(finite_abs_tau):
        scale = max(float(np.percentile(finite_abs_tau, 90)), 1e-14)
        zero_tol = max(1e-10 * scale, 1e-12)
        signs = np.zeros(len(tau), dtype=np.int8)
        signs[tau > zero_tol] = 1
        signs[tau < -zero_tol] = -1
        nz = signs[signs != 0]
        sign_changes = int(np.sum(nz != np.roll(nz, 1))) if len(nz) > 1 else 0
        # Each physical transition is counted once on a periodic ring, including wrap-around.
        zero_fraction = float(np.mean(signs == 0))
        signed_fraction = float(np.mean(signs))
    else:
        zero_tol = None
        sign_changes = None
        zero_fraction = None
        signed_fraction = None

    hmax = float(np.max(edge)) if len(edge) else None
    kmax = float(np.nanmax(kappa[np.isfinite(kappa)])) if np.any(np.isfinite(kappa)) else None
    chord_deviation_bound_proxy = (kmax * hmax * hmax / 8.0) if _finite(kmax) and _finite(hmax) else None

    phase_mod = None
    if _finite(tau_integral):
        phase_mod = float(((tau_integral + math.pi) % (2.0 * math.pi)) - math.pi)

    return {
        "tau_signed_integral": tau_integral,
        "kappa_total": kappa_total,
        "max_tangent_turn_rad": max_turn,
        "max_subcurve_total_curvature_estimate_rad": max_subcurve_curvature,
        "max_edge_length": hmax,
        "chord_deviation_bound_proxy": chord_deviation_bound_proxy,
        "tau_zero_tolerance": zero_tol,
        "tau_zero_fraction": zero_fraction,
        "tau_sign_changes_numeric": sign_changes,
        "tau_signed_fraction_numeric": signed_fraction,
        "hasimoto_phase_mod_2pi_rad": phase_mod,
    }


def _writhe_order(levels: list[dict[str, Any]], numeric_floor: float) -> tuple[list[float], list[dict[str, float]], str | None]:
    vals = []
    for lev in levels:
        w = lev.get("metrics", {}).get("Wr")
        if _finite(w):
            vals.append((int(lev["resolution"]), float(w)))
    if len(vals) < 3:
        return [], [], "fewer than three finite writhe levels"

    diffs = []
    for i in range(len(vals) - 1):
        n0, w0 = vals[i]
        n1, w1 = vals[i + 1]
        diffs.append({"N0": n0, "N1": n1, "abs_delta": abs(w1 - w0)})

    if all(d["abs_delta"] <= numeric_floor for d in diffs[-min(3, len(diffs)) :]):
        return [math.inf], diffs, None

    orders = []
    for i in range(len(diffs) - 1):
        d0 = diffs[i]["abs_delta"]
        d1 = diffs[i + 1]["abs_delta"]
        n0 = float(diffs[i]["N0"])
        n1 = float(diffs[i]["N1"])
        n2 = float(diffs[i + 1]["N1"])
        r0 = n1 / n0
        r1 = n2 / n1
        if d0 <= numeric_floor or d1 <= numeric_floor or r0 <= 1 or r1 <= 1:
            continue
        # Exact for a geometric ladder; for unequal ratios this remains a local asymptotic estimator.
        r = math.sqrt(r0 * r1)
        orders.append(math.log(d0 / d1) / math.log(r))
    if not orders:
        return [], diffs, "no stable finite-difference order estimate"
    return orders, diffs, None


def evaluate_generic_literature_gates(levels: list[dict[str, Any]], config: Any) -> dict[str, Any]:
    """Evaluate source-independent, literature-derived geometry integrity gates."""
    enabled = bool(getattr(config, "literature_gates", True))
    if not enabled:
        return {"enabled": False, "hard_gate_pass": True, "gates": {}}

    gates: dict[str, Any] = {}
    finest = levels[-1] if levels else None

    # Li & Peters: numerical proxy for the sufficient isotopy conditions.
    if not finest:
        gates["G1_isotopy_safe_sampling"] = _gate(
            "INDETERMINATE", hard=True, source="Li & Peters (2013)",
            rationale="No qualification level is available.",
        )
    else:
        comps = finest.get("component_metrics", [])
        failures = []
        details = []
        for i, m in enumerate(comps):
            turn = m.get("max_tangent_turn_rad")
            subcurve_k = m.get("max_subcurve_total_curvature_estimate_rad")
            dev = m.get("chord_deviation_bound_proxy")
            reach = m.get("reach")
            turn_limit = float(getattr(config, "isotopy_turn_limit_rad", math.pi / 2.0))
            tube_fraction = float(getattr(config, "isotopy_tube_fraction", 0.5))
            # Li--Peters criterion is total curvature of each subcurve < pi/2.
            # We integrate spline curvature over each sampling interval and also report
            # the tangent turning angle as an independent numerical cross-check.
            turn_ok = _finite(subcurve_k) and float(subcurve_k) < turn_limit
            tube_ok = _finite(dev) and _finite(reach) and float(reach) > 0 and float(dev) < tube_fraction * float(reach)
            details.append({
                "component": i,
                "max_tangent_turn_rad": turn,
                "max_subcurve_total_curvature_estimate_rad": subcurve_k,
                "subcurve_total_curvature_limit_rad": turn_limit,
                "chord_deviation_bound_proxy": dev,
                "reach": reach,
                "tube_fraction_limit": tube_fraction,
                "turn_ok": bool(turn_ok),
                "tube_ok": bool(tube_ok),
            })
            if not (turn_ok and tube_ok):
                failures.append(i)
        if not comps:
            status = "INDETERMINATE"
        else:
            status = "PASS" if not failures else "FAIL"
        gates["G1_isotopy_safe_sampling"] = _gate(
            status, hard=True, source="Li & Peters (2013), Isotopic Convergence Theorem",
            rationale=(
                "Numerical sufficient-condition proxy: estimated total curvature on every sample interval stays below pi/2 and a curvature-based chord-deviation bound "
                "stays inside a conservative fraction of the estimated embedded tube radius. This is not an exact ambient-isotopy proof."
            ),
            components=details,
        )

    # Cantarella: O(N^-2) writhe convergence expected for smooth curve vs inscribed polygon.
    if not getattr(config, "expensive_metrics", True):
        gates["G2_writhe_quadratic_convergence"] = _gate(
            "INDETERMINATE", hard=True, source="Cantarella (2002)",
            rationale="Writhe is disabled in this configuration.",
        )
    else:
        floor = float(getattr(config, "writhe_order_numeric_floor", 1e-10))
        orders, diffs, reason = _writhe_order(levels, floor)
        pmin = float(getattr(config, "writhe_order_min", 1.25))
        if reason:
            status = "INDETERMINATE"
        elif orders and math.isinf(orders[-1]):
            status = "PASS"
        else:
            tail = orders[-min(2, len(orders)) :] if orders else []
            p_est = float(np.median(tail)) if tail else None
            status = "PASS" if _finite(p_est) and p_est >= pmin else "FAIL"
        gates["G2_writhe_quadratic_convergence"] = _gate(
            status, hard=True, source="Cantarella (2002), SIAM Journal on Numerical Analysis",
            rationale=(
                "For smooth curves sampled by inscribed polygons the writhe error is O(N^-2). "
                "PKLSA estimates the local asymptotic order from successive resolution differences; the threshold is intentionally below 2 to allow pre-asymptotic finite-resolution data."
            ),
            estimated_orders=orders,
            successive_differences=diffs,
            minimum_accepted_order=pmin,
            numeric_floor=floor,
            indeterminate_reason=reason,
        )

    # Liu et al. 2026: unsigned Frenet data can lose mirror/branch information.
    if not finest:
        chirality_status = "INDETERMINATE"
        chirality_payload = {}
    else:
        comps = finest.get("component_metrics", [])
        signed_tau = all(_finite(m.get("tau_signed_integral")) for m in comps) if comps else False
        wr_present = finest.get("metrics", {}).get("Wr") is not None
        chirality_status = "PASS" if signed_tau and wr_present else "FAIL"
        chirality_payload = {
            "signed_torsion_integrals": [m.get("tau_signed_integral") for m in comps],
            "numeric_torsion_sign_changes": [m.get("tau_sign_changes_numeric") for m in comps],
            "signed_writhe_present": bool(wr_present),
            "branch_invariant_warning": (
                "The exact c(tau) branch invariant depends on infinite-order torsion zeros and cannot be certified from finite samples. "
                "PKLSA therefore preserves signed torsion and signed writhe rather than reducing geometry identity to {kappa, |tau|}."
            ),
        }
    gates["G3_signed_frenet_chirality_completeness"] = _gate(
        chirality_status, hard=True, source="Liu, Wang, Tian & Wang (2026), arXiv:2608.09194",
        rationale="Signed torsion and an orientation-sensitive observable are retained so mirror/chirality information is not discarded by an unsigned Frenet descriptor.",
        **chirality_payload,
    )

    # Brizard/Hasimoto is retained as a diagnostic only; generic closed geometry does not imply an NLSE traveling-wave solution.
    phase = []
    if finest:
        phase = [m.get("hasimoto_phase_mod_2pi_rad") for m in finest.get("component_metrics", [])]
    gates["D1_hasimoto_phase_holonomy"] = _gate(
        "DIAGNOSTIC", hard=False, source="Hasimoto (1972); Brizard (2026)",
        rationale=(
            "Reports the signed torsion phase modulo 2pi. Closed geometry alone is insufficient to assert the special NLSE/elastica traveling-wave closure conditions."
        ),
        component_phase_mod_2pi_rad=phase,
    )

    hard = [g for g in gates.values() if g.get("hard")]
    hard_gate_pass = bool(hard) and all(g.get("status") == "PASS" for g in hard)
    return {"enabled": True, "hard_gate_pass": hard_gate_pass, "gates": gates}


def _is_ideal_like(carrier: Any) -> bool:
    sf = str(getattr(carrier, "source_family", "") or "").lower()
    role = str(getattr(carrier, "source_role", "") or "").lower()
    md = getattr(carrier, "metadata", {}) or {}
    return (
        sf in {"gilbert_ideal", "knotplot_ideal", "ridgerunner"}
        or "ideal" in sf
        or "ideal" in role
        or md.get("reference_ropelength") is not None
    )


def torus_analytic_length_ratio(p: int, q: int, lam: float, samples: int = 131072) -> float:
    """Return L/(2*pi*R) for the standard Oberti-Ricca torus-knot parametrization."""
    p = int(p); q = int(q); lam = float(lam)
    if p <= 0 or q <= 0 or not (0.0 < lam < 1.0):
        raise ValueError("p,q must be positive and 0 < lambda < 1")
    w = q / p
    alpha = np.linspace(0.0, 2.0 * math.pi * p, int(samples), endpoint=False)
    integrand = np.sqrt((1.0 + lam * np.cos(w * alpha)) ** 2 + (lam * w) ** 2)
    return float(np.mean(integrand) * p)


def evaluate_contextual_literature_gates(carrier: Any, qualification: dict[str, Any], config: Any) -> dict[str, Any]:
    gates: dict[str, Any] = {}
    levels = qualification.get("levels", [])
    finest = levels[-1] if levels else {}
    metrics = finest.get("metrics", {})
    topo = str(getattr(carrier, "topology_id", "") or "")
    md = getattr(carrier, "metadata", {}) or {}

    # Przybyl & Pieranski high-resolution ideal trefoil benchmark.
    if topo == "3_1" and _is_ideal_like(carrier):
        value = metrics.get("Rop")
        tol = float(getattr(config, "ideal_trefoil_rel_tol", 0.01))
        if _finite(value):
            rel = abs(float(value) - IDEAL_TREFOIL_ROPELENGTH_DIAMETER) / IDEAL_TREFOIL_ROPELENGTH_DIAMETER
            status = "PASS" if rel <= tol else "FAIL"
        else:
            rel = None
            status = "INDETERMINATE"
        upstream = md.get("reference_ropelength")
        if _finite(upstream):
            upstream_rel = abs(float(upstream) - IDEAL_TREFOIL_ROPELENGTH_DIAMETER) / IDEAL_TREFOIL_ROPELENGTH_DIAMETER
            upstream_status = "PASS" if upstream_rel <= tol else "FAIL"
        else:
            upstream_rel = None
            upstream_status = "INDETERMINATE"
        gates["B1_ideal_trefoil_ropelength"] = _gate(
            status,
            hard=bool(getattr(config, "enforce_ideal_trefoil_benchmark", False)),
            source="Przybyl & Pieranski (2014)",
            rationale=(
                "Compares the recomputed PKLSA diameter-convention ropelength L/Thi against 16.3714672385, "
                "equivalent to the paper's radius-convention 32.742934477. If an upstream ideal-knot reference length is present, "
                "it is audited independently so source accuracy is not conflated with PKLSA's numerical reach estimator."
            ),
            measured_ropelength_diameter=value,
            benchmark_ropelength_diameter=IDEAL_TREFOIL_ROPELENGTH_DIAMETER,
            benchmark_ropelength_radius=IDEAL_TREFOIL_ROPELENGTH_RADIUS,
            relative_error=rel,
            relative_tolerance=tol,
            upstream_reference_ropelength_diameter=upstream,
            upstream_reference_relative_error=upstream_rel,
            upstream_reference_status=upstream_status,
        )
    else:
        gates["B1_ideal_trefoil_ropelength"] = _gate(
            "NOT_APPLICABLE", hard=False, source="Przybyl & Pieranski (2014)",
            rationale="Benchmark applies only to explicitly ideal-like 3_1 carriers.",
        )

    # Oberti & Ricca torus-knot analytic benchmark when the source declares its parametrization.
    keys = ("torus_p", "torus_q", "torus_lambda")
    if all(k in md for k in keys):
        p, q, lam = int(md["torus_p"]), int(md["torus_q"]), float(md["torus_lambda"])
        w = q / p
        lam_cr = 1.0 / (1.0 + w * w)
        payload: dict[str, Any] = {
            "p": p, "q": q, "w": w, "lambda": lam, "lambda_critical": lam_cr,
            "minimum_crossing_number": min(p * (q - 1), q * (p - 1)),
        }
        R = md.get("torus_major_radius")
        native_L = qualification.get("scale_context", {}).get("native_total_length")
        if _finite(R) and _finite(native_L) and float(R) > 0:
            analytic_ratio = torus_analytic_length_ratio(p, q, lam)
            measured_ratio = float(native_L) / (2.0 * math.pi * float(R))
            rel = abs(measured_ratio - analytic_ratio) / max(abs(analytic_ratio), 1e-15)
            tol = float(getattr(config, "torus_length_rel_tol", 5e-3))
            status = "PASS" if rel <= tol else "FAIL"
            payload.update({
                "analytic_L_over_2piR": analytic_ratio,
                "measured_L_over_2piR": measured_ratio,
                "relative_error": rel,
                "relative_tolerance": tol,
            })
        else:
            status = "DIAGNOSTIC"
            payload["note"] = "torus_major_radius metadata is absent; only lambda_critical and crossing diagnostics are available"
        gates["B2_torus_analytic_geometry"] = _gate(
            status, hard=False, source="Oberti & Ricca (2016)",
            rationale="Checks the declared standard torus-knot parametrization against analytic length and critical-aspect-ratio relations when sufficient metadata exists.",
            **payload,
        )
    else:
        gates["B2_torus_analytic_geometry"] = _gate(
            "NOT_APPLICABLE", hard=False, source="Oberti & Ricca (2016)",
            rationale="Requires explicit torus_p, torus_q and torus_lambda source metadata.",
        )

    # Maggioni/Kivotides handoff: eligibility only, never a dynamics claim.
    reach = metrics.get("reach")
    wr = metrics.get("Wr")
    dynamics_ready = _finite(reach) and float(reach) > 0 and wr is not None
    gates["D2_vortex_dynamics_handoff"] = _gate(
        "READY" if dynamics_ready else "INDETERMINATE", hard=False,
        source="Maggioni et al. (2010); Kivotides & Leonard (2020)",
        rationale=(
            "Geometry has the minimum scale/orientation observables needed to seed a later finite-core/Biot-Savart calculation. "
            "No circulation, core profile, Reynolds number or dynamical stability is inferred here."
        ),
        positive_reach=bool(_finite(reach) and float(reach) > 0),
        signed_writhe_present=bool(wr is not None),
    )
    return gates


def merge_contextual_gates(report: dict[str, Any], contextual: dict[str, Any]) -> dict[str, Any]:
    out = dict(report or {})
    gates = dict(out.get("gates", {}))
    gates.update(contextual)
    out["gates"] = gates
    hard = [g for g in gates.values() if g.get("hard")]
    out["hard_gate_pass"] = all(g.get("status") == "PASS" for g in hard) if hard else True
    out["status_counts"] = {
        s: sum(1 for g in gates.values() if g.get("status") == s)
        for s in sorted({str(g.get("status")) for g in gates.values()})
    }
    return out
