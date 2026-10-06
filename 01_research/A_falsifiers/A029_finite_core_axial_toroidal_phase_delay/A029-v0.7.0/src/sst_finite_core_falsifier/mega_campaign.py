"""A029 v0.7.0 Specific-Lagrangian Mega Falsifier.

This is an additive orchestration/certification layer over the sealed v0.6
specific-Lagrangian producer.  The parent producer is hash-guarded and left
unchanged.

Ordered run:
  00 parent/preflight + fresh blind prepare
  01 finite K_l + C_k kernel campaign
  02 Delta->0 / Richardson / radial curvature certification
  03 independent raw amplitude + physical phase-origin qualification
  04 physical-reference + SI action + A042/QGI phase closure
  05 full-radial curvature coherence/cancellation characterization
  06 rigid/mirror/orientation transformation characterization
  07 attosecond forward gate using a frozen source-linked mapping matrix

Every missing physical prerequisite is fail-closed as NOT_RUN.  No synthetic
amplitude, physical scale, phase origin, reference displacement, or attosecond
mapping is inserted.
"""
from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
import math
import shutil
import zipfile
from typing import Any

import numpy as np

from .lagrangian_certification import (
    complex_overlap,
    complex_rms,
    construct_curvature_kernel,
    phase_align_series,
    quadratic_power_exponent,
    relative_span,
    richardson_zero_from_two,
)
from .model import Candidate, load_candidate
from .native import backend_name
from .prepare import prepare
from .raw_timeseries import find_raw_modal_timeseries, load_scientific_series

SCHEMA = "A029-SST-SPECIFIC-LAGRANGIAN-MEGA-2.0"
EXPECTED_PARENT_PRODUCER_SHA256 = "df880fdb1814ad568728506033ade1b15fde42c6726fdad854a7ecbc706136a0"
EXPECTED_PARENT_TEST_SHA256 = "1b3d131f55b940f47f916f43845c24a877ac064c81afe2ef49a573ac04aad56f"
CLEAN_FLAGS = (
    "depends_on_h",
    "depends_on_hbar",
    "depends_on_compton_radius",
    "depends_on_electron_mass",
    "depends_on_alpha",
)


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return [_jsonable(v) for v in x.tolist()]
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, complex):
        return {"real": float(x.real), "imag": float(x.imag)}
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x


def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(_jsonable(obj), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows([{k: _jsonable(v) for k, v in r.items()} for r in rows])


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _rooted(project_root, value):
    p = Path(value)
    return p if p.is_absolute() else Path(project_root) / p


def _cumtrapz(t, y):
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    out = np.zeros_like(y, dtype=float)
    if len(t) > 1:
        out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(t))
    return out


def _parent_integrity(project_root: Path) -> dict[str, Any]:
    producer = project_root / "src" / "sst_finite_core_falsifier" / "sst_lagrangian.py"
    test = project_root / "tests" / "test_sst_lagrangian.py"
    if not producer.exists():
        return {"status": "FAIL", "reason": "v0.6 parent sst_lagrangian.py missing"}
    psha = sha256_file(producer)
    tsha = sha256_file(test) if test.exists() else None
    ok = psha == EXPECTED_PARENT_PRODUCER_SHA256 and (tsha in (None, EXPECTED_PARENT_TEST_SHA256))
    return {
        "status": "PASS" if ok else "FAIL",
        "producer_sha256": psha,
        "expected_producer_sha256": EXPECTED_PARENT_PRODUCER_SHA256,
        "test_sha256": tsha,
        "expected_test_sha256": EXPECTED_PARENT_TEST_SHA256,
        "producer_unchanged_by_v070": True,
    }


def _identify_pair(row, catalog):
    a = load_candidate(Path(catalog) / row["geometry_a"])
    b = load_candidate(Path(catalog) / row["geometry_b"])
    za = abs(float(a.closure_offset)) <= 1e-14
    zb = abs(float(b.closure_offset)) <= 1e-14
    if za == zb:
        raise ValueError(f"{row['pair_id']}: expected exactly one exact-closure candidate")
    if za:
        return a, b, row["candidate_a"], row["candidate_b"]
    return b, a, row["candidate_b"], row["candidate_a"]


def _save_stage1_npz(path, r):
    np.savez_compressed(
        path,
        t_hat=np.asarray(r["t_hat"], float),
        r_hat=np.asarray(r["r_hat"], float),
        K_core_mean_re=np.asarray(r["K_l_core_mean_complex"]).real,
        K_core_mean_im=np.asarray(r["K_l_core_mean_complex"]).imag,
        Ck_core_mean_re=np.asarray(r["C_k_core_mean_complex"]).real,
        Ck_core_mean_im=np.asarray(r["C_k_core_mean_complex"]).imag,
        K_radial_re=np.asarray(r["K_l_radial_complex"]).real,
        K_radial_im=np.asarray(r["K_l_radial_complex"]).imag,
        Ck_radial_re=np.asarray(r["C_k_radial_complex"]).real,
        Ck_radial_im=np.asarray(r["C_k_radial_complex"]).imag,
        closed_core_mean_re=np.asarray(r["closed_lagrangian_core_mean_complex"]).real,
        closed_core_mean_im=np.asarray(r["closed_lagrangian_core_mean_complex"]).imag,
    )


def stage01_kernel_campaign(catalog, out, cfg, limit=None):
    d = Path(out) / "01_kernel_campaign"
    (d / "cases").mkdir(parents=True, exist_ok=True)
    rows = read_csv(Path(catalog) / "pairs_public.csv")
    rows = rows[:limit] if limit else rows
    summary = []
    for row in rows:
        pid = row["pair_id"]
        try:
            closed, control, cid, _ = _identify_pair(row, catalog)
            r = construct_curvature_kernel(
                closed,
                control,
                cfg,
                n_t=int(cfg["mega"]["stage01_n_t"]),
                n_cycles=float(cfg["mega"]["stage01_cycles"]),
            )
            diag = r.get("diagnostics", {})
            rec = {
                "pair_id": pid,
                "closed_candidate_id": cid,
                "status": r.get("status"),
                "scientifically_qualified_parent": bool(r.get("scientifically_qualified_parent", False)),
                "geometry_sha256": r.get("geometry_sha256"),
                "basis_hash": r.get("basis_hash"),
                "radial_n": r.get("radial_n"),
                "control_offset_abs": r.get("control_offset_abs"),
                "delta_k_hat": r.get("delta_k_hat"),
                "branch_overlap_minus": r.get("branch_overlap", {}).get("minus"),
                "branch_overlap_plus": r.get("branch_overlap", {}).get("plus"),
                "finite_K_to_closed_rms": diag.get("finite_K_to_closed_rms"),
                "finite_K_core_mean_rms": diag.get("finite_K_core_mean_rms"),
                "C_k_core_mean_rms": diag.get("C_k_core_mean_rms"),
                "max_branch_growth_gain": r.get("time_horizon", {}).get("max_branch_growth_gain"),
                "arrays_npz": f"cases/{pid}.npz",
            }
            if "t_hat" in r:
                _save_stage1_npz(d / "cases" / f"{pid}.npz", r)
        except Exception as e:
            rec = {"pair_id": pid, "status": "ERROR", "scientifically_qualified_parent": False, "error": repr(e)}
        summary.append(rec)
    write_csv(d / "kernel_summary.csv", summary)
    write_json(d / "kernel_summary.json", {"schema": SCHEMA, "stage": 1, "rows": summary})
    return {
        "status": "READY",
        "n_pairs": len(summary),
        "n_parent_qualified": sum(bool(r.get("scientifically_qualified_parent")) for r in summary),
        "rows": summary,
    }


