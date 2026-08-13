from __future__ import annotations
import numpy as np
from .fourier import sample_component
from .geometry import component_geometry, aggregate_geometry, sst_scale_lift
from .topology import topology_summary
from .contacts import contact_summary
from .biot_savart import analyze_sign_configurations
from .symmetry import mirror_icp_score, inertia_symmetry
from .models import IdealLink
from .native_ext import BackendOptions


def _resample(link: IdealLink, n: int):
    return [sample_component(component, n) for component in link.components]


def convergence_audit(link, ns, backend_options, compute_linking=True, curvature_refine_peaks=16):
    out = []
    for n in ns:
        samples = _resample(link, n)
        geos = [component_geometry(sample, curvature_refine_peaks) for sample in samples]
        row = {
            "n": n,
            "total_length_D": float(sum(g["numerical_length_D"] for g in geos)),
            "sampled_max_curvature_Dinv": float(max(g["sampled_curvature_max_Dinv"] for g in geos)),
            "refined_max_curvature_Dinv": float(max(g["refined_curvature_max_Dinv"] for g in geos)),
            "max_curvature_Dinv": float(max(g["refined_curvature_max_Dinv"] for g in geos)),
            "max_length_relative_error": float(max(abs(g["length_relative_error"]) for g in geos)),
        }
        if compute_linking:
            topo = topology_summary([sample.r for sample in samples], False, 256, backend_options)
            row["linking_backend"] = topo["backend"]
            row["max_linking_integer_error"] = topo["max_linking_integer_error"]
        out.append(row)
    return out


def invariance_audit(link, backend_options, n=256):
    samples = _resample(link, n)
    base_summary = topology_summary([sample.r for sample in samples], False, 256, backend_options)
    base = np.asarray(base_summary["linking_matrix"])
    rng = np.random.default_rng(20260804)
    matrix = rng.normal(size=(3, 3))
    rotation, _ = np.linalg.qr(matrix)
    if np.linalg.det(rotation) < 0:
        rotation[:, -1] *= -1
    shift = np.array([0.37, -0.21, 0.11])
    transformed = [(sample.r @ rotation.T) + shift for sample in samples]
    rotated = np.asarray(topology_summary(transformed, False, 256, backend_options)["linking_matrix"])
    mirrored_curves = [sample.r * np.array([-1, 1, 1]) for sample in samples]
    mirrored = np.asarray(topology_summary(mirrored_curves, False, 256, backend_options)["linking_matrix"])
    reversed_curves = [sample.r[::-1].copy() for sample in samples]
    reversed_matrix = np.asarray(topology_summary(reversed_curves, False, 256, backend_options)["linking_matrix"])
    return {
        "backend": base_summary["backend"],
        "rigid_transform_max_abs_error": float(np.max(np.abs(rotated-base))),
        "mirror_sign_flip_max_abs_error": float(np.max(np.abs(mirrored+base))),
        "reverse_all_components_max_abs_error": float(np.max(np.abs(reversed_matrix-base))),
    }


