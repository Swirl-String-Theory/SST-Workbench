from __future__ import annotations
import numpy as np
from .fourier import sample_component
from .geometry import component_geometry, aggregate_geometry, sst_scale_lift
from .gates import thickness_gate, curvature_mode_convergence
from .topology import topology_summary
from .contacts import contact_summary
from .biot_savart import analyze_sign_configurations
from .symmetry import mirror_icp_score, inertia_symmetry
from .models import IdealLink
from .native_ext import BackendOptions


def _resample(link: IdealLink, n: int):
    return [sample_component(component, n) for component in link.components]


def convergence_audit(
    link: IdealLink,
    ns: list[int],
    backend_options: BackendOptions,
    compute_linking: bool = True,
) -> list[dict]:
    out = []
    for n in ns:
        samples = _resample(link, n)
        geos = [component_geometry(sample, link.diameter) for sample in samples]
        row = {
            "n": n,
            "total_length_D": float(sum(g["numerical_length_D"] for g in geos)),
            "max_curvature_Dinv": float(max(g["curvature_max_Dinv"] for g in geos)),
            "max_length_relative_error": float(max(abs(g["length_relative_error"]) for g in geos)),
        }
        if compute_linking:
            topo = topology_summary(
                [sample.r for sample in samples], False, 256, backend_options
            )
            row["linking_backend"] = topo["backend"]
            row["max_linking_integer_error"] = topo["max_linking_integer_error"]
        out.append(row)
    return out


def invariance_audit(
    link: IdealLink,
    backend_options: BackendOptions,
    n: int = 256,
) -> dict:
    samples = _resample(link, n)
    base_summary = topology_summary(
        [sample.r for sample in samples], False, 256, backend_options
    )
    base = np.asarray(base_summary["linking_matrix"])
    rng = np.random.default_rng(20260804)
    matrix = rng.normal(size=(3, 3))
    rotation, _ = np.linalg.qr(matrix)
    if np.linalg.det(rotation) < 0:
        rotation[:, -1] *= -1
    shift = np.array([0.37, -0.21, 0.11])
    transformed = [(sample.r @ rotation.T) + shift for sample in samples]
    rotated = np.asarray(topology_summary(
        transformed, False, 256, backend_options
    )["linking_matrix"])
    mirrored_curves = [sample.r * np.array([-1, 1, 1]) for sample in samples]
    mirrored = np.asarray(topology_summary(
        mirrored_curves, False, 256, backend_options
    )["linking_matrix"])
    reversed_curves = [sample.r[::-1].copy() for sample in samples]
    reversed_matrix = np.asarray(topology_summary(
        reversed_curves, False, 256, backend_options
    )["linking_matrix"])
    return {
        "backend": base_summary["backend"],
        "rigid_transform_max_abs_error": float(np.max(np.abs(rotated-base))),
        "mirror_sign_flip_max_abs_error": float(np.max(np.abs(mirrored+base))),
        "reverse_all_components_max_abs_error": float(np.max(np.abs(reversed_matrix-base))),
    }


def analyze_link(
    link: IdealLink,
    cfg: dict,
    backend_options: BackendOptions,
    backend_metadata: dict,
    run_signature: str,
) -> dict:
    n = int(cfg["sample_n"])
    samples = _resample(link, n)
    component_results = [component_geometry(sample, link.diameter) for sample in samples]
    aggregate = aggregate_geometry(component_results, link.diameter)

    topo_samples = _resample(link, int(cfg.get("topology_n", n)))
    topo = topology_summary(
        [sample.r for sample in topo_samples],
        bool(cfg.get("compute_writhe", True)),
        int(cfg.get("chunk", 256)),
        backend_options,
    )

    contact_samples = _resample(link, int(cfg.get("contact_n", n)))
    contacts = contact_summary(
        contact_samples,
        link.diameter,
        float(cfg.get("contact_tolerance", 0.01)),
        self_exclusion_D=float(cfg.get("self_exclusion_D", 2.0)),
        neighbour_cap=int(cfg.get("self_neighbour_cap", 256)),
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
            link,
            list(cfg.get("convergence_n", [128, 256])),
            backend_options,
        ),
        "invariances": invariance_audit(link, backend_options, min(256, n)),
        "sst_scale": sst_scale_lift(
            aggregate, component_results, cfg.get("sst_mapping", {})
        ),
        "thickness_gate": thickness_gate(
            component_results, contacts, link.diameter,
            float(cfg.get("thickness_tolerance", 1e-3)),
        ),
        "curvature_mode_convergence": curvature_mode_convergence(
            link,
            tuple(cfg.get("curvature_cutoffs", (12, 20, 30, 50, 100))),
            int(cfg.get("curvature_convergence_n", 4096)),
        ) if cfg.get("curvature_convergence", True) else {},
    }
    if cfg.get("biot_savart", True):
        bs_samples = _resample(link, int(cfg.get("bs_n", min(n, 256))))
        rows, diagnostics = analyze_sign_configurations(
            bs_samples,
            [float(value) for value in cfg.get("epsilons_D", [0.1])],
            backend_options,
            linking_matrix=np.asarray(topo["linking_matrix"]),
            local_skip_velocity=int(cfg.get("local_skip_velocity", 3)),
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
        )
        result["biot_savart"] = rows
        result["biot_savart_diagnostics"] = diagnostics
    else:
        result["biot_savart"] = []
        result["biot_savart_diagnostics"] = {}

    upper = np.triu_indices(len(link.components), 1)
    linking = np.asarray(topo["linking_matrix"])
    refined_min = min(
        (pair["refined_min_distance_D"] for pair in contacts["mutual_pairs"]),
        default=float("nan"),
    )
    bs_best = min(
        (row["relative_equilibrium_score"] for row in result["biot_savart"]),
        default=float("nan"),
    )
    result["features"] = {
        "crossings": int(link.link_id[1:].split("a")[0].split("n")[0]),
        "components": len(link.components),
        "total_length_D": aggregate["numerical_total_length_D"],
        "standard_ropelength": aggregate["standard_total_ropelength_radius"],
        "length_imbalance_cv": aggregate["length_imbalance_cv"],
        "max_curvature_Dinv": aggregate["max_curvature_Dinv"],
        "bending_integral": aggregate["total_bending_integral_Dinv"],
        "spectral_entropy": aggregate["mean_spectral_entropy"],
        "spectral_tail": aggregate["max_spectral_tail_fraction"],
        "total_abs_linking": float(np.sum(np.abs(linking[upper]))),
        "signed_linking": float(np.sum(linking[upper])),
        "linking_integer_error": topo["max_linking_integer_error"],
        "refined_mutual_min_D": refined_min,
        "contact_edges": contacts["graph"]["contact_edge_count"],
        "contact_cycle_rank": contacts["graph"]["contact_graph_cycle_rank"],
        "mirror_proxy": result["symmetry"]["mirror_icp_chamfer_normalized"],
        "best_relative_equilibrium_score": bs_best,
        "thickness_gate_passes": result["thickness_gate"]["passes"],
        "allowed_diameter_D": result["thickness_gate"]["allowed_diameter_D"],
        "binding_constraint": result["thickness_gate"]["binding_constraint"],
        "curvature_spectral_tail": result["thickness_gate"]["curvature_spectral_tail_fraction"],
        "largest_converged_cutoff": (
            result["curvature_mode_convergence"].get("largest_cutoff_within_bound")
            if result.get("curvature_mode_convergence") else None
        ),
    }
    return result