def _richardson_record(large: dict, small: dict) -> dict[str, Any]:
    c1 = np.asarray(large["C_k_core_mean_complex"], complex)
    c2 = np.asarray(small["C_k_core_mean_complex"], complex)
    c0 = richardson_zero_from_two(c1, float(large["delta_k_hat"]), c2, float(small["delta_k_hat"]))
    return {
        "C0": c0,
        "rms": complex_rms(c0),
        "basis_hash": small.get("basis_hash"),
        "max_branch_growth_gain": small.get("time_horizon", {}).get("max_branch_growth_gain"),
        "t_hat": np.asarray(small["t_hat"], float),
    }


def stage02_certification(catalog, out, cfg, stage1, limit=None, allow_adaptive_extension=True):
    d = Path(out) / "02_certification"
    (d / "cases").mkdir(parents=True, exist_ok=True)
    mc = cfg["mega"]["certification"]
    public = {r["pair_id"]: r for r in read_csv(Path(catalog) / "pairs_public.csv")}
    candidates = list(stage1["rows"])
    if limit:
        candidates = candidates[:limit]
    rows = []

    offset_scales = [float(x) for x in mc["offset_scales"]]
    if len(offset_scales) < 4 or sorted(offset_scales, reverse=True) != offset_scales:
        raise ValueError("offset_scales must contain >=4 strictly descending scales")
    s_large, s_small = offset_scales[-2], offset_scales[-1]
    radial_levels = [int(x) for x in mc["radial_extrapolation_levels"]]
    if len(radial_levels) < 3:
        raise ValueError("radial_extrapolation_levels must contain at least 3 levels")
    n_ref = max(radial_levels)

    for s1 in candidates:
        pid = s1["pair_id"]
        if not s1.get("scientifically_qualified_parent"):
            rows.append({"pair_id": pid, "status": "NOT_RUN_PARENT_MODE", "reason": s1.get("status")})
            continue
        try:
            closed, control, _, _ = _identify_pair(public[pid], catalog)
            base_delta = abs(float(control.closure_offset))
            cache: dict[tuple[int, float], dict] = {}

            def get(N, scale):
                key = (int(N), float(scale))
                if key not in cache:
                    cache[key] = construct_curvature_kernel(
                        closed,
                        control,
                        cfg,
                        control_offset_abs=base_delta * float(scale),
                        radial_n=int(N),
                        n_t=int(mc["sweep_n_t"]),
                        n_cycles=float(mc["sweep_cycles"]),
                        evaluate_parent_convergence=(int(N) == int(n_ref)),
                    )
                return cache[key]

            # Detuning null and local-curvature stability at the highest radial resolution.
            offset_rows = []
            for scale in offset_scales:
                rr = get(n_ref, scale)
                offset_rows.append({
                    "scale": scale,
                    "delta": rr.get("control_offset_abs"),
                    "delta_k_hat": rr.get("delta_k_hat"),
                    "K_rms": complex_rms(rr["K_l_core_mean_complex"]) if "K_l_core_mean_complex" in rr else None,
                    "Ck_rms": complex_rms(rr["C_k_core_mean_complex"]) if "C_k_core_mean_complex" in rr else None,
                    "status": rr.get("status"),
                    "branch_min": min(rr.get("branch_overlap", {}).get("minus", 0.0), rr.get("branch_overlap", {}).get("plus", 0.0)),
                })
            p = quadratic_power_exponent(
                [x["delta_k_hat"] for x in offset_rows if x["delta_k_hat"]],
                [x["K_rms"] for x in offset_rows if x["K_rms"]],
            )
            cspan = relative_span([x["Ck_rms"] for x in offset_rows[-3:]])
            monotone = all(
                float(offset_rows[i + 1]["K_rms"]) < float(offset_rows[i]["K_rms"])
                for i in range(len(offset_rows) - 1)
                if offset_rows[i]["K_rms"] is not None and offset_rows[i + 1]["K_rms"] is not None
            )
            branch_all = all(x["status"] == "QUALIFIED_PARENT_MODE" for x in offset_rows)
            detuning_pass = bool(
                branch_all
                and monotone
                and np.isfinite(p)
                and abs(p - 2.0) <= float(mc["detuning_power_abs_error_max"])
                and cspan <= float(mc["offset_curvature_rel_span_max"])
            )

            # Fail closed at the first scientific dependency.  If the symmetric
            # detuning null itself fails, radial certification is not meaningful and
            # is deliberately not spent on an already-falsified branch.
            if not detuning_pass:
                rec = {
                    "pair_id": pid,
                    "status": "FAIL",
                    "detuning_null_gate_pass": False,
                    "detuning_power_exponent": p,
                    "offset_curvature_rel_span_last3": cspan,
                    "offset_sweep": offset_rows,
                    "radial_curvature_gate_pass": False,
                    "radial_extrapolation": [],
                    "adaptive_radial_extension_status": "NOT_RUN_UPSTREAM_DETUNING",
                    "interpretation": "Detuning null failed; downstream radial curvature certification was not executed.",
                }
                rows.append(rec)
                continue

            # Richardson C_k(dk->0) at multiple N.  Comparing the extrapolated local
            # object avoids treating the finite-Delta K residual as an invariant.
            radial_rows = []
            rich: dict[int, dict] = {}
            for N in radial_levels:
                a = get(N, s_large)
                b = get(N, s_small)
                if a.get("status") != "QUALIFIED_PARENT_MODE" or b.get("status") != "QUALIFIED_PARENT_MODE":
                    radial_rows.append({"N": N, "status": "NOT_QUALIFIED"})
                    continue
                rr = _richardson_record(a, b)
                rich[N] = rr
                radial_rows.append({"N": N, "status": "READY", "Ck0_rms": rr["rms"]})

            def radial_gate(levels):
                last = list(levels)[-3:]
                if not all(N in rich for N in last):
                    return False, math.inf, 0.0, last
                span = relative_span([rich[N]["rms"] for N in last])
                ref = rich[last[-1]]["C0"]
                overlaps = []
                for N in last[:-1]:
                    _, _, ov = phase_align_series(ref, rich[N]["C0"])
                    overlaps.append(ov)
                shape = min(overlaps) if overlaps else 1.0
                passed = bool(span <= float(mc["radial_curvature_rel_span_max"]) and shape >= float(mc["radial_shape_overlap_min"]))
                return passed, span, shape, last

            radial_pass, rspan, shape_min, gate_levels = radial_gate(radial_levels)
            extension_status = "NOT_NEEDED" if radial_pass else "NOT_RUN"
            extension_levels = [int(x) for x in mc.get("adaptive_radial_extension_levels", [])]
            if (not radial_pass) and detuning_pass and extension_levels:
                if allow_adaptive_extension:
                    extension_status = "EXECUTED"
                    for N in extension_levels:
                        a = get(N, s_large)
                        b = get(N, s_small)
                        if a.get("status") != "QUALIFIED_PARENT_MODE" or b.get("status") != "QUALIFIED_PARENT_MODE":
                            radial_rows.append({"N": N, "status": "NOT_QUALIFIED", "adaptive_extension": True})
                            continue
                        rr = _richardson_record(a, b)
                        rich[N] = rr
                        radial_rows.append({"N": N, "status": "READY", "Ck0_rms": rr["rms"], "adaptive_extension": True})
                    combined = radial_levels + [N for N in extension_levels if N not in radial_levels]
                    radial_pass, rspan, shape_min, gate_levels = radial_gate(combined)
                else:
                    extension_status = "SKIPPED_DIAGNOSTIC_BACKEND"

            status = "PASS" if detuning_pass and radial_pass else "FAIL"
            cert_n = max(rich) if rich else n_ref
            rec = {
                "pair_id": pid,
                "status": status,
                "detuning_null_gate_pass": detuning_pass,
                "detuning_power_exponent": p,
                "offset_curvature_rel_span_last3": cspan,
                "offset_sweep": offset_rows,
                "radial_curvature_gate_pass": radial_pass,
                "radial_curvature_rel_span_last3": rspan,
                "radial_shape_overlap_min_last3": shape_min,
                "radial_extrapolation": radial_rows,
                "radial_gate_levels": gate_levels,
                "adaptive_radial_extension_status": extension_status,
                "certification_radial_n": cert_n,
                "certification_basis_hash": rich.get(cert_n, {}).get("basis_hash"),
                "certification_geometry_sha256": s1.get("geometry_sha256"),
                "max_branch_growth_gain": rich.get(cert_n, {}).get("max_branch_growth_gain"),
                "tested_delta_k_hat_max": max(float(x["delta_k_hat"]) for x in offset_rows if x["delta_k_hat"]),
                "tested_delta_k_hat_min": min(float(x["delta_k_hat"]) for x in offset_rows if x["delta_k_hat"]),
                "interpretation": (
                    "Primary object is Richardson-extrapolated C_k = d^2 L/d(k_hat)^2. "
                    "Finite K(Delta) is retained as a diagnostic and must vanish quadratically."
                ),
            }

            if cert_n in rich:
                rr_small = get(cert_n, s_small)
                rr_large = get(cert_n, s_large)
                C0_core = rich[cert_n]["C0"]
                C0_radial = richardson_zero_from_two(
                    np.asarray(rr_large["C_k_radial_complex"], complex),
                    float(rr_large["delta_k_hat"]),
                    np.asarray(rr_small["C_k_radial_complex"], complex),
                    float(rr_small["delta_k_hat"]),
                )
                np.savez_compressed(
                    d / "cases" / f"{pid}_Ck0.npz",
                    t_hat=np.asarray(rr_small["t_hat"], float),
                    r_hat=np.asarray(rr_small["r_hat"], float),
                    Ck0_core_mean_re=C0_core.real,
                    Ck0_core_mean_im=C0_core.imag,
                    Ck0_radial_re=C0_radial.real,
                    Ck0_radial_im=C0_radial.imag,
                    delta_k_hat_large=float(rr_large["delta_k_hat"]),
                    delta_k_hat_small=float(rr_small["delta_k_hat"]),
                )
                rec["certified_kernel_npz"] = f"cases/{pid}_Ck0.npz"
        except Exception as e:
            rec = {"pair_id": pid, "status": "ERROR", "error": repr(e)}
        rows.append(rec)

    write_json(d / "certification.json", {"schema": SCHEMA, "stage": 2, "rows": rows})
    write_csv(
        d / "certification.csv",
        [{k: v for k, v in r.items() if k not in ("offset_sweep", "radial_extrapolation")} for r in rows],
    )
    return {"status": "READY", "n_tested": len(rows), "n_pass": sum(r.get("status") == "PASS" for r in rows), "rows": rows}