def _epsilon_diagnostics(rows: list[dict], comparison_epsilon: float) -> dict:
    if not rows:
        return {}
    eps_values = sorted({float(row["epsilon_D"]) for row in rows})
    fixed = [row for row in rows if np.isclose(row["epsilon_D"], comparison_epsilon, rtol=0, atol=1e-12)]
    if not fixed:
        raise ValueError(
            f"comparison_epsilon_D={comparison_epsilon} must be one of epsilons_D={eps_values}"
        )
    fixed_best = min(fixed, key=lambda row: row["relative_equilibrium_score"])
    global_best = min(rows, key=lambda row: row["relative_equilibrium_score"])
    sector_groups = {}
    for row in rows:
        key = tuple(row["signs"])
        sector_groups.setdefault(key, []).append(row)
    extrapolations = []
    for signs, group in sector_groups.items():
        group = sorted(group, key=lambda row: row["epsilon_D"])
        if len(group) < 3:
            continue
        x = np.asarray([row["epsilon_D"]**2 for row in group], dtype=float)
        y = np.asarray([row["relative_equilibrium_score"] for row in group], dtype=float)
        coeff = np.polyfit(x, y, 1)
        fitted = coeff[0]*x + coeff[1]
        ss_res = float(np.sum((y-fitted)**2))
        ss_tot = float(np.sum((y-y.mean())**2))
        extrapolations.append({
            "signs": list(signs),
            "intercept_epsilon0": float(coeff[1]),
            "slope_per_epsilon2": float(coeff[0]),
            "r2": float(1-ss_res/max(ss_tot, 1e-300)),
        })
    extrapolated_best = min(extrapolations, key=lambda row: row["intercept_epsilon0"], default=None)
    fixed_signs = tuple(fixed_best["signs"])
    fixed_sector_curve = sorted(
        (row for row in rows if tuple(row["signs"]) == fixed_signs),
        key=lambda row: row["epsilon_D"],
    )
    monotone_decreasing = all(
        b["relative_equilibrium_score"] <= a["relative_equilibrium_score"] + 1e-14
        for a, b in zip(fixed_sector_curve, fixed_sector_curve[1:])
    )
    return {
        "comparison_epsilon_D": float(comparison_epsilon),
        "fixed_epsilon_best_score": float(fixed_best["relative_equilibrium_score"]),
        "fixed_epsilon_best_signs": list(fixed_best["signs"]),
        "fixed_epsilon_best_circulation_class": fixed_best["circulation_class"],
        "legacy_min_over_epsilon_score": float(global_best["relative_equilibrium_score"]),
        "legacy_min_over_epsilon_D": float(global_best["epsilon_D"]),
        "legacy_min_over_epsilon_signs": list(global_best["signs"]),
        "global_min_at_largest_epsilon": bool(np.isclose(global_best["epsilon_D"], max(eps_values))),
        "fixed_sector_score_monotone_decreasing_with_epsilon": bool(monotone_decreasing),
        "epsilon0_extrapolations": extrapolations,
        "epsilon0_extrapolated_best": extrapolated_best,
        "status": (
            "The fixed-epsilon score is the primary comparative quantity. The minimum over "
            "epsilon is retained only as a smoothing-sensitivity diagnostic."
        ),
    }


