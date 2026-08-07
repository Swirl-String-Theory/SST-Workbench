from __future__ import annotations

import numpy as np

from .fourier import sample_component
from .qm_energy import geometric_terms
from .native_ext import BackendOptions
from .native_ext.core import (
    link_velocity_batch_arc_exclusion,
    neumann_coupling_matrices_arc_exclusion,
)
from .biot_savart import sign_matrix, fit_normal_rigid_motion


def _samples(link, n: int):
    return [sample_component(component, int(n)) for component in link.components]


def _richardson(values: list[float], ns: list[int]) -> dict:
    if len(values) < 3:
        return {"order_estimate": None, "continuum_estimate": None}
    v0, v1, v2 = map(float, values[-3:])
    n0, n1, n2 = map(float, ns[-3:])
    # Only use the standard factor-two estimate when the grid is geometric.
    r1 = n1 / n0
    r2 = n2 / n1
    if abs(r1-r2) > 1e-12 or r1 <= 1.0:
        return {"order_estimate": None, "continuum_estimate": None}
    d01 = v0-v1
    d12 = v1-v2
    if abs(d12) < 1e-15 or d01*d12 <= 0:
        return {"order_estimate": None, "continuum_estimate": None}
    p = float(np.log(abs(d01/d12))/np.log(r1))
    if not np.isfinite(p) or p <= 0:
        return {"order_estimate": None, "continuum_estimate": None}
    denom = r1**p - 1.0
    estimate = float(v2 + (v2-v1)/denom) if abs(denom) > 1e-15 else None
    return {"order_estimate": p, "continuum_estimate": estimate}


def audit_link_continuum(link, cfg: dict, backend_options: BackendOptions) -> dict:
    ns = [int(x) for x in cfg.get("continuum_sample_ns", [96, 192, 384])]
    if len(ns) < 2 or sorted(ns) != ns or len(set(ns)) != len(ns):
        raise ValueError("continuum_sample_ns must be a strictly increasing list with at least two entries")
    diameter = float(link.diameter)
    epsilon = float(cfg.get("qm_epsilon_D", 0.10))*diameter
    energy_arc = float(cfg.get("self_exclusion_energy_arc_D", 0.20))*diameter
    velocity_arc = float(cfg.get("self_exclusion_velocity_arc_D", 0.25))*diameter
    rep_soft = float(cfg.get("repulsion_softness_D", 0.04))
    rep_margin = float(cfg.get("repulsion_margin", 0.0))
    sectors = sign_matrix(len(link.components))

    rows = []
    for n in ns:
        samples = _samples(link, n)
        curves = [np.ascontiguousarray(s.r, dtype=float) for s in samples]
        length, bending, repulsion = geometric_terms(curves, diameter, rep_soft, rep_margin)
        coupling, energy_backend = neumann_coupling_matrices_arc_exclusion(
            curves, [epsilon], energy_arc, backend_options
        )
        velocity_batches, velocity_backend = link_velocity_batch_arc_exclusion(
            curves, sectors, epsilon, velocity_arc, backend_options
        )
        if velocity_backend != energy_backend:
            raise RuntimeError(f"mixed backend: {velocity_backend} vs {energy_backend}")
        coupling = np.asarray(coupling[0], dtype=float)
        sector_rows = []
        for k, signs in enumerate(sectors):
            fits = fit_normal_rigid_motion(samples, [batch[k] for batch in velocity_batches])
            sector_rows.append({
                "signs": [int(x) for x in signs],
                "sign_string": "".join("+" if x > 0 else "-" for x in signs),
                "neumann_energy_D": float(signs @ coupling @ signs) / max(diameter, 1e-300),
                "relative_equilibrium_score": float(fits["relative_equilibrium_score"]),
            })
        rows.append({
            "sample_n": n,
            "length_over_D": float(length/diameter),
            "bending_times_D": float(bending*diameter),
            "tube_repulsion_dimensionless": float(repulsion),
            "coupling_matrix_over_D": coupling/max(diameter, 1e-300),
            "sectors": sector_rows,
            "backend": energy_backend,
        })

    highest = rows[-1]
    term_names = ["length_over_D", "bending_times_D", "tube_repulsion_dimensionless"]
    term_convergence = {}
    for name in term_names:
        vals = [float(row[name]) for row in rows]
        rel_last = abs(vals[-1]-vals[-2])/max(abs(vals[-1]), 1e-300)
        term_convergence[name] = {
            "values": vals,
            "last_pair_relative_difference": float(rel_last),
            **_richardson(vals, ns),
        }

    sector_convergence = []
    for idx, signs in enumerate(sectors):
        energies = [float(row["sectors"][idx]["neumann_energy_D"]) for row in rows]
        residuals = [float(row["sectors"][idx]["relative_equilibrium_score"]) for row in rows]
        e_rel = abs(energies[-1]-energies[-2])/max(abs(energies[-1]), 1e-300)
        r_rel = abs(residuals[-1]-residuals[-2])/max(abs(residuals[-1]), 1e-300)
        sector_convergence.append({
            "signs": [int(x) for x in signs],
            "sign_string": "".join("+" if x > 0 else "-" for x in signs),
            "neumann_energy_D_values": energies,
            "neumann_last_pair_relative_difference": float(e_rel),
            "relative_equilibrium_values": residuals,
            "relative_equilibrium_last_pair_relative_difference": float(r_rel),
            "neumann_richardson": _richardson(energies, ns),
            "equilibrium_richardson": _richardson(residuals, ns),
        })

    tolerance = float(cfg.get("continuum_relative_tolerance", 0.05))
    max_rel = max(
        [x["last_pair_relative_difference"] for x in term_convergence.values()]
        + [x["neumann_last_pair_relative_difference"] for x in sector_convergence]
        + [x["relative_equilibrium_last_pair_relative_difference"] for x in sector_convergence]
    )
    return {
        "link_id": link.link_id,
        "diameter_D": diameter,
        "sample_ns": ns,
        "epsilon_D": epsilon/diameter,
        "self_exclusion_energy_arc_D": energy_arc/diameter,
        "self_exclusion_velocity_arc_D": velocity_arc/diameter,
        "rows": rows,
        "term_convergence": term_convergence,
        "sector_convergence": sector_convergence,
        "max_last_pair_relative_difference": float(max_rel),
        "continuum_relative_tolerance": tolerance,
        "continuum_pass": bool(max_rel <= tolerance),
        "status": (
            "[NUMERICAL] Fixed-physical-arc self exclusion with N refinement. "
            "Pass means only that the listed baseline diagnostics meet the requested last-pair tolerance."
        ),
    }