def _amplitude_phase_from_record(rec, expected_geometry_sha, expected_basis_hash):
    reasons = []
    if rec.get("amplitude_provenance_status") != "INDEPENDENT_RAW_DYNAMICS":
        reasons.append("amplitude_provenance_status must be INDEPENDENT_RAW_DYNAMICS")
    if rec.get("amplitude_semantics") != "core_rms_velocity_ratio_to_V0":
        reasons.append("amplitude_semantics must be core_rms_velocity_ratio_to_V0")
    if rec.get("mode_normalization") != "core_rms_velocity_unity":
        reasons.append("mode_normalization must be core_rms_velocity_unity")
    if rec.get("amplitude_reference") != "t0":
        reasons.append("amplitude_reference must be t0")
    if rec.get("source_geometry_sha256") != expected_geometry_sha:
        reasons.append("source_geometry_sha256 mismatch")
    if rec.get("lagrangian_basis_hash") != expected_basis_hash:
        reasons.append("lagrangian_basis_hash mismatch")
    if reasons:
        return None, None, reasons
    t = np.asarray(rec.get("t", []), float)
    a = np.asarray(rec.get("a_real", []), float) + 1j * np.asarray(rec.get("a_imag", []), float)
    if len(t) != len(a) or len(t) < 1:
        return None, None, ["invalid raw modal series"]
    j = int(np.argmin(np.abs(t)))
    tol = float(rec.get("t0_tolerance", 1e-9 * max(1.0, float(np.ptp(t)) if len(t) > 1 else 1.0)))
    if abs(float(t[j])) > tol:
        return None, None, ["raw modal series has no t=0 reference sample"]
    a0 = complex(a[j])
    eps = float(abs(a0))
    if not np.isfinite(eps) or eps <= 0:
        return None, None, ["nonpositive/nonfinite epsilon0"]
    return eps, float(np.angle(a0)), []


