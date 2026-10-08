from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import os
import numpy as np

from sst_falsifier.backend_contract import parity_gate, require_backend
from sst_falsifier.backends import cpp_pybind
from sst_falsifier.blind import opaque_id
from sst_falsifier.source_registry import workbench_root
from sst_falsifier.util import write_json

from .io import sha256_file
from .geometry import resample_closed, thickness_proxy, geom_stats, closure_edge_ratio
from .metrics import (
    total_velocity, total_energy_length, relative_equilibrium,
    orientation_symmetry, mirror_symmetry, holonomy_metrics,
    exterior_differential_metrics, energy_partition, far_field_decay,
    biot_savart,
)
from .population import cauchy_population_control
from .pklsa import PKLSACarrier, discover_qualified_carriers, load_pklsa_geometry, stratified_limit
from .cross_source import evaluate_cross_source_consistency


def _mode_params(cfg: dict[str, Any], mode: str) -> dict[str, Any]:
    e = cfg["experiment"]
    m = mode.upper()
    if m == "BASIC":
        return {"max_files": int(e["max_files_basic"]), "n": int(e["resample_n_basic"]), "n2": int(e["convergence_n_basic"])}
    if m == "CERTIFY":
        return {"max_files": int(e["max_files_certify"]), "n": int(e["resample_n_certify"]), "n2": int(e["convergence_n_certify"])}
    return {"max_files": int(e["max_files_full"]), "n": int(e["resample_n_full"]), "n2": int(e["convergence_n_full"])}


def _synthetic_circle(n: int = 192) -> np.ndarray:
    a = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return np.column_stack([np.cos(a), np.sin(a), np.zeros_like(a)])


def _reference_controls() -> dict[str, Any]:
    p = _synthetic_circle(192)
    q = np.array([[0.0, 0.0, 2.0], [0.25, -0.1, 1.7], [2.0, 0.0, 0.5]], dtype=float)
    v = biot_savart(p, q, gamma=1.0, core=0.05)
    finite = bool(np.isfinite(v).all())
    rev = biot_savart(p[::-1].copy(), q, gamma=1.0, core=0.05)
    reversal = float(np.linalg.norm(v + rev) / max(float(np.linalg.norm(v)), 1e-300))
    e = total_energy_length([p], 0.05)
    return {
        "finite_velocity": finite,
        "orientation_reversal_relative_l2": reversal,
        "energy_length": float(e),
        "energy_positive": bool(np.isfinite(e) and e > 0.0),
        "pass": bool(finite and reversal <= 1e-12 and np.isfinite(e) and e > 0.0),
    }


