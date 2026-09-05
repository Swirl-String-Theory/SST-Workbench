from __future__ import annotations
import numpy as np
from .fourier import sample_component
from .geometry import component_geometry, aggregate_geometry, sst_scale_lift
from .topology import topology_summary
from .contacts import contact_summary
from .biot_savart import analyze_sign_configurations
from .symmetry import mirror_icp_score, inertia_symmetry
from .models import IdealLink

def _resample(link: IdealLink, n: int):
    return [sample_component(c, n) for c in link.components]

def convergence_audit(link: IdealLink, ns: list[int], compute_linking: bool = True) -> list[dict]:
    out = []
    for n in ns:
        samples = _resample(link, n)
        geos = [component_geometry(s) for s in samples]
        row = {
            "n": n,
            "total_length_D": float(sum(g["numerical_length_D"] for g in geos)),
            "max_curvature_Dinv": float(max(g["curvature_max_Dinv"] for g in geos)),
            "max_length_relative_error": float(max(abs(g["length_relative_error"]) for g in geos)),
        }
        if compute_linking:
            topo = topology_summary([s.r for s in samples], False, 256)
            row["max_linking_integer_error"] = topo["max_linking_integer_error"]
        out.append(row)
    return out

def invariance_audit(link: IdealLink, n: int = 256) -> dict:
    samples = _resample(link, n)
    base = topology_summary([s.r for s in samples], False, 256)["linking_matrix"]
    rng = np.random.default_rng(20260804)
    M = rng.normal(size=(3,3))
    Q, _ = np.linalg.qr(M)
    if np.linalg.det(Q) < 0:
        Q[:, -1] *= -1
    shift = np.array([0.37, -0.21, 0.11])
    transformed = [(s.r @ Q.T) + shift for s in samples]
    rot = topology_summary(transformed, False, 256)["linking_matrix"]
    mirrored = [s.r * np.array([-1,1,1]) for s in samples]
    mir = topology_summary(mirrored, False, 256)["linking_matrix"]
    reversed_curves = [s.r[::-1].copy() for s in samples]
    rev = topology_summary(reversed_curves, False, 256)["linking_matrix"]
    return {
        "rigid_transform_max_abs_error": float(np.max(np.abs(rot-base))),
        "mirror_sign_flip_max_abs_error": float(np.max(np.abs(mir+base))),
        "reverse_all_components_max_abs_error": float(np.max(np.abs(rev-base))),
    }

def analyze_link(link: IdealLink, cfg: dict) -> dict:
    n = int(cfg["sample_n"])
    samples = _resample(link, n)
    component_results = [component_geometry(s) for s in samples]
    aggregate = aggregate_geometry(component_results, link.diameter)
    topo_samples = _resample(link, int(cfg.get("topology_n", n)))
    topo = topology_summary(
        [s.r for s in topo_samples],
        bool(cfg.get("compute_writhe", True)),
        int(cfg.get("chunk", 256)),
    )
    contact_samples = _resample(link, int(cfg.get("contact_n", n)))
    contacts = contact_summary(
        contact_samples, link.diameter, float(cfg.get("contact_tolerance", 0.01))
    )
    symmetry_samples = _resample(link, int(cfg.get("symmetry_n", min(n, 512))))
    result = {
        "link_id": link.link_id,
        "conway": link.conway,
        "diameter_D": link.diameter,
        "geometry": {"components": component_results, "aggregate": aggregate},
        "topology": topo,
        "contacts": contacts,
        "symmetry": {
            **mirror_icp_score([s.r for s in symmetry_samples]),
            **inertia_symmetry([s.r for s in symmetry_samples]),
        },
        "convergence": convergence_audit(link, list(cfg.get("convergence_n", [128,256]))),
        "invariances": invariance_audit(link, min(256, n)),
        "sst_scale": sst_scale_lift(aggregate, component_results, cfg.get("sst_mapping", {})),
    }
    if cfg.get("biot_savart", True):
        bs_samples = _resample(link, int(cfg.get("bs_n", min(n, 256))))
        result["biot_savart"] = analyze_sign_configurations(
            bs_samples, [float(x) for x in cfg.get("epsilons_D", [0.1])]
        )
    else:
        result["biot_savart"] = []
    # Compact cross-link features used by ranking/PCA.
    upper = np.triu_indices(len(link.components), 1)
    lk = np.asarray(topo["linking_matrix"])
    refined_min = min(
        (p["refined_min_distance_D"] for p in contacts["mutual_pairs"]),
        default=float("nan"),
    )
    bs_best = min(
        (x["relative_equilibrium_score"] for x in result["biot_savart"]),
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
        "total_abs_linking": float(np.sum(np.abs(lk[upper]))),
        "signed_linking": float(np.sum(lk[upper])),
        "linking_integer_error": topo["max_linking_integer_error"],
        "refined_mutual_min_D": refined_min,
        "contact_edges": contacts["graph"]["contact_edge_count"],
        "contact_cycle_rank": contacts["graph"]["contact_graph_cycle_rank"],
        "mirror_proxy": result["symmetry"]["mirror_icp_chamfer_normalized"],
        "best_relative_equilibrium_score": bs_best,
    }
    return result