def stage03_amplitude_phase(project_root, out, cfg, stage2):
    d = Path(out) / "03_amplitude_phase"
    d.mkdir(parents=True, exist_ok=True)
    roots = [_rooted(project_root, x) for x in cfg["mega"]["amplitude"].get("raw_timeseries_roots", [])]
    paths = find_raw_modal_timeseries(*roots)
    series = load_scientific_series(paths)
    by_geom: dict[str, list[dict]] = {}
    for r in series:
        by_geom.setdefault(str(r.get("source_geometry_sha256", "")), []).append(r)

    rows = []
    max_linear = float(cfg["mega"]["amplitude"].get("max_linear_perturbation_ratio", 0.1))
    for c in stage2["rows"]:
        pid = c["pair_id"]
        if c.get("status") != "PASS":
            rows.append({"pair_id": pid, "status": "NOT_RUN_UPSTREAM_CERTIFICATION"})
            continue
        g = str(c.get("certification_geometry_sha256"))
        candidates = by_geom.get(g, [])
        accepted = None
        reject_reasons = []
        for rec in candidates:
            eps, phase0, reasons = _amplitude_phase_from_record(rec, g, str(c.get("certification_basis_hash")))
            if reasons:
                reject_reasons.append({"path": rec.get("_path"), "reasons": reasons})
                continue
            gain = float(c.get("max_branch_growth_gain") or 1.0)
            if eps * gain > max_linear:
                reject_reasons.append({"path": rec.get("_path"), "reasons": [f"epsilon0*growth_gain exceeds {max_linear}"]})
                continue
            accepted = (rec, eps, phase0, gain)
            break
        if accepted is None:
            rows.append({
                "pair_id": pid,
                "status": "NOT_RUN_NO_MATCHING_INDEPENDENT_RAW_SERIES",
                "n_geometry_matches": len(candidates),
                "rejections": reject_reasons,
            })
            continue
        rec, eps, phase0, gain = accepted
        rows.append({
            "pair_id": pid,
            "status": "PASS",
            "epsilon0": eps,
            "phase0_rad": phase0,
            "max_branch_growth_gain": gain,
            "max_perturbation_ratio_over_window": eps * gain,
            "source_geometry_sha256": g,
            "lagrangian_basis_hash": c.get("certification_basis_hash"),
            "raw_series_path": rec.get("_path"),
            "raw_series_sha256": sha256_file(rec["_path"]) if rec.get("_path") else None,
        })
    write_json(d / "amplitude_phase.json", {"schema": SCHEMA, "stage": 3, "n_scientific_series_discovered": len(series), "rows": rows})
    return {"status": "READY", "n_pass": sum(r.get("status") == "PASS" for r in rows), "rows": rows}


def _discover_qgi(project_root, configured):
    p = _rooted(project_root, configured) if configured else Path("__missing__")
    if p.exists():
        return p, None
    search_root = Path(project_root).parent.parent
    hits = sorted(search_root.glob("A042*/**/qgi_specific_action.json")) if search_root.exists() else []
    if len(hits) == 1:
        return hits[0], None
    if len(hits) > 1:
        return p, f"ambiguous QGI discovery: {len(hits)} qgi_specific_action.json files found"
    return p, "QGI specific-action JSON missing"


def _clean_scale(meta):
    reasons = []
    if meta.get("status") != "INDEPENDENT_PHYSICAL_SCALE":
        reasons.append("status must be INDEPENDENT_PHYSICAL_SCALE")
    for k in CLEAN_FLAGS:
        if bool(meta.get(k, True)):
            reasons.append(f"{k} must be false")
    if int(meta.get("free_fit_parameters", -1)) != 0:
        reasons.append("free_fit_parameters must equal 0")
    for k in ("core_radius_m", "velocity_scale_m_s"):
        try:
            if not (float(meta[k]) > 0 and np.isfinite(float(meta[k]))):
                reasons.append(f"{k} invalid")
        except Exception:
            reasons.append(f"{k} missing")
    return not reasons, reasons


def _clean_reference(meta):
    reasons = []
    if meta.get("status") != "PHYSICALLY_DERIVED_REFERENCE":
        reasons.append("status must be PHYSICALLY_DERIVED_REFERENCE")
    if meta.get("reference_mode") != "LOCAL_K_CURVATURE":
        reasons.append("reference_mode must be LOCAL_K_CURVATURE")
    if not bool(meta.get("closure_displacement_independently_derived", False)):
        reasons.append("closure_displacement_independently_derived must be true")
    if bool(meta.get("depends_on_attosecond_data", True)):
        reasons.append("depends_on_attosecond_data must be false")
    if bool(meta.get("depends_on_qgi_target", True)):
        reasons.append("depends_on_qgi_target must be false")
    if int(meta.get("free_fit_parameters", -1)) != 0:
        reasons.append("free_fit_parameters must equal 0")
    try:
        dk = abs(float(meta["physical_delta_k_hat"]))
        if not (dk > 0 and np.isfinite(dk)):
            reasons.append("physical_delta_k_hat invalid")
    except Exception:
        reasons.append("physical_delta_k_hat missing")
    return not reasons, reasons


