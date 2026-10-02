from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np

from . import __version__
from .billiard import scan_billiard
from .constants import SST_CONSTANTS, R_C
from .contact import extract_contact_map, PeriodicLiftMap
from .force_balance import geometric_force_balance
from .gates import Gate, DEFAULT_THRESHOLDS, status
from .geometry import PeriodicCurve, compute_geometry, resample_closed_curve, sampled_thickness_proxy
from .hydrodynamics import hydrodynamic_force_test
from .io import write_xyz
from .plotting import plot_curve, plot_contact_map, plot_force_compatibility, plot_hydro_sweep
from .util import circular_distance, csv_dump, json_dump, sha256_array


def _finite_stats(array: np.ndarray) -> dict[str, float]:
    values = np.asarray(array, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return {"min": float("nan"), "max": float("nan"), "mean": float("nan"), "rms": float("nan")}
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "rms": float(np.sqrt(np.mean(values * values))),
    }


def _contact_rows(contact) -> list[dict[str, Any]]:
    rows = []
    for i, s in enumerate(contact.s):
        rows.append({
            "index": i,
            "s": float(s),
            "branch_a": float(contact.branch_a[i]),
            "branch_b": float(contact.branch_b[i]),
            "branch_a_lift": float(contact.branch_a_lift[i]),
            "branch_b_lift": float(contact.branch_b_lift[i]),
            "pt_a": float(contact.pt_a[i]),
            "pt_b": float(contact.pt_b[i]),
            "orth_a": float(contact.orth_a[i]),
            "orth_b": float(contact.orth_b[i]),
        })
    return rows