def _compute_sample(carrier: PKLSACarrier, cfg: dict[str, Any], mode: str, key: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    e = cfg["experiment"]
    t = cfg["thresholds"]
    mp = _mode_params(cfg, mode)
    raw = load_pklsa_geometry(carrier.source_path)
    n, n2 = mp["n"], mp["n2"]
    comps = [resample_closed(p, n) for p in raw]
    comps2 = [resample_closed(p, n2) for p in raw]

    gs, L = geom_stats(comps)
    closure = [closure_edge_ratio(p) for p in raw]
    tp = thickness_proxy(comps2)
    thickness = float(tp["thickness_proxy"])
    edge_mean = float(np.mean([g["edge_mean"] for g in gs]))
    core = float(e["core_radius_scale"]) * thickness
    if not np.isfinite(core) or core <= 0:
        raise ValueError("non-positive finite-core radius proxy")

    v = total_velocity(comps, None, core)
    req = relative_equilibrium(comps, v)
    energy = total_energy_length(comps, core)
    v2 = total_velocity(comps2, None, core)
    req2 = relative_equilibrium(comps2, v2)
    energy2 = total_energy_length(comps2, core)
    conv = {
        "energy_rel_diff": float(abs(energy2 - energy) / max(abs(energy2), 1e-300)),
        "re_abs_diff": float(abs(req2["normal_nrmse"] - req["normal_nrmse"])),
        "energy_length_low": float(energy),
        "energy_length_high": float(energy2),
        "re_low": float(req["normal_nrmse"]),
        "re_high": float(req2["normal_nrmse"]),
    }

    nh = max(int(e["holonomy_source_factor"]) * n, 384)
    comph = [resample_closed(p, nh) for p in raw]
    hol = holonomy_metrics(
        comph, thickness,
        int(e["holonomy_stations_per_component"]),
        int(e["holonomy_loop_points"]),
        float(e["holonomy_loop_radius_as_thickness"]),
    )
    valid_hol = [r for r in hol if abs(int(r["nearest_integer"])) >= 1]
    hol_err = max([float(r["integer_abs_error"]) for r in valid_hol], default=float("inf"))

    sym = {
        "orientation_relative_error": orientation_symmetry(comps, core),
        "mirror_relative_error": mirror_symmetry(comps, core),
    }

    ext = exterior_differential_metrics(
        comph,
        float(e["exterior_radius_factor"]),
        int(e["exterior_directions"]),
        float(e["exterior_fd_fraction"]),
    )
    ep_lo = energy_partition(
        comps, core, int(e["energy_samples_low"]),
        float(e["energy_domain_radius_factor"]),
        float(e["source_zone_core_multiples"]),
    )
    ep_hi = energy_partition(
        comps, core, int(e["energy_samples_high"]),
        float(e["energy_domain_radius_factor"]),
        float(e["source_zone_core_multiples"]),
    )
    ep_refine = abs(float(ep_hi["exterior_energy_fraction"]) - float(ep_lo["exterior_energy_fraction"]))
    ff = far_field_decay(comph, list(e["far_field_radius_factors"]), int(e["far_field_directions"]))

    statuses = {
        "H0": bool(
            min(int(g["n_vertices"]) for g in gs) >= int(t["geometry_min_vertices"])
            and max(closure) <= float(t["geometry_closure_edge_ratio_max"])
            and np.isfinite(thickness)
            and thickness / max(edge_mean, 1e-300) >= float(t["geometry_min_thickness_over_edge"])
        ),
        "H1": bool(
            conv["energy_rel_diff"] <= float(t["convergence_energy_rel_diff_max"])
            and conv["re_abs_diff"] <= float(t["convergence_re_abs_diff_max"])
        ),
        "H2": bool(
            len(valid_hol) >= int(t["holonomy_min_valid_loops"])
            and hol_err <= float(t["holonomy_integer_abs_error_max"])
        ),
        "H3": bool(req["normal_nrmse"] <= float(t["relative_equilibrium_normal_nrmse_max"])),
        "H4": bool(
            sym["orientation_relative_error"] <= float(t["symmetry_orientation_relative_error_max"])
            and sym["mirror_relative_error"] <= float(t["symmetry_mirror_relative_error_max"])
        ),
        "P3": bool(
            ext["n_valid"] >= int(t["exterior_min_valid_points"])
            and ext["median_speed"] > 0.0
            and ext["max_div_dimensionless"] <= float(t["exterior_div_dimensionless_max"])
            and ext["max_curl_dimensionless"] <= float(t["exterior_curl_dimensionless_max"])
        ),
        "P4": bool(
            len(valid_hol) >= int(t["holonomy_min_valid_loops"])
            and hol_err <= float(t["holonomy_integer_abs_error_max"])
            and ext["median_speed"] > 0.0
        ),
        "P5": bool(
            ep_hi["exterior_energy_fraction"] >= float(t["exterior_energy_fraction_min"])
            and ep_refine <= float(t["exterior_energy_fraction_refinement_abs_max"])
        ),
        "P6": bool(
            ff.get("eligible", False)
            and ff.get("fit_r2", -np.inf) >= float(t["far_field_fit_r2_min"])
            and float(t["far_field_exponent_min"]) <= ff.get("velocity_decay_exponent", np.inf) <= float(t["far_field_exponent_max"])
        ) if ff.get("eligible", False) else None,
    }

    identity_material = f"{carrier.geometry_sha256}:{carrier.carrier_id}"
    bid = opaque_id(identity_material, key, 16)
    topology_group_id = opaque_id("topology:" + carrier.topology_id, key, 16)
    source_family_group_id = opaque_id("source-family:" + carrier.source_family, key, 16)
    provenance_family_group_id = opaque_id("provenance-family:" + carrier.provenance_family, key, 16)
    provider_group_id = opaque_id("provider-group:" + carrier.provider_group, key, 16)
    independence_group_id = opaque_id("independence-group:" + carrier.independence_group, key, 16)
    public = {
        "blind_id": bid,
        "topology_group_id": topology_group_id,
        "source_family_group_id": source_family_group_id,
        "provenance_family_group_id": provenance_family_group_id,
        "provider_group_id": provider_group_id,
        "independence_group_id": independence_group_id,
        "source_generated": bool(carrier.generated),
        "n_components": len(comps),
        "length_reference": float(L),
        "core_radius_reference": core,
        "thickness": tp,
        "closure_edge_ratios": [float(x) for x in closure],
        "convergence": conv,
        "holonomy": hol,
        "relative_equilibrium": req,
        "symmetry": sym,
        "exterior_differential": ext,
        "energy_partition_low": ep_lo,
        "energy_partition_high": ep_hi,
        "energy_partition_refinement_abs": float(ep_refine),
        "far_field": ff,
        "sample_gate_pass": statuses,
    }
    private = {
        "blind_id": bid,
        "topology_group_id": topology_group_id,
        "source_family_group_id": source_family_group_id,
        "provider_group_id": provider_group_id,
        "topology_id": carrier.topology_id,
        "carrier_id": carrier.carrier_id,
        "source_family": carrier.source_family,
        "provenance_family": carrier.provenance_family,
        "provider_group": carrier.provider_group,
        "independence_group": carrier.independence_group,
        "source_role": carrier.source_role,
        "source_generated": bool(carrier.generated),
        "representation": carrier.representation,
        "source_path": str(carrier.source_path),
        "descriptor_path": str(carrier.descriptor_path),
        "qualification_summary_path": str(carrier.qualification_summary_path),
        "geometry_sha256": carrier.geometry_sha256,
        "source_file_sha256": carrier.source_file_sha256,
    }
    return public, private


def _aggregate(samples: list[dict[str, Any]], errors: list[dict[str, Any]], gid: str) -> tuple[str, dict[str, Any], str]:
    vals = [s["sample_gate_pass"].get(gid) for s in samples]
    eligible = [v for v in vals if v is not None]
    passes = sum(v is True for v in eligible)
    fails = sum(v is False for v in eligible)
    metrics = {"n_samples": len(samples), "n_eligible": len(eligible), "n_pass": passes, "n_fail": fails, "n_errors": len(errors)}
    if errors:
        return "FAIL", metrics, "One or more inputs could not be evaluated; later independent gates were still attempted on completed inputs."
    if not eligible:
        return "UNRESOLVED", metrics, "No eligible input existed for this gate."
    status = "PASS" if fails == 0 else "FAIL"
    return status, metrics, "Aggregate FAIL means at least one eligible sample failed; inspect BLIND_SAMPLE_METRICS.json for per-input classifications."


def _cpp_parity(root: Path, cfg: dict[str, Any]) -> tuple[str, dict[str, Any], str, dict[str, Any]]:
    p = _synthetic_circle(256)
    q = np.vstack([_synthetic_circle(80) * 1.7, np.array([[0.0, 0.0, 2.2]])])
    ref = biot_savart(p, q, gamma=1.0, core=0.07)
    try:
        cand, result = cpp_pybind.biot_savart(root, p, q, gamma=1.0, core=0.07, force_build=False, require=True)
        require_backend(
            result,
            accepted_actual=cfg["backends"]["cpp"]["accepted_actual"],
            authority="CERTIFICATION",
            precision="float64",
        )
        pg = parity_gate(cand, ref, float(cfg["thresholds"]["cpp_python_relative_l2_max"]))
        status = "PASS" if pg["pass"] else "FAIL"
        return status, pg, "Strict C++ FP64 certification; no Python fallback can satisfy B0.", result.to_dict()
    except Exception as ex:
        return "FAIL", {"error_type": type(ex).__name__, "error": str(ex)}, "C++ certification backend unavailable or outside tolerance; scientific Python gates remain interpretable.", {"error": str(ex)}


def run_scientific_pipeline(root: Path, cfg: dict[str, Any], ledger, mode: str) -> dict[str, Any]:
    out = root / f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    out.mkdir(parents=True, exist_ok=True)
    (out / "private").mkdir(exist_ok=True)

    ledger.record("G0", "PASS", metrics={"mode": mode, "framework_version": cfg["framework"]["version"]}, reason="Framework verified the frozen protocol before pipeline entry.")

    carriers: list[PKLSACarrier] = []
    source_meta: dict[str, Any] = {}
    source_discovery_error: str | None = None
    try:
        carriers, source_meta = discover_qualified_carriers(root)
    except Exception as ex:
        source_discovery_error = f"{type(ex).__name__}: {ex}"

    source_ok = bool(
        source_discovery_error is None
        and source_meta.get("publication_ready_geometry_layer")
        and int(source_meta.get("n_qualified_carriers", 0)) > 0
        and int(source_meta.get("n_descriptor_errors", 0)) == 0
    )
    src_metrics = {
        "pklsa_expected_schema": "PKLSA-HIGH-RES-QUALIFICATION-4",
        "pklsa_expected_atlas_version": "0.4.0",
        "publication_ready_geometry_layer": bool(source_meta.get("publication_ready_geometry_layer", False)),
        "release_schema": source_meta.get("release_schema"),
        "atlas_version": source_meta.get("atlas_version"),
        "builder_version": source_meta.get("builder_version"),
        "n_qualified_carriers": int(source_meta.get("n_qualified_carriers", 0)),
        "n_upstream_carriers": int(source_meta.get("n_upstream_carriers", 0)),
        "n_generated_carriers": int(source_meta.get("n_generated_carriers", 0)),
        "n_qualification_summaries": int(source_meta.get("n_qualification_summaries", 0)),
        "n_excluded_topologies": int(source_meta.get("n_excluded_topologies", 0)),
        "n_descriptor_errors": int(source_meta.get("n_descriptor_errors", 0)),
        "discovery_error": source_discovery_error,
    }
    write_json(out / "PKLSA_SOURCE_AUDIT.json", {"schema":"A016-PKLSA-SOURCE-AUDIT-1", **src_metrics})
    write_json(out / "private" / "PKLSA_SOURCE_AUDIT_PRIVATE.json", {"schema":"A016-PKLSA-SOURCE-AUDIT-PRIVATE-1", "discovery_error":source_discovery_error, "source_meta":source_meta})
    ledger.record("G1", "PASS" if source_ok else "FAIL", metrics=src_metrics, reason="PKLSA v0.4.0 must expose one publication-ready geometry layer with resolvable qualified carriers; topology/source identities remain private during blind scoring.")

    controls = _reference_controls()
    ledger.record("G2", "PASS" if controls["pass"] else "FAIL", metrics=controls, reason="Self-contained FP64 sanity controls; independent of external knot identities.")

    pop = cauchy_population_control()
    t = cfg["thresholds"]
    if ledger.dependencies_pass("P0"):
        p0 = bool(pop["cauchy_relative_error"] <= float(t["cauchy_relative_error_max"]) and pop["zero_remains_zero"] and pop["nonzero_remains_nonzero"])
        ledger.record("P0", "PASS" if p0 else "FAIL", metrics={k: pop[k] for k in ("cauchy_relative_error", "zero_population_abs_error", "zero_remains_zero", "nonzero_remains_nonzero")}, reason="Exact Cauchy-map material-population control under an invertible incompressible affine flow.")
    else:
        ledger.skip_due_prerequisite("P0")
    if ledger.dependencies_pass("P1"):
        p1 = bool(pop["jacobian_abs_error"] <= float(t["jacobian_abs_error_max"]))
        ledger.record("P1", "PASS" if p1 else "FAIL", metrics={"det_F": pop["det_F"], "jacobian_abs_error": pop["jacobian_abs_error"]}, reason="det(F)=1 material-volume control.")
    else:
        ledger.skip_due_prerequisite("P1")
    if ledger.dependencies_pass("P2"):
        p2 = bool(pop["flux_relative_error"] <= float(t["flux_relative_error_max"]))
        ledger.record("P2", "PASS" if p2 else "FAIL", metrics={"flux_initial": pop["flux_initial"], "flux_final": pop["flux_final"], "flux_relative_error": pop["flux_relative_error"]}, reason="Stretching raises |omega| while reciprocal cross-section change preserves vorticity flux.")
    else:
        ledger.skip_due_prerequisite("P2")

    samples: list[dict[str, Any]] = []
    private_map: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if source_ok and ledger.status("G2") == "PASS":
        mp = _mode_params(cfg, mode)
        selected = stratified_limit(carriers, mp["max_files"])
        key = (root / "private" / "OPAQUE_ID_KEY.bin").read_bytes()
        for carrier in selected:
            try:
                public, private = _compute_sample(carrier, cfg, mode, key)
                samples.append(public)
                private_map.append(private)
            except Exception as ex:
                identity_material = f"{carrier.geometry_sha256}:{carrier.carrier_id}"
                bid = opaque_id(identity_material, key, 16)
                topology_group_id = opaque_id("topology:" + carrier.topology_id, key, 16)
                errors.append({
                    "blind_id": bid,
                    "topology_group_id": topology_group_id,
                    "provider_group_id": opaque_id("provider-group:" + carrier.provider_group, key, 16),
                    "source_generated": bool(carrier.generated),
                    "error_type": type(ex).__name__,
                    "error": str(ex),
                })
                private_map.append({
                    "blind_id": bid, "topology_group_id": topology_group_id,
                    "topology_id": carrier.topology_id, "carrier_id": carrier.carrier_id,
                    "source_family": carrier.source_family, "provider_group": carrier.provider_group,
                    "source_path": str(carrier.source_path), "geometry_sha256": carrier.geometry_sha256,
                })
        if not selected:
            errors.append({"blind_id": None, "error_type": "NoInputs", "error": "No qualified PKLSA carriers were selected."})

    write_json(out / "BLIND_SAMPLE_METRICS.json", {
        "schema": "A016-BLIND-SAMPLE-METRICS-3",
        "mode": mode,
        "samples": samples,
        "errors": errors,
    })
    write_json(out / "private" / "INPUT_REVEAL_MAP.json", {
        "schema": "A016-RUNTIME-INPUT-REVEAL-3",
        "mapping": private_map,
    })

    source_gates = ["H0", "H1", "H2", "H3", "H4", "P3", "P4", "P5", "P6"]
    for gid in source_gates:
        if not ledger.dependencies_pass(gid):
            ledger.skip_due_prerequisite(gid)
            continue
        st, metrics, reason = _aggregate(samples, errors, gid)
        if gid == "P6":
            eligible_rows = [s["far_field"] for s in samples if s["sample_gate_pass"].get("P6") is not None]
            metrics["velocity_decay_exponents"] = [r.get("velocity_decay_exponent") for r in eligible_rows]
            metrics["pressure_gradient_decay_exponents"] = [r.get("derived_pressure_gradient_decay_exponent") for r in eligible_rows]
            if len(eligible_rows) < int(t["far_field_min_eligible"]):
                st = "UNRESOLVED"
                reason = "Fewer than the preregistered minimum number of nonzero-vector-area geometries were eligible."
        ledger.record(gid, st, metrics=metrics, reason=reason)

    if ledger.dependencies_pass("X0"):
        st, metrics, reason = evaluate_cross_source_consistency(samples, errors, cfg)
        ledger.record("X0", st, metrics=metrics, reason=reason)
    else:
        ledger.skip_due_prerequisite("X0")

    if ledger.dependencies_pass("B0"):
        st, metrics, reason, backend = _cpp_parity(root, cfg)
        ledger.record("B0", st, metrics=metrics, reason=reason, requested_backend="cpp", actual_backend=backend.get("actual_backend"), authority=backend.get("authority", "CERTIFICATION" if st == "PASS" else None))
    else:
        ledger.skip_due_prerequisite("B0")
        backend = {"status": "NOT_RUN_PREREQUISITE"}

    # G9 is framework-controlled and is appended as DEFERRED by the blind runner.
    return {
        "schema": "A016-BACKEND-MANIFEST-3",
        "python_reference": {"actual_backend": "python-numpy-fp64", "precision": "float64", "authority": "REFERENCE"},
        "cpp_certification": backend,
        "n_public_samples": len(samples),
        "n_sample_errors": len(errors),
        "continue_after_scientific_fail": True,
    }