def stage04_cross_chain(project_root, out, cfg, stage2, stage3):
    d = Path(out) / "04_action_phase_closure"
    (d / "cases").mkdir(parents=True, exist_ok=True)
    cc = cfg["mega"]["cross_chain"]
    qpath, qerr = _discover_qgi(project_root, cc.get("qgi_specific_action_json", ""))
    spath = _rooted(project_root, cc.get("physical_scale_provenance_json", ""))
    rpath = _rooted(project_root, cc.get("reference_contract_json", ""))
    common = []
    if qerr:
        common.append(qerr)
    if not spath.exists():
        common.append("independent physical scale provenance missing")
    if not rpath.exists():
        common.append("physical reference contract missing")

    qgi = scale = ref = None
    if not common:
        qgi = json.loads(qpath.read_text(encoding="utf-8"))
        scale = json.loads(spath.read_text(encoding="utf-8"))
        ref = json.loads(rpath.read_text(encoding="utf-8"))
        clean, reasons = _clean_scale(scale)
        if not clean:
            common += reasons
        clean, reasons = _clean_reference(ref)
        if not clean:
            common += reasons
        if qgi.get("status") != "READY" or qgi.get("hbar_over_m_m2_s") in (None, ""):
            common.append("QGI specific action not READY")
        if bool(qgi.get("planck_target_used", True)):
            common.append("QGI specific action used Planck target")

    cert = {r["pair_id"]: r for r in stage2["rows"]}
    amp = {r["pair_id"]: r for r in stage3["rows"]}
    rows = []
    for pid, c in cert.items():
        if c.get("status") != "PASS":
            rows.append({"pair_id": pid, "status": "NOT_RUN_UPSTREAM_CERTIFICATION"})
            continue
        a = amp.get(pid, {})
        if a.get("status") != "PASS":
            rows.append({"pair_id": pid, "status": "NOT_RUN_NO_ABSOLUTE_AMPLITUDE_PHASE"})
            continue
        if common:
            rows.append({"pair_id": pid, "status": "NOT_RUN_PROVENANCE", "reasons": common})
            continue
        dk_phys = abs(float(ref["physical_delta_k_hat"]))
        if dk_phys > float(c["tested_delta_k_hat_max"]):
            rows.append({"pair_id": pid, "status": "NOT_RUN_REFERENCE_OUTSIDE_CERTIFIED_DETUNING_RANGE", "physical_delta_k_hat": dk_phys})
            continue
        z = np.load(Path(out) / "02_certification" / "cases" / f"{pid}_Ck0.npz")
        t_hat = np.asarray(z["t_hat"], float)
        C0 = np.asarray(z["Ck0_core_mean_re"], float) + 1j*np.asarray(z["Ck0_core_mean_im"], float)
        # For K = L(0)-[L(-dk)+L(+dk)]/2, K ~ -0.5 * L'' * dk^2.
        Kphys = -0.5 * C0 * dk_phys * dk_phys
        eps = float(a["epsilon0"])
        phase0 = float(a["phase0_rad"])
        dl_hat = eps * np.real(np.exp(1j * phase0) * Kphys)
        ds_hat = _cumtrapz(t_hat, dl_hat)
        core_radius = float(scale["core_radius_m"])
        V0 = float(scale["velocity_scale_m_s"])
        t_s = t_hat * core_radius / V0
        dl_si = V0*V0 * dl_hat
        ds_si = core_radius*V0 * ds_hat
        hbm = float(qgi["hbar_over_m_m2_s"])
        sigma_hbm = qgi.get("sigma_hbar_over_m_m2_s")
        sigma_hbm = None if sigma_hbm in (None, "") else float(sigma_hbm)
        phi = ds_si / hbm
        sigma_phi = None if sigma_hbm is None else np.abs(phi) * abs(sigma_hbm / hbm)
        out_npz = d / "cases" / f"{pid}_action_phase.npz"
        save = {
            "t_hat": t_hat,
            "t_s": t_s,
            "delta_l_hat": dl_hat,
            "delta_l_sst_m2_s2": dl_si,
            "delta_specific_action_m2_s": ds_si,
            "delta_phase_rad": phi,
            "Ck0_core_mean_re": C0.real,
            "Ck0_core_mean_im": C0.imag,
        }
        if sigma_phi is not None:
            save["sigma_delta_phase_rad"] = sigma_phi
        np.savez_compressed(out_npz, **save)
        rows.append({
            "pair_id": pid,
            "status": "PASS",
            "epsilon0": eps,
            "phase0_rad": phase0,
            "physical_delta_k_hat": dk_phys,
            "core_radius_m": core_radius,
            "velocity_scale_m_s": V0,
            "hbar_over_m_qgi_m2_s": hbm,
            "sigma_hbar_over_m_qgi_m2_s": sigma_hbm,
            "max_abs_specific_action_m2_s": float(np.max(np.abs(ds_si))),
            "max_abs_phase_rad": float(np.max(np.abs(phi))),
            "relative_phase_rms_rad": float(np.sqrt(np.mean((phi - np.mean(phi))**2))),
            "action_npz": f"cases/{pid}_action_phase.npz",
            "action_npz_sha256": sha256_file(out_npz),
        })
    write_json(d / "cross_chain.json", {"schema": SCHEMA, "stage": 4, "global_prerequisite_reasons": common, "rows": rows})
    return {"status": "READY", "n_pass": sum(r.get("status") == "PASS" for r in rows), "rows": rows}


def stage05_radial(out, cfg, stage2):
    d = Path(out) / "05_radial"
    d.mkdir(parents=True, exist_ok=True)
    threshold = cfg["mega"]["radial"].get("coherence_min")
    rows = []
    for c in stage2["rows"]:
        pid = c["pair_id"]
        if c.get("status") != "PASS":
            rows.append({"pair_id": pid, "status": "NOT_RUN_UPSTREAM_CERTIFICATION"})
            continue
        z = np.load(Path(out) / "02_certification" / "cases" / f"{pid}_Ck0.npz")
        r = np.asarray(z["r_hat"], float)
        K = np.asarray(z["Ck0_radial_re"], float) + 1j*np.asarray(z["Ck0_radial_im"], float)
        mean = np.asarray(z["Ck0_core_mean_re"], float) + 1j*np.asarray(z["Ck0_core_mean_im"], float)
        mask = r <= 1.0
        if K.size == 0 or np.count_nonzero(mask) < 2:
            rows.append({"pair_id": pid, "status": "NOT_RUN_NO_RADIAL_CURVATURE"})
            continue
        rr = r[mask]
        kk = K[mask]
        amp = np.abs(kk)
        w = rr[:, None] * amp
        denom = np.sum(w, axis=0)
        resultant = np.abs(np.sum(w * np.exp(1j*np.angle(kk)), axis=0)) / np.maximum(denom, 1e-30)
        coh = float(np.nanmedian(resultant))
        field_rms_t = np.sqrt(np.trapezoid(np.abs(kk)**2 * rr[:, None], rr, axis=0) / max(float(np.trapezoid(rr, rr)), 1e-30))
        cancel = complex_rms(mean) / max(float(np.sqrt(np.mean(field_rms_t**2))), 1e-30)
        status = "CHARACTERIZED" if threshold is None else ("PASS" if coh >= float(threshold) else "FAIL")
        rows.append({
            "pair_id": pid,
            "status": status,
            "median_radial_phase_resultant": coh,
            "core_cancellation_ratio": float(cancel),
            "threshold": threshold,
            "observable": "Richardson-extrapolated C_k radial field",
        })
    write_json(d / "radial.json", {"schema": SCHEMA, "stage": 5, "rows": rows})
    return {"status": "READY", "rows": rows}