def analyze_link(link, cfg, backend_options, backend_metadata, run_signature):
    n = int(cfg["sample_n"])
    peak_count = int(cfg.get("curvature_refine_peaks", 16))
    samples = _resample(link, n)
    component_results = [component_geometry(sample, peak_count) for sample in samples]
    aggregate = aggregate_geometry(component_results, link.diameter)

    topo_samples = _resample(link, int(cfg.get("topology_n", n)))
    topo = topology_summary(
        [sample.r for sample in topo_samples], bool(cfg.get("compute_writhe", True)),
        int(cfg.get("chunk", 256)), backend_options,
    )
    contact_samples = _resample(link, int(cfg.get("contact_n", n)))
    contacts = contact_summary(
        contact_samples, link.diameter, float(cfg.get("contact_tolerance", 0.01)),
        int(cfg.get("contact_patch_adjacency", 2)),
    )
    symmetry_samples = _resample(link, int(cfg.get("symmetry_n", min(n, 512))))
    result = {
        "suite_version": "0.2.1",
        "run_signature": run_signature,
        "link_id": link.link_id,
        "conway": link.conway,
        "diameter_D": link.diameter,
        "backend": backend_metadata,
        "geometry": {"components": component_results, "aggregate": aggregate},
        "topology": topo,
        "contacts": contacts,
        "symmetry": {
            **mirror_icp_score([sample.r for sample in symmetry_samples]),
            **inertia_symmetry([sample.r for sample in symmetry_samples]),
        },
        "convergence": convergence_audit(
            link, list(cfg.get("convergence_n", [128, 256])), backend_options,
            curvature_refine_peaks=peak_count,
        ),
        "invariances": invariance_audit(link, backend_options, min(256, n)),
        "sst_scale": sst_scale_lift(aggregate, component_results, cfg.get("sst_mapping", {})),
    }
    if cfg.get("biot_savart", True):
        bs_samples = _resample(link, int(cfg.get("bs_n", min(n, 256))))
        rows, diagnostics = analyze_sign_configurations(
            bs_samples, [float(value) for value in cfg.get("epsilons_D", [0.1])],
            backend_options, linking_matrix=np.asarray(topo["linking_matrix"]),
            local_skip_velocity=int(cfg.get("local_skip_velocity", 3)),
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
        )
        result["biot_savart"] = rows
        result["biot_savart_diagnostics"] = diagnostics
        result["epsilon_comparison"] = _epsilon_diagnostics(
            rows, float(cfg.get("comparison_epsilon_D", 0.1))
        )
    else:
        result["biot_savart"] = []
        result["biot_savart_diagnostics"] = {}
        result["epsilon_comparison"] = {}

    upper = np.triu_indices(len(link.components), 1)
    linking = np.asarray(topo["linking_matrix"])
    refined_min = min((pair["refined_min_distance_D"] for pair in contacts["mutual_pairs"]), default=float("nan"))
    epsdiag = result["epsilon_comparison"]
    cmap = contacts["contact_map"]
    result["features"] = {
        "crossings": int(link.link_id[1:].split("a")[0].split("n")[0]),
        "components": len(link.components),
        "total_length_D": aggregate["numerical_total_length_D"],
        "standard_ropelength": aggregate["standard_total_ropelength_radius"],
        "length_imbalance_cv": aggregate["length_imbalance_cv"],
        "max_curvature_Dinv": aggregate["max_curvature_Dinv"],
        "sampled_max_curvature_Dinv": aggregate["max_sampled_curvature_Dinv"],
        "curvature_refinement_gain": aggregate["max_curvature_refinement_gain_fraction"],
        "bending_integral": aggregate["total_bending_integral_Dinv"],
        "spectral_entropy": aggregate["mean_spectral_entropy"],
        "spectral_tail": aggregate["max_spectral_tail_fraction"],
        "total_abs_linking": float(np.sum(np.abs(linking[upper]))),
        "signed_linking": float(np.sum(linking[upper])),
        "linking_integer_error": topo["max_linking_integer_error"],
        "refined_mutual_min_D": refined_min,
        "contact_edges": contacts["graph"]["contact_edge_count"],
        "raw_contact_cycle_rank": contacts["graph"]["raw_contact_graph_cycle_rank"],
        "contact_cycle_rank": cmap["augmented_contact_graph_cycle_rank"],
        "contact_patch_count": cmap["patch_count"],
        "continuous_contact_patch_count": cmap["continuous_contact_patch_count"],
        "contact_map_closed_orbits": cmap["total_closed_orbit_count"],
        "contact_map_period9_candidates": cmap["candidate_period_9_count"],
        "mirror_proxy": result["symmetry"]["mirror_icp_chamfer_normalized"],
        "comparison_epsilon_D": epsdiag.get("comparison_epsilon_D", float("nan")),
        "fixed_core_relative_equilibrium_score": epsdiag.get("fixed_epsilon_best_score", float("nan")),
        "fixed_core_best_signs": "".join("+" if x > 0 else "-" for x in epsdiag.get("fixed_epsilon_best_signs", [])),
        # Legacy diagnostic retained for compatibility; not the primary rank in v0.2.1.
        "best_relative_equilibrium_score": epsdiag.get("legacy_min_over_epsilon_score", float("nan")),
        "best_epsilon_D": epsdiag.get("legacy_min_over_epsilon_D", float("nan")),
        "min_at_largest_epsilon": epsdiag.get("global_min_at_largest_epsilon", False),
        "epsilon0_extrapolated_score": (
            epsdiag.get("epsilon0_extrapolated_best", {}) or {}
        ).get("intercept_epsilon0", float("nan")),
    }
    return result