def analyze_curve(
    raw_points: np.ndarray,
    out: Path,
    *,
    source: dict[str, Any],
    samples: int = 256,
    hydro_samples: int = 96,
    exclusion_fraction: float = 0.03,
    core_ratios: list[float] | None = None,
    physical_thickness_m: float = R_C,
    skip_hydro: bool = False,
    hydro_interactions: list[str] | None = None,
    local_band: int = 3,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    if samples < 16 or hydro_samples < 16:
        raise ValueError("samples and hydro_samples must both be >= 16")
    if not (0.0 < exclusion_fraction < 0.5):
        raise ValueError("exclusion_fraction must lie in (0, 0.5)")
    if physical_thickness_m <= 0.0:
        raise ValueError("physical_thickness_m must be positive")
    if local_band < 0:
        raise ValueError("local_band must be non-negative")
    thresholds_all = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        thresholds_all.update(thresholds)
    if core_ratios is None:
        core_ratios = [0.10, 0.20, 0.35, 0.50, 0.75, 1.00]
    if not core_ratios or any(float(value) <= 0.0 for value in core_ratios):
        raise ValueError("all core_ratios must be positive")
    if hydro_interactions is None:
        hydro_interactions = ["full", "nonlocal"]
    unknown_interactions = set(hydro_interactions) - {"full", "local", "nonlocal"}
    if unknown_interactions:
        raise ValueError(f"unknown hydrodynamic interactions: {sorted(unknown_interactions)}")

    points = resample_closed_curve(raw_points, samples)
    geom = compute_geometry(points)
    thickness = sampled_thickness_proxy(geom, exclusion_fraction)
    reported_length = source.get("reported_length")
    reported_diameter = source.get("diameter")
    source_length_relative_error = None
    source_diameter_relative_error = None
    source_consistency = True
    if reported_length is not None and float(reported_length) > 0.0:
        source_length_relative_error = abs(geom.length - float(reported_length)) / float(reported_length)
        source_consistency = source_consistency and source_length_relative_error <= thresholds_all["H0_source_length_relative_max"]
    if reported_diameter is not None and float(reported_diameter) > 0.0:
        source_diameter_relative_error = abs(2.0 * thickness["thickness_proxy"] - float(reported_diameter)) / float(reported_diameter)
        source_consistency = source_consistency and source_diameter_relative_error <= thresholds_all["H0_source_diameter_relative_max"]
    contact = extract_contact_map(geom, exclusion_fraction)
    map_a = PeriodicLiftMap(contact.s, contact.branch_a_lift, contact.branch_winding_a)
    map_b = PeriodicLiftMap(contact.s, contact.branch_b_lift, contact.branch_winding_b)
    billiard_a = scan_billiard(map_a, 9, branch_name="branch_a")
    billiard_b = scan_billiard(map_b, 9, branch_name="branch_b")
    billiard = billiard_a if billiard_a.closure_residual <= billiard_b.closure_residual else billiard_b
    orbit_distances = circular_distance(billiard_a.orbit[:, None], billiard_b.orbit[None, :])
    paired_orbit_hausdorff = float(max(
        np.max(np.min(orbit_distances, axis=1)),
        np.max(np.min(orbit_distances, axis=0)),
    ))
    sigma, tau = (map_a, map_b) if billiard.map_branch == "branch_a" else (map_b, map_a)
    curve = PeriodicCurve(points)
    force = geometric_force_balance(curve, geom.s, sigma, tau)

    write_xyz(out / "geometry" / "resampled_curve.xyz", points)
    csv_dump(out / "contact" / "contact_map.csv", _contact_rows(contact))
    force_rows = []
    for i, s in enumerate(force.s):
        force_rows.append({
            "index": i,
            "s": float(s),
            "F_in_scalar": float(force.scalar_in[i]) if np.isfinite(force.scalar_in[i]) else "",
            "F_out_scalar": float(force.scalar_out[i]) if np.isfinite(force.scalar_out[i]) else "",
            "local_balance_residual": float(force.local_balance_residual[i]),
            "compatibility_residual": float(force.compatibility_residual[i]),
            "determinant_abs": float(force.determinant_abs[i]),
            "sigma_prime": float(force.sigma_derivative[i]),
            "tau_prime": float(force.tau_derivative[i]),
            "inverse_compatibility_residual": float(force.inverse_compatibility_residual[i]),
        })
    csv_dump(out / "force" / "geometric_force_balance.csv", force_rows)

    orbit_xyz = curve.eval(billiard.orbit)
    write_xyz(out / "billiard" / "orbit9.xyz", orbit_xyz)
    json_dump(out / "billiard" / "billiard9.json", {
        **asdict(billiard),
        "orbit": [float(x) for x in billiard.orbit],
        "orbit_xyz": orbit_xyz.tolist(),
        "branch_a_candidate": {**asdict(billiard_a), "orbit": billiard_a.orbit.tolist()},
        "branch_b_candidate": {**asdict(billiard_b), "orbit": billiard_b.orbit.tolist()},
    })

    plot_curve(points, out / "plots" / "curve_and_9_billiard.png", orbit_xyz)
    plot_contact_map(contact.s, contact.branch_a, contact.branch_b, out / "plots" / "contact_map.png")
    plot_force_compatibility(force.s, force.compatibility_residual, out / "plots" / "force_compatibility.png")

    hydro_rows: list[dict[str, Any]] = []
    hydro_npz: dict[str, np.ndarray] = {}
    if not skip_hydro:
        hydro_points = resample_closed_curve(points, hydro_samples)
        hydro_geom = compute_geometry(hydro_points)
        hydro_thickness = sampled_thickness_proxy(hydro_geom, exclusion_fraction)["thickness_proxy"]
        for interaction in hydro_interactions:
            for core_ratio in core_ratios:
                result = hydrodynamic_force_test(
                    hydro_geom,
                    hydro_thickness,
                    float(core_ratio),
                    physical_thickness_m,
                    interaction=interaction,
                    local_band=local_band,
                )
                row = {
                    "interaction": interaction,
                    "local_band": local_band,
                    "core_ratio": float(core_ratio),
                    "energy_dimensionless": result.energy_dimensionless,
                    "force_density_rms_dimensionless": result.force_density_rms_dimensionless,
                    "force_density_rms_N_m": result.force_density_rms_N_m,
                    "normal_alignment_cosine": result.normal_alignment_cosine,
                    "fitted_shape_residual": result.fitted_shape_residual,
                    "fitted_scale_N": result.fitted_scale_N,
                    "tension_mean_N": float(np.nanmean(result.tension_N)),
                    "tension_std_N": float(np.nanstd(result.tension_N)),
                    "tension_cv": result.tension_cv,
                    "binormal_leakage": result.binormal_leakage,
                    "tangential_leakage": result.tangential_leakage,
                    "relative_equilibrium_residual": result.relative_equilibrium_residual,
                    "translation_x_m_s": float(result.translation_m_s[0]),
                    "translation_y_m_s": float(result.translation_m_s[1]),
                    "translation_z_m_s": float(result.translation_m_s[2]),
                    "rotation_x_s_inv": float(result.rotation_s_inv[0]),
                    "rotation_y_s_inv": float(result.rotation_s_inv[1]),
                    "rotation_z_s_inv": float(result.rotation_s_inv[2]),
                }
                hydro_rows.append(row)
                tag = f"{interaction}_{str(core_ratio).replace('.', 'p')}"
                hydro_npz[f"force_density_bar_{tag}"] = result.force_density_dimensionless
                hydro_npz[f"force_density_SI_{tag}"] = result.force_density_physical
                hydro_npz[f"tension_N_{tag}"] = result.tension_N
        csv_dump(out / "hydrodynamics" / "core_sweep.csv", hydro_rows)
        np.savez_compressed(out / "hydrodynamics" / "fields.npz", points=hydro_points, **hydro_npz)
        plot_hydro_sweep(hydro_rows, out / "plots" / "hydrodynamic_core_sweep.png")

    orth_values = np.r_[contact.orth_a, contact.orth_b]
    orth_rms = float(np.sqrt(np.nanmean(orth_values * orth_values)))
    full_rows = [row for row in hydro_rows if row["interaction"] == "full"]
    nonlocal_rows = [row for row in hydro_rows if row["interaction"] == "nonlocal"]
    h5_passes = [row["relative_equilibrium_residual"] <= thresholds_all["H5_relative_equilibrium_max"] for row in full_rows]
    h6_passes = [
        row["fitted_shape_residual"] <= thresholds_all["H6_force_shape_residual_max"]
        and row["tension_cv"] <= thresholds_all["H6_tension_cv_max"]
        and row["binormal_leakage"] <= thresholds_all["H6_binormal_leakage_max"]
        and row["normal_alignment_cosine"] >= thresholds_all["H6_alignment_min"]
        and row["fitted_scale_N"] > 0.0
        for row in full_rows
    ]
    hydro_pass_fraction = float(np.mean(np.asarray(h5_passes) & np.asarray(h6_passes))) if full_rows else 0.0
    h8_passes = [
        row["fitted_shape_residual"] <= thresholds_all["H8_nonlocal_force_shape_residual_max"]
        and row["normal_alignment_cosine"] >= thresholds_all["H8_nonlocal_alignment_min"]
        for row in nonlocal_rows
    ]

    gates = [
        Gate("H0", "Input, discretization, and source-scale integrity", status(geom.edge_ratio <= thresholds_all["H0_edge_ratio_max"] and source_consistency), "NUMERICAL", {
            "point_count": samples,
            "length": geom.length,
            "edge_ratio": geom.edge_ratio,
            "edge_cv": geom.edge_cv,
            "points_sha256": sha256_array(points),
            "source_length_relative_error": source_length_relative_error,
            "source_diameter_relative_error": source_diameter_relative_error,
        }, {
            "edge_ratio_max": thresholds_all["H0_edge_ratio_max"],
            "source_length_relative_max": thresholds_all["H0_source_length_relative_max"],
            "source_diameter_relative_max": thresholds_all["H0_source_diameter_relative_max"],
        }),
        Gate("H1", "Two-branch contact-map extraction", status(contact.completeness_fraction >= thresholds_all["H1_contact_completeness_min"] and orth_rms <= thresholds_all["H1_contact_orth_rms_max"]), "GEOMETRIC_NUMERICAL", {
            "completeness_fraction": contact.completeness_fraction,
            "orthogonality_rms": orth_rms,
            "contact_thickness_median": contact.thickness_contact_median,
            "contact_thickness_min": contact.thickness_contact_min,
        }, {"completeness_min": thresholds_all["H1_contact_completeness_min"], "orthogonality_rms_max": thresholds_all["H1_contact_orth_rms_max"]}),
        Gate("H2", "Contact branches are degree-one approximate inverses", status(contact.inverse_residual_rms <= thresholds_all["H2_inverse_rms_max"] and contact.branch_winding_a == 1 and contact.branch_winding_b == 1), "GEOMETRIC_NUMERICAL", {
            "inverse_residual_rms": contact.inverse_residual_rms,
            "branch_winding_a": contact.branch_winding_a,
            "branch_winding_b": contact.branch_winding_b,
        }, {"inverse_rms_max": thresholds_all["H2_inverse_rms_max"], "winding_required": 1}),
        Gate("H3", "Paired primitive 9-billiard on inverse branches", status(
            max(billiard_a.closure_residual, billiard_b.closure_residual) <= thresholds_all["H3_billiard_closure_max"]
            and min(billiard_a.min_lower_period_residual, billiard_b.min_lower_period_residual) >= thresholds_all["H3_lower_period_min"]
            and min(billiard_a.unique_orbit_points, billiard_b.unique_orbit_points) >= thresholds_all["H3_unique_points_min"]
            and paired_orbit_hausdorff <= thresholds_all["H3_paired_orbit_hausdorff_max"]
        ), "NUMERICAL_CONJECTURE_TEST", {
            "selected_branch": billiard.map_branch,
            "selected_seed": billiard.seed,
            "branch_a_closure_residual": billiard_a.closure_residual,
            "branch_b_closure_residual": billiard_b.closure_residual,
            "branch_a_min_lower_period_residual": billiard_a.min_lower_period_residual,
            "branch_b_min_lower_period_residual": billiard_b.min_lower_period_residual,
            "branch_a_unique_orbit_points": billiard_a.unique_orbit_points,
            "branch_b_unique_orbit_points": billiard_b.unique_orbit_points,
            "paired_orbit_hausdorff": paired_orbit_hausdorff,
        }, {
            "closure_max_each_branch": thresholds_all["H3_billiard_closure_max"],
            "lower_period_min_each_branch": thresholds_all["H3_lower_period_min"],
            "unique_points_min_each_branch": thresholds_all["H3_unique_points_min"],
            "paired_orbit_hausdorff_max": thresholds_all["H3_paired_orbit_hausdorff_max"],
        }),
        Gate("H4", "Carlen contact-force compatibility", status(max(force.compatibility_relative_l2, force.inverse_compatibility_relative_l2) <= thresholds_all["H4_force_compatibility_max"] and force.ill_conditioned_fraction <= thresholds_all["H4_ill_conditioned_fraction_max"] and force.local_balance_relative_l2 <= thresholds_all["H4_local_balance_max"]), "GEOMETRIC_MECHANICAL_BRIDGE", {
            "compatibility_relative_l2": force.compatibility_relative_l2,
            "inverse_compatibility_relative_l2": force.inverse_compatibility_relative_l2,
            "local_balance_relative_l2": force.local_balance_relative_l2,
            "ill_conditioned_fraction": force.ill_conditioned_fraction,
        }, {"compatibility_max": thresholds_all["H4_force_compatibility_max"], "ill_conditioned_fraction_max": thresholds_all["H4_ill_conditioned_fraction_max"], "local_balance_max": thresholds_all["H4_local_balance_max"]}, note="The thesis explicitly states that this condition is not yet derived from ropelength minimization."),
        Gate("H5", "Regularized Biot-Savart relative equilibrium", status(any(h5_passes) if full_rows else None), "INDEPENDENT_HYDRODYNAMIC_PROXY", {
            "core_sweep": [{"core_ratio": row["core_ratio"], "residual": row["relative_equilibrium_residual"]} for row in full_rows],
        }, {"relative_equilibrium_max": thresholds_all["H5_relative_equilibrium_max"]}),
        Gate("H6", "Hamiltonian energy-gradient shape and emergent tension", status(any(h6_passes) if full_rows else None), "INDEPENDENT_HYDRODYNAMIC_PROXY", {
            "core_sweep": [{
                "core_ratio": row["core_ratio"],
                "shape_residual": row["fitted_shape_residual"],
                "tension_cv": row["tension_cv"],
                "binormal_leakage": row["binormal_leakage"],
                "alignment_cosine": row["normal_alignment_cosine"],
                "fitted_scale_N": row["fitted_scale_N"],
            } for row in full_rows],
        }, {"shape_residual_max": thresholds_all["H6_force_shape_residual_max"], "tension_cv_max": thresholds_all["H6_tension_cv_max"], "binormal_leakage_max": thresholds_all["H6_binormal_leakage_max"], "alignment_min": thresholds_all["H6_alignment_min"], "fitted_scale_positive": True}),
        Gate("H7", "Finite-core robustness across a/thickness sweep", status(hydro_pass_fraction >= thresholds_all["H7_core_sweep_pass_fraction_min"] if full_rows else None), "ROBUSTNESS", {
            "joint_pass_fraction": hydro_pass_fraction,
            "core_ratios": core_ratios,
        }, {"joint_pass_fraction_min": thresholds_all["H7_core_sweep_pass_fraction_min"]}),
        Gate("H8", "Nonlocal hydrodynamic contact-force guard", status(any(h8_passes) if nonlocal_rows else None), "INDEPENDENT_NONLOCAL_HYDRODYNAMIC_PROXY", {
            "core_sweep": [{
                "core_ratio": row["core_ratio"],
                "shape_residual": row["fitted_shape_residual"],
                "alignment_cosine": row["normal_alignment_cosine"],
                "force_density_rms_N_m": row["force_density_rms_N_m"],
            } for row in nonlocal_rows],
            "local_band": local_band,
        }, {
            "shape_residual_max": thresholds_all["H8_nonlocal_force_shape_residual_max"],
            "alignment_min": thresholds_all["H8_nonlocal_alignment_min"],
        }, note="The local/nonlocal index split is a diagnostic and must itself be resolution-tested."),
    ]
    gate_dicts = [g.to_dict() for g in gates]
    blocking = [g for g in gates if g.blocker]
    any_blocking_fail = any(g.status == "FAIL" for g in blocking)
    any_blocking_not_run = any(g.status == "NOT_RUN" for g in blocking)
    all_blocking_pass = bool(blocking) and all(g.status == "PASS" for g in blocking)
    if any_blocking_fail:
        scientific_verdict = "FALSIFIED_OR_UNRESOLVED_AT_ONE_OR_MORE_GATES"
    elif any_blocking_not_run:
        scientific_verdict = "INCOMPLETE_REQUIRED_GATES_NOT_RUN"
    else:
        scientific_verdict = "NOT_FALSIFIED_BY_CONFIGURED_GATES"

    summary = {
        "package": "SST_contact_billiard_hydrodynamic_falsifier",
        "version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "constants": SST_CONSTANTS,
        "settings": {
            "samples": samples,
            "hydro_samples": hydro_samples,
            "exclusion_fraction": exclusion_fraction,
            "core_ratios": core_ratios,
            "physical_thickness_m": physical_thickness_m,
            "skip_hydro": skip_hydro,
            "hydro_interactions": hydro_interactions,
            "local_band": local_band,
            "thresholds": thresholds_all,
        },
        "geometry": {
            "length": geom.length,
            "edge_ratio": geom.edge_ratio,
            "edge_cv": geom.edge_cv,
            "source_length_relative_error": source_length_relative_error,
            "source_diameter_relative_error": source_diameter_relative_error,
            "curvature": _finite_stats(geom.curvature),
            "torsion": _finite_stats(geom.torsion),
            **thickness,
        },
        "contact": {
            "completeness_fraction": contact.completeness_fraction,
            "inverse_residual_rms": contact.inverse_residual_rms,
            "orthogonality_rms": orth_rms,
            "branch_winding_a": contact.branch_winding_a,
            "branch_winding_b": contact.branch_winding_b,
        },
        "billiard": {
            **asdict(billiard),
            "orbit": billiard.orbit.tolist(),
            "paired_orbit_hausdorff": paired_orbit_hausdorff,
            "branch_a_closure_residual": billiard_a.closure_residual,
            "branch_b_closure_residual": billiard_b.closure_residual,
        },
        "geometric_force": {
            "compatibility_relative_l2": force.compatibility_relative_l2,
            "inverse_compatibility_relative_l2": force.inverse_compatibility_relative_l2,
            "local_balance_relative_l2": force.local_balance_relative_l2,
            "ill_conditioned_fraction": force.ill_conditioned_fraction,
        },
        "hydrodynamics": hydro_rows,
        "gates": gate_dicts,
        "all_executed_blocking_gates_pass": all_blocking_pass,
        "scientific_verdict": scientific_verdict,
        "non_claims": [
            "A PASS does not prove SST or identify an electron.",
            "The contact-map and 9-billiard are numerical unless independently converged.",
            "The regularized Rosenhead-type filament kernel is a finite-core proxy, not a resolved Euler core simulation.",
            "The local/nonlocal segment split is discretization-dependent and is used only as a falsification guard.",
            "The Hamiltonian gradient comparison tests shape with one global scale; the fitted tension and its constancy remain independent diagnostics.",
        ],
    }
    json_dump(out / "summary.json", summary)
    json_dump(out / "gates.json", {"gates": gate_dicts, "all_executed_blocking_gates_pass": all_blocking_pass})
    json_dump(out / "manifest.json", {
        "package_version": __version__,
        "python": sys.version,
        "platform": platform.platform(),
        "source": source,
        "outputs": [str(p.relative_to(out)) for p in sorted(out.rglob("*")) if p.is_file()],
    })
    return summary


def convergence_campaign(
    raw_points: np.ndarray,
    out: Path,
    *,
    source: dict[str, Any],
    resolutions: list[int],
    exclusion_fraction: float = 0.03,
) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for n in resolutions:
        p = resample_closed_curve(raw_points, n)
        geom = compute_geometry(p)
        thick = sampled_thickness_proxy(geom, exclusion_fraction)
        contact = extract_contact_map(geom, exclusion_fraction)
        a = PeriodicLiftMap(contact.s, contact.branch_a_lift, contact.branch_winding_a)
        b = PeriodicLiftMap(contact.s, contact.branch_b_lift, contact.branch_winding_b)
        ba = scan_billiard(a, 9, grid=max(1024, 8 * n), branch_name="a")
        bb = scan_billiard(b, 9, grid=max(1024, 8 * n), branch_name="b")
        bill = ba if ba.closure_residual <= bb.closure_residual else bb
        orbit_distances = circular_distance(ba.orbit[:, None], bb.orbit[None, :])
        paired_hausdorff = float(max(
            np.max(np.min(orbit_distances, axis=1)),
            np.max(np.min(orbit_distances, axis=0)),
        ))
        rows.append({
            "samples": n,
            "length": geom.length,
            "edge_ratio": geom.edge_ratio,
            "thickness_proxy": thick["thickness_proxy"],
            "ropelength_diameter_proxy": thick["ropelength_diameter_proxy"],
            "contact_completeness": contact.completeness_fraction,
            "contact_inverse_rms": contact.inverse_residual_rms,
            "billiard_selected_branch": bill.map_branch,
            "billiard_selected_seed": bill.seed,
            "billiard_a_closure": ba.closure_residual,
            "billiard_b_closure": bb.closure_residual,
            "billiard_a_lower_period_min": ba.min_lower_period_residual,
            "billiard_b_lower_period_min": bb.min_lower_period_residual,
            "billiard_paired_orbit_hausdorff": paired_hausdorff,
        })
    csv_dump(out / "convergence.csv", rows)
    verdict = {
        "source": source,
        "resolutions": resolutions,
        "rows": rows,
        "note": "Convergence is evidence only when the final three resolutions stabilize; no extrapolation is silently imposed.",
    }
    json_dump(out / "convergence.json", verdict)
    return verdict