def _transform_candidate(c, kind):
    comps = []
    for x in c.components:
        y = np.asarray(x, float).copy()
        if kind == "mirror":
            y[:, 0] *= -1.0
        elif kind == "orientation_reverse":
            y = y[::-1].copy()
        elif kind == "rigid_rotation":
            ang = 0.731
            ca, sa = np.cos(ang), np.sin(ang)
            R = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1.0]])
            y = y @ R.T
        else:
            raise ValueError(kind)
        comps.append(y)
    return Candidate(
        comps,
        c.profile_name,
        c.axial_ratio,
        c.core_fraction,
        c.m,
        c.n,
        c.closure_offset,
        list(c.radial_levels),
        c.radial_n_dispersion,
        c.rmax,
        dict(c.metadata),
    )


def _transformed_Ck0(closed, control, cfg, radial_n=None):
    mc = cfg["mega"]["certification"]
    nref = int(radial_n) if radial_n is not None else max(int(x) for x in mc["radial_extrapolation_levels"])
    scales = [float(x) for x in mc["offset_scales"]]
    d0 = abs(float(control.closure_offset))
    a = construct_curvature_kernel(
        closed, control, cfg,
        control_offset_abs=d0*scales[-2], radial_n=nref,
        n_t=int(cfg["mega"]["transformations"]["n_t"]), n_cycles=float(cfg["mega"]["transformations"]["cycles"]),
    )
    b = construct_curvature_kernel(
        closed, control, cfg,
        control_offset_abs=d0*scales[-1], radial_n=nref,
        n_t=int(cfg["mega"]["transformations"]["n_t"]), n_cycles=float(cfg["mega"]["transformations"]["cycles"]),
    )
    if a.get("status") != "QUALIFIED_PARENT_MODE" or b.get("status") != "QUALIFIED_PARENT_MODE":
        return None, "branch not qualified"
    C0 = richardson_zero_from_two(
        np.asarray(a["C_k_core_mean_complex"], complex), float(a["delta_k_hat"]),
        np.asarray(b["C_k_core_mean_complex"], complex), float(b["delta_k_hat"]),
    )
    return C0, None


def stage06_transformations(catalog, out, cfg, stage2, limit=None):
    d = Path(out) / "06_transformations"
    d.mkdir(parents=True, exist_ok=True)
    public = {r["pair_id"]: r for r in read_csv(Path(catalog) / "pairs_public.csv")}
    cases = [r for r in stage2["rows"] if r.get("status") == "PASS"]
    maxc = cfg["mega"]["transformations"].get("max_cases")
    if limit:
        maxc = min(int(maxc), limit) if maxc else limit
    if maxc:
        cases = cases[:int(maxc)]
    rows = []
    for c in cases:
        pid = c["pair_id"]
        closed, control, _, _ = _identify_pair(public[pid], catalog)
        z = np.load(Path(out) / "02_certification" / "cases" / f"{pid}_Ck0.npz")
        base = np.asarray(z["Ck0_core_mean_re"], float) + 1j*np.asarray(z["Ck0_core_mean_im"], float)
        qb = complex_rms(base)
        rec = {"pair_id": pid, "status": "CHARACTERIZED", "signed_chirality_parity_status": "NOT_IDENTIFIABLE_WITHOUT_EXTERNAL_ORIENTATION_PHASE_CONVENTION"}
        for kind in ("rigid_rotation", "mirror", "orientation_reverse"):
            try:
                C0, reason = _transformed_Ck0(_transform_candidate(closed, kind), _transform_candidate(control, kind), cfg, c.get("certification_radial_n"))
                if C0 is None:
                    rec[kind + "_status"] = "NOT_RUN"
                    rec[kind + "_reason"] = reason
                    continue
                aligned, rot, ov = phase_align_series(base, C0)
                q = complex_rms(aligned)
                rec[kind + "_status"] = "READY"
                rec[kind + "_magnitude_ratio"] = q / max(qb, 1e-30)
                rec[kind + "_shape_overlap"] = ov
                rec[kind + "_phase_alignment_rad"] = rot
            except Exception as e:
                rec[kind + "_status"] = "ERROR"
                rec[kind + "_error"] = repr(e)
        tol = float(cfg["mega"]["transformations"]["rigid_rotation_rel_tol"])
        ovmin = float(cfg["mega"]["transformations"]["rigid_rotation_shape_overlap_min"])
        ratio = rec.get("rigid_rotation_magnitude_ratio", math.nan)
        rov = rec.get("rigid_rotation_shape_overlap", 0.0)
        rec["rigid_rotation_invariance_gate"] = "PASS" if np.isfinite(ratio) and abs(ratio - 1.0) <= tol and rov >= ovmin else "FAIL"
        rows.append(rec)
    write_json(d / "transformations.json", {"schema": SCHEMA, "stage": 6, "rows": rows})
    return {"status": "READY", "rows": rows}


def _forward(kernel, weights, phase):
    kw = kernel * weights[None, :]
    m0 = np.sum(kw, axis=1)
    m1 = np.sum(kw * np.exp(1j * phase), axis=1)
    dm = 1j * np.sum(kw * phase, axis=1)
    i0 = np.abs(m0)**2
    i1 = np.abs(m1)**2
    return i0, i1, 2*np.real(np.conj(m0)*dm)


def stage07_attosecond(project_root, out, cfg, stage4):
    d = Path(out) / "07_attosecond"
    (d / "cases").mkdir(parents=True, exist_ok=True)
    ac = cfg["mega"]["attosecond"]
    manifest = _rooted(project_root, ac.get("mapping_manifest_json", ""))
    if not manifest.exists():
        r = {"status": "NOT_RUN", "reason": "attosecond mapping manifest missing", "note": "no synthetic mapping is substituted"}
        write_json(d / "attosecond.json", r)
        return r
    meta = json.loads(manifest.read_text(encoding="utf-8"))
    if meta.get("mapping_to_attosecond_kernel") != "PHYSICALLY_DERIVED_AND_FROZEN" or int(meta.get("free_phase_fit_parameters", -1)) != 0:
        r = {"status": "INVALID_MAPPING_PROVENANCE", "provenance": meta}
        write_json(d / "attosecond.json", r)
        return r
    action = {r["pair_id"]: r for r in stage4["rows"] if r.get("status") == "PASS"}
    rows = []
    for ent in meta.get("entries", []):
        pid = str(ent.get("pair_id", ""))
        src = action.get(pid)
        if src is None:
            rows.append({"pair_id": pid, "status": "NOT_RUN_NO_CERTIFIED_ACTION_SOURCE"})
            continue
        action_path = Path(out) / "04_action_phase_closure" / src["action_npz"]
        if ent.get("source_action_sha256") != sha256_file(action_path):
            rows.append({"pair_id": pid, "status": "INVALID_SOURCE_HASH"})
            continue
        bundle = _rooted(project_root, ent.get("bundle_npz", ""))
        if not bundle.exists():
            rows.append({"pair_id": pid, "status": "NOT_RUN_MAPPING_BUNDLE_MISSING"})
            continue
        with np.load(action_path, allow_pickle=False) as za:
            ds_action = np.asarray(za["delta_specific_action_m2_s"], float)
        with np.load(bundle, allow_pickle=False) as z:
            req = ("kernel_re", "kernel_im", "weights", "action_map_matrix")
            miss = [k for k in req if k not in z.files]
            if miss:
                rows.append({"pair_id": pid, "status": "INVALID_MAPPING_BUNDLE", "missing": miss})
                continue
            K = np.asarray(z["kernel_re"], float) + 1j*np.asarray(z["kernel_im"], float)
            K = K[None, :] if K.ndim == 1 else K
            w = np.asarray(z["weights"], float)
            M = np.asarray(z["action_map_matrix"], float)
            extras = {k: np.asarray(z[k]) for k in z.files if k in ("energy_eV", "theta_rad", "delay_s", "direction")}
        if M.ndim != 2 or M.shape[1] != len(ds_action) or M.shape[0] != K.shape[1] or len(w) != K.shape[1]:
            rows.append({"pair_id": pid, "status": "INVALID_MAPPING_DIMENSIONS"})
            continue
        ds_kernel = M @ ds_action
        hbm = float(src["hbar_over_m_qgi_m2_s"])
        phase1 = ds_kernel / hbm
        phase = np.broadcast_to(phase1[None, :], K.shape)
        i0, i1, dilin = _forward(K, w, phase)
        probe = np.full(K.shape, float(ac.get("global_phase_probe_rad", 0.731)))
        g0, g1, _ = _forward(K, w, probe)
        null = float(np.max(np.abs(g1-g0) / np.maximum(g0, 1e-300)))
        rel = phase - np.mean(phase, axis=1, keepdims=True)
        save = {"I_orthodox": i0, "I_sst": i1, "delta_I_linear": dilin, "delta_phase_rad": phase, **extras}
        np.savez_compressed(d / "cases" / f"{pid}_attosecond_prediction.npz", **save)
        rows.append({
            "pair_id": pid,
            "status": "PASS" if null <= float(ac.get("global_phase_null_rel_max", 1e-12)) else "FAIL_GLOBAL_PHASE_NULL",
            "max_abs_phase_rad": float(np.max(np.abs(phase))),
            "relative_phase_rms_rad": float(np.sqrt(np.mean(rel*rel))),
            "global_phase_null_max_rel": null,
            "free_phase_fit_parameters": 0,
        })
    status = "READY" if rows else "NOT_RUN_NO_MAPPING_ENTRIES"
    write_json(d / "attosecond.json", {"status": status, "rows": rows, "mapping_manifest_sha256": sha256_file(manifest)})
    return {"status": status, "n_pass": sum(r.get("status") == "PASS" for r in rows), "rows": rows}


def _tree_hashes(root, exclude_parts=()):
    root = Path(root)
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(x in p.parts for x in exclude_parts):
            continue
        out[p.relative_to(root).as_posix()] = sha256_file(p)
    return out


def seal_blind(project_root, blind, catalog, config, private_commitment):
    project_root = Path(project_root)
    blind = Path(blind)
    code = {}
    for sub in ("src", "config"):
        p = project_root / sub
        if p.exists():
            code.update({f"{sub}/{k}": v for k, v in _tree_hashes(p, ("__pycache__", ".pytest_cache")).items()})
    for rel in ("run_specific_lagrangian_mega.py", "run_specific_lagrangian_mega.cmd", "PARENT_PROVENANCE.json", "MEGA_PATCH_v0.7.0_MANIFEST.json"):
        p = project_root / rel
        if p.exists():
            code[rel] = sha256_file(p)
    files = {
        p.relative_to(blind).as_posix(): sha256_file(p)
        for p in sorted(blind.rglob("*"))
        if p.is_file() and p.name != "SEALED_MANIFEST.json"
    }
    rec = {
        "schema": "A029-MEGA-SEAL-2.0",
        "code_tree": code,
        "config_sha256": sha256_file(config),
        "public_pairs_sha256": sha256_file(Path(catalog) / "pairs_public.csv"),
        "private_key_commitment_sha256": private_commitment,
        "parent_producer_sha256": EXPECTED_PARENT_PRODUCER_SHA256,
        "blind_files": files,
        "blind_tree_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
    }
    write_json(blind / "SEALED_MANIFEST.json", rec)
    return rec


def verify_blind(blind):
    blind = Path(blind)
    rec = json.loads((blind / "SEALED_MANIFEST.json").read_text(encoding="utf-8"))
    files = {
        p.relative_to(blind).as_posix(): sha256_file(p)
        for p in sorted(blind.rglob("*"))
        if p.is_file() and p.name != "SEALED_MANIFEST.json"
    }
    if files != rec["blind_files"]:
        raise RuntimeError("blind tree changed after seal")
    return rec


def reveal_summary(prepared, blind, revealed):
    verify_blind(blind)
    key = json.loads((Path(prepared) / "private" / "pair_key.json").read_text(encoding="utf-8"))
    mapping = {r["pair_id"]: r for r in key}
    cert = json.loads((Path(blind) / "02_certification" / "certification.json").read_text(encoding="utf-8"))["rows"]
    radial = json.loads((Path(blind) / "05_radial" / "radial.json").read_text(encoding="utf-8"))["rows"]
    rmap = {r["pair_id"]: r for r in radial}
    rows = []
    for c in cert:
        meta = mapping.get(c["pair_id"], {})
        rows.append({
            "pair_id": c["pair_id"],
            "carrier_id": meta.get("carrier_id"),
            "family": meta.get("family"),
            "profile": meta.get("profile"),
            "axial_ratio": meta.get("axial_ratio"),
            "core_fraction": meta.get("core_fraction"),
            "m": meta.get("m"),
            "n": meta.get("n"),
            "certification_status": c.get("status"),
            "detuning_power_exponent": c.get("detuning_power_exponent"),
            "Ck0_radial_rel_span": c.get("radial_curvature_rel_span_last3"),
            "radial_coherence": rmap.get(c["pair_id"], {}).get("median_radial_phase_resultant"),
        })
    groups = {}
    for r in rows:
        groups.setdefault((r.get("carrier_id"), r.get("family")), []).append(r)
    summary = []
    for (carrier, fam), rr in groups.items():
        summary.append({
            "carrier_id": carrier,
            "family": fam,
            "n_cases": len(rr),
            "n_certified": sum(x.get("certification_status") == "PASS" for x in rr),
            "interpretation": "discovery grouping only; certification does not establish a topological invariant",
        })
    write_csv(Path(revealed) / "revealed_case_map.csv", rows)
    write_json(Path(revealed) / "topology_grouping.json", {"status": "DISCOVERY_ONLY_TOPOLOGY_GROUPING", "groups": summary})
    return {"n_revealed_cases": len(rows), "n_groups": len(summary)}


def package_outputs(out_dir):
    out = Path(out_dir)
    parent = out.parent
    stem = out.name

    def zmake(path, items):
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for item in items:
                item = Path(item)
                if not item.exists():
                    continue
                for p in ([item] if item.is_file() else sorted(item.rglob("*"))):
                    if p.is_file():
                        z.write(p, p.relative_to(out.parent))

    blind_zip = parent / f"{stem}_BLIND.zip"
    revealed_zip = parent / f"{stem}_REVEALED.zip"
    full_zip = parent / f"{stem}.zip"
    zmake(blind_zip, [out / "blind"])
    zmake(revealed_zip, [out / "blind", out / "revealed"])
    zmake(full_zip, [out / "blind", out / "revealed", out / "RUN_REPORT.json"])
    return {"blind_zip": str(blind_zip), "revealed_zip": str(revealed_zip), "full_zip": str(full_zip)}


def run_mega(project_root, config_path, out_dir, *, limit=None, diagnostic_python=False, do_reveal=True):
    root = Path(project_root).resolve()
    config_path = Path(config_path).resolve()
    out = Path(out_dir).resolve()
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    blind = out / "blind"
    revealed = out / "revealed"
    prepared = out / "_private_prepared"
    blind.mkdir(parents=True)
    revealed.mkdir(parents=True)

    parent = _parent_integrity(root)
    if parent.get("status") != "PASS":
        write_json(blind / "00_PARENT_INTEGRITY.json", parent)
        raise RuntimeError(f"v0.6 parent integrity failed: {parent}")

    backend = backend_name()
    native = backend == "cpp-pybind11"
    full_campaign = limit is None
    scientific = bool(native and full_campaign and not diagnostic_python)
    if bool(cfg.get("require_native", True)) and not native and not diagnostic_python:
        raise RuntimeError("native cpp-pybind11 backend required; use --diagnostic-python only for explicitly non-certifying runs")
    cert_class = "SCIENTIFIC_NATIVE_FULL" if scientific else (
        "DIAGNOSTIC_LIMITED" if limit is not None else "DIAGNOSTIC_PYTHON_FALLBACK"
    )
    pre = {
        "schema": SCHEMA,
        "backend": backend,
        "certification_class": cert_class,
        "config_sha256": sha256_file(config_path),
        "limit": limit,
        "parent_integrity": parent,
    }
    write_json(blind / "00_PARENT_INTEGRITY.json", parent)
    write_json(blind / "00_PREFLIGHT.json", pre)

    prep = prepare(root, prepared, config_path)
    catalog = prepared / "blind_catalog"
    private_commit = prep.get("private_key_commitment_sha256")
    write_json(blind / "00_PREPARE_PUBLIC_SUMMARY.json", prep)

    s1 = stage01_kernel_campaign(catalog, blind, cfg, limit)
    s2 = stage02_certification(catalog, blind, cfg, s1, limit, allow_adaptive_extension=native)
    s3 = stage03_amplitude_phase(root, blind, cfg, s2)
    s4 = stage04_cross_chain(root, blind, cfg, s2, s3)
    s5 = stage05_radial(blind, cfg, s2)
    s6 = stage06_transformations(catalog, blind, cfg, s2, limit)
    s7 = stage07_attosecond(root, blind, cfg, s4)

    if s2["n_pass"] == 0:
        overall = "NO_CURVATURE_CERTIFIED"
    elif s3["n_pass"] == 0:
        overall = "CURVATURE_CERTIFIED__RAW_AMPLITUDE_PHASE_PENDING"
    elif s4["n_pass"] == 0:
        overall = "AMPLITUDE_PHASE_READY__PHYSICAL_REFERENCE_SCALE_OR_QGI_PENDING"
    elif s7.get("status") != "READY" or s7.get("n_pass", 0) == 0:
        overall = "SPECIFIC_ACTION_PHASE_READY__ATTOS_MAPPING_PENDING"
    else:
        overall = "END_TO_END_FORWARD_PREDICTION_READY"
    if not scientific:
        overall = "DIAGNOSTIC__" + overall

    pipe = {
        "schema": SCHEMA,
        "overall": overall,
        "certification_class": cert_class,
        "stages": {
            "00": {"status": "PASS", "backend": backend, "parent_integrity": parent["status"]},
            "01": {k: v for k, v in s1.items() if k != "rows"},
            "02": {k: v for k, v in s2.items() if k != "rows"},
            "03": {k: v for k, v in s3.items() if k != "rows"},
            "04": {k: v for k, v in s4.items() if k != "rows"},
            "05": {"status": s5["status"]},
            "06": {"status": s6["status"]},
            "07": {k: v for k, v in s7.items() if k != "rows"},
        },
    }
    write_json(blind / "PIPELINE_STATUS.json", pipe)
    seal_blind(root, blind, catalog, config_path, private_commit)

    rev = None
    if do_reveal:
        rev = reveal_summary(prepared, blind, revealed)

    report = {
        "pipeline": pipe,
        "seal_sha256": sha256_file(blind / "SEALED_MANIFEST.json"),
        "reveal_summary": rev,
        "important_boundaries": [
            "v0.6 sst_lagrangian.py is hash-guarded and not overwritten by v0.7.0.",
            "Finite K_l(Delta) is a symmetric finite-difference diagnostic and must vanish as O(delta_k^2).",
            "The primary certified local object is Richardson-extrapolated C_k = d^2 L/d(k_hat)^2; C_k is not itself a physical action.",
            "A real action requires independently measured complex amplitude a(0)=epsilon*exp(i phase0), a clean SI scale, and an independently derived physical delta_k_hat.",
            "A042/QGI supplies the action-to-phase denominator only; it is not used to fit the A029 numerator.",
            "Attosecond forwarding is NOT_RUN unless a source-hash-linked physical mapping matrix is supplied with zero fitted phase parameters.",
        ],
    }
    write_json(out / "RUN_REPORT.json", report)
    packs = package_outputs(out)
    report["packages"] = packs
    write_json(out / "RUN_REPORT.json", report)
    # Rebuild once so the full archive contains the final RUN_REPORT with package paths.
    package_outputs(out)
    return report
