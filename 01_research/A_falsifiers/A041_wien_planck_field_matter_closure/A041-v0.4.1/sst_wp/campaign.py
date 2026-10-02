from __future__ import annotations
import argparse
import json
import math
import re
import traceback
from pathlib import Path
import numpy as np

from .common import load_json, dump_json, write_csv, nowstamp, sha256_file, geometry_sha256, relerr
from .geometry import load_geometry, normalize_components, discover
from .relative_equilibrium import fit_relative_equilibrium
from .perturb import perturbed, perturbed_along_mode, project_mode_to_normal
from .dynamics import evolve
from .modal import aligned_displacement, discover_pod_mode, dominant_frequency
from .energy import dimensionless_line_energy
from .native_ext import NATIVE_AVAILABLE
from .blind_guard import assert_blind_code_clean, assert_blind_config_clean


def _analysis_start(n, cfg):
    frac = float(cfg.get("matched_mode_transient_fraction", cfg.get("discovery_fraction", 0.4)))
    return min(max(0, int(round(n * frac))), max(0, n - 16))


def _mode_projection_coefficient(odd, mode_flat):
    m = np.asarray(mode_flat, float).reshape(-1)
    den = float(np.dot(m, m))
    if not np.isfinite(den) or den <= 1e-300:
        raise RuntimeError("invalid frozen mode norm")
    return np.asarray(odd, float) @ m / den


def discover_frozen_mode(X, offs, cfg):
    """Dedicated target-free broadband probe -> one frozen normal POD mode."""
    eps = float(cfg.get("mode_discovery_probe_amplitude", 0.002))
    qcfg = dict(cfg)
    qcfg["t_final"] = float(cfg.get("mode_discovery_t_final", cfg.get("t_final", 0.06)))
    qcfg["samples"] = int(cfg.get("mode_discovery_samples", cfg.get("samples", 192)))

    Xp = perturbed(X, offs, eps, +1)
    Xm = perturbed(X, offs, eps, -1)
    tp, sp, dp = evolve(Xp, offs, qcfg, qcfg["samples"], cfl_divisor=1.0)
    tm, sm, dm = evolve(Xm, offs, qcfg, qcfg["samples"], cfl_divisor=1.0)
    n = min(len(tp), len(tm), len(sp), len(sm))
    if n < 16:
        raise RuntimeError("insufficient discovery snapshots")
    odd = (aligned_displacement(sp[:n], X) - aligned_displacement(sm[:n], X)) / (2 * eps)
    phi_raw, pdiag = discover_pod_mode(
        odd,
        transient_fraction=float(cfg.get("mode_discovery_transient_fraction", 0.10)),
    )
    phi, ndiag = project_mode_to_normal(X, offs, phi_raw, normalize_rms=True)
    diag = {
        **pdiag,
        **ndiag,
        "probe_amplitude_hat": eps,
        "probe_t_final_hat": float(qcfg["t_final"]),
        "probe_mesh_cv_max_observed": max(float(dp["mesh_cv_max_observed"]), float(dm["mesh_cv_max_observed"])),
        "probe_adaptive_reparameterizations": int(dp["adaptive_reparameterizations"] + dm["adaptive_reparameterizations"]),
    }
    return phi, diag


def _frequency_window_resolved(fq, cfg, target_cycles=None):
    need = float(target_cycles if target_cycles is not None else cfg.get("gates", {}).get("min_cycles", 4.0))
    return bool(
        np.isfinite(float(fq.get("frequency", float("nan"))))
        and float(fq.get("frequency", 0.0)) > 0
        and not bool(fq.get("frequency_window_limited", True))
        and float(fq.get("cycles", 0.0)) >= need
    )


def _run_matched_pair(X, offs, mode_flat, eps, cfg, cfl_divisor, t_final, sample_count):
    Xp = perturbed_along_mode(X, offs, mode_flat, eps, +1)
    Xm = perturbed_along_mode(X, offs, mode_flat, eps, -1)
    qcfg = dict(cfg)
    qcfg["t_final"] = float(t_final)
    qcfg["samples"] = int(sample_count)
    tp, sp, dp = evolve(Xp, offs, qcfg, qcfg["samples"], cfl_divisor=cfl_divisor)
    tm, sm, dm = evolve(Xm, offs, qcfg, qcfg["samples"], cfl_divisor=cfl_divisor)
    n = min(len(tp), len(tm), len(sp), len(sm))
    if n < 16:
        raise RuntimeError("insufficient matched-mode snapshots")
    times = tp[:n]
    odd = (aligned_displacement(sp[:n], X) - aligned_displacement(sm[:n], X)) / (2 * float(eps))
    coef = _mode_projection_coefficient(odd, mode_flat)
    fq = dominant_frequency(times, coef, _analysis_start(n, cfg))
    return fq, dp, dm


def certify_frequency_horizon(X, offs, mode_flat, eps, cfg, cfl_divisor=1.0, auto=True, t_final_override=None):
    """Iteratively enlarge the target-free observation window until it resolves.

    A first non-zero FFT bin is never extrapolated into a period estimate.  Such
    a result simply doubles the dimensionless horizon, up to a preregistered cap.
    """
    baseT = float(cfg.get("t_final", 0.0))
    if baseT <= 0:
        raise RuntimeError("t_final must be positive")
    T = float(t_final_override if t_final_override is not None else baseT)
    base_samples = int(cfg.get("samples", 192))
    max_samples = int(cfg.get("max_frequency_samples", 2048))
    max_factor = float(cfg.get("max_frequency_horizon_factor", 32.0))
    max_rounds = int(cfg.get("max_frequency_extension_rounds", 6))
    growth = float(cfg.get("frequency_horizon_growth", 2.0))
    target_cycles = float(cfg.get("target_frequency_cycles", 6.0))

    history = []
    final = None
    final_dp = final_dm = None
    for round_index in range(max_rounds + 1):
        factor = T / baseT
        samples = min(max_samples, max(base_samples, int(math.ceil(base_samples * factor))))
        fq, dp, dm = _run_matched_pair(
            X, offs, mode_flat, eps, cfg, cfl_divisor, T, samples
        )
        history.append({
            "round": int(round_index),
            "t_final_hat": float(T),
            "horizon_factor": float(factor),
            "samples": int(samples),
            "frequency_hat": float(fq.get("frequency", float("nan"))),
            "fft_bin_index": int(fq.get("fft_bin_index", -1)),
            "cycles": float(fq.get("cycles", 0.0)),
            "window_limited": bool(fq.get("frequency_window_limited", True)),
        })
        final, final_dp, final_dm = fq, dp, dm
        if _frequency_window_resolved(fq, cfg, target_cycles=target_cycles):
            status = "RESOLVED"
            break
        if not auto:
            status = "UNRESOLVED_FIXED_HORIZON"
            break
        if round_index >= max_rounds or factor >= max_factor * (1 - 1e-12):
            status = "UNRESOLVED_HORIZON_CAP"
            break

        if bool(fq.get("frequency_window_limited", True)):
            nextT = T * max(1.25, growth)
        else:
            cyc = max(float(fq.get("cycles", 0.0)), 1e-6)
            need = max(1.25, 1.15 * target_cycles / cyc)
            nextT = T * min(max(growth, 1.25), max(need, 1.25))
        nextT = min(baseT * max_factor, nextT)
        if nextT <= T * (1 + 1e-12):
            status = "UNRESOLVED_HORIZON_CAP"
            break
        T = nextT
    else:
        status = "UNRESOLVED_HORIZON_CAP"

    final = dict(final or {})
    final.update({
        "frequency_certification_status": status,
        "frequency_certified": bool(status == "RESOLVED"),
        "effective_t_final": float(T),
        "frequency_horizon_factor": float(T / baseT),
        "frequency_extension_rounds": int(max(0, len(history) - 1)),
        "frequency_certification_history": history,
    })
    return final, final_dp, final_dm


def _blank_error_row(eps, code):
    return {
        "row_status": "ERROR",
        "error_code": str(code),
        "amplitude_hat": float(eps),
        "delta_E_hat": "",
        "base_energy_hat": "",
        "delta_E_over_abs_base": "",
        "energy_signal_valid": False,
        "frequency_hat": "",
        "omega_hat": "",
        "spectral_power": "",
        "cycles": "",
        "period_cv": "",
        "harmonic_r2": "",
        "fft_bin_index": "",
        "frequency_window_limited": True,
        "frequency_certified": False,
        "frequency_certification_status": "ERROR",
        "frequency_extension_rounds": "",
        "frequency_horizon_factor": "",
        "effective_t_final_hat": "",
        "mesh_cv_plus": "",
        "mesh_cv_minus": "",
        "mesh_edge_ratio_plus": "",
        "mesh_edge_ratio_minus": "",
        "adaptive_reparams_plus": "",
        "adaptive_reparams_minus": "",
        "dt_hat_min": "",
        "dt_hat_max": "",
        "n_steps": "",
    }


def run_case(path, cfg, resolution, eps_list):
    comps = load_geometry(path)
    X, offs = normalize_components(comps, resolution)

    gamma_hat = float(cfg.get("gamma_dimensionless", 1.0))
    if gamma_hat != 1.0:
        raise RuntimeError("v0.4.1 strict blind action campaign requires gamma_dimensionless = 1")

    reinfo = fit_relative_equilibrium(
        X, offs, gamma_hat, cfg["core_fraction"], cfg.get("require_native", False)
    )
    E0_hat, _ = dimensionless_line_energy(
        X, offs, cfg["core_fraction"], cfg.get("require_native", False)
    )

    errors = []
    try:
        frozen_mode, mode_diag = discover_frozen_mode(X, offs, cfg)
        mode_valid = bool(
            float(mode_diag["mode_normal_fraction"])
            >= float(cfg.get("gates", {}).get("min_mode_normal_fraction", 0.50))
        )
    except Exception as e:
        errors.append({"stage": "mode_discovery", "error": repr(e), "traceback": traceback.format_exc()[-3000:]})
        rows = [_blank_error_row(eps, "MODE_DISCOVERY_ERROR") for eps in eps_list]
        for row in rows:
            row.update({
                "mode_discovery_valid": False,
                "mode_normal_fraction": "",
                "mode_pod_power_fraction": "",
                "epsilon_RE": reinfo["epsilon_RE_perp"],
                "epsilon_RE_perp": reinfo["epsilon_RE_perp"],
                "epsilon_RE_full": reinfo["epsilon_RE_full"],
                "normal_velocity_fraction": reinfo["normal_velocity_fraction"],
                "normalization_L_hat": 1.0,
                "normalization_Gamma_hat": 1.0,
                "core_fraction_hat": float(cfg["core_fraction"]),
            })
        return X, offs, reinfo, rows, {
            "frequency_hat_by_cfl_divisor": [],
            "shared_t_final_hat": None,
            "all_refinements_frequency_resolved": False,
            "highest_refinement_rel_change": None,
        }, {"valid": False}, errors

    first_eps = float(eps_list[0])
    cert = cert_dp = cert_dm = None
    try:
        cert, cert_dp, cert_dm = certify_frequency_horizon(
            X, offs, frozen_mode, first_eps, cfg, cfl_divisor=1.0, auto=True
        )
        shared_t_final = float(cert["effective_t_final"])
    except Exception as e:
        errors.append({"stage": "frequency_certification", "error": repr(e), "traceback": traceback.format_exc()[-3000:]})
        shared_t_final = float(cfg.get("t_final", 0.0))

    rows = []
    for eps in eps_list:
        eps = float(eps)
        try:
            Xp = perturbed_along_mode(X, offs, frozen_mode, eps, +1)
            Xm = perturbed_along_mode(X, offs, frozen_mode, eps, -1)
            Ep_hat, _ = dimensionless_line_energy(
                Xp, offs, cfg["core_fraction"], cfg.get("require_native", False)
            )
            Em_hat, _ = dimensionless_line_energy(
                Xm, offs, cfg["core_fraction"], cfg.get("require_native", False)
            )
            dE_hat = 0.5 * (Ep_hat + Em_hat) - E0_hat

            if cert is not None and abs(eps - first_eps) <= 1e-15:
                fq, dp, dm = cert, cert_dp, cert_dm
            else:
                fq, dp, dm = certify_frequency_horizon(
                    X, offs, frozen_mode, eps, cfg,
                    cfl_divisor=1.0,
                    auto=False,
                    t_final_override=shared_t_final,
                )
                fq["frequency_certification_status"] = (
                    "RESOLVED_SHARED_HORIZON"
                    if _frequency_window_resolved(fq, cfg, target_cycles=cfg.get("target_frequency_cycles", 6.0))
                    else "UNRESOLVED_SHARED_HORIZON"
                )
                fq["frequency_certified"] = bool(fq["frequency_certification_status"] == "RESOLVED_SHARED_HORIZON")

            row = {
                "row_status": "OK",
                "error_code": "",
                "amplitude_hat": eps,
                "delta_E_hat": dE_hat,
                "base_energy_hat": E0_hat,
                "delta_E_over_abs_base": dE_hat / max(abs(E0_hat), 1e-300),
                "energy_signal_valid": bool(np.isfinite(dE_hat) and dE_hat > 0),
                "frequency_hat": fq["frequency"],
                "omega_hat": fq["omega"],
                "spectral_power": fq["spectral_power"],
                "cycles": fq["cycles"],
                "period_cv": fq["period_cv"],
                "harmonic_r2": fq["harmonic_r2"],
                "fft_bin_index": fq.get("fft_bin_index", -1),
                "fft_bin_width_hat": fq.get("fft_bin_width", ""),
                "frequency_window_limited": fq.get("frequency_window_limited", True),
                "frequency_certified": bool(fq.get("frequency_certified", False)),
                "frequency_certification_status": fq.get("frequency_certification_status", "UNRESOLVED"),
                "frequency_extension_rounds": fq.get("frequency_extension_rounds", 0),
                "frequency_horizon_factor": fq.get("frequency_horizon_factor", shared_t_final / max(float(cfg.get("t_final", 1.0)), 1e-300)),
                "effective_t_final_hat": fq.get("effective_t_final", shared_t_final),
                "mode_discovery_valid": bool(mode_valid),
                "mode_normal_fraction": mode_diag["mode_normal_fraction"],
                "mode_pod_power_fraction": mode_diag["pod_power_fraction"],
                "mode_probe_mesh_cv": mode_diag["probe_mesh_cv_max_observed"],
                "epsilon_RE": reinfo["epsilon_RE_perp"],
                "epsilon_RE_perp": reinfo["epsilon_RE_perp"],
                "epsilon_RE_full": reinfo["epsilon_RE_full"],
                "normal_velocity_fraction": reinfo["normal_velocity_fraction"],
                "mesh_cv_plus": dp["mesh_cv_max_observed"],
                "mesh_cv_minus": dm["mesh_cv_max_observed"],
                "mesh_sample_cv_plus": dp["sample_mesh_max_cv"],
                "mesh_sample_cv_minus": dm["sample_mesh_max_cv"],
                "mesh_edge_ratio_plus": dp["mesh_edge_ratio_max_observed"],
                "mesh_edge_ratio_minus": dm["mesh_edge_ratio_max_observed"],
                "adaptive_reparams_plus": dp["adaptive_reparameterizations"],
                "adaptive_reparams_minus": dm["adaptive_reparameterizations"],
                "dt_hat_min": min(float(dp["dt_min"]), float(dm["dt_min"])),
                "dt_hat_max": max(float(dp["dt_max"]), float(dm["dt_max"])),
                "n_steps": max(int(dp["n_steps"]), int(dm["n_steps"])),
                "max_substeps_budget": max(int(dp["max_substeps_budget"]), int(dm["max_substeps_budget"])),
                "normalization_L_hat": 1.0,
                "normalization_Gamma_hat": 1.0,
                "core_fraction_hat": float(cfg["core_fraction"]),
                "matched_energy_frequency_same_frozen_mode": True,
            }
            rows.append(row)
        except Exception as e:
            errors.append({
                "stage": "amplitude_run",
                "amplitude_hat": eps,
                "error": repr(e),
                "traceback": traceback.format_exc()[-3000:],
            })
            row = _blank_error_row(eps, type(e).__name__)
            row.update({
                "mode_discovery_valid": bool(mode_valid),
                "mode_normal_fraction": mode_diag["mode_normal_fraction"],
                "mode_pod_power_fraction": mode_diag["pod_power_fraction"],
                "epsilon_RE": reinfo["epsilon_RE_perp"],
                "epsilon_RE_perp": reinfo["epsilon_RE_perp"],
                "epsilon_RE_full": reinfo["epsilon_RE_full"],
                "normal_velocity_fraction": reinfo["normal_velocity_fraction"],
                "normalization_L_hat": 1.0,
                "normalization_Gamma_hat": 1.0,
                "core_fraction_hat": float(cfg["core_fraction"]),
                "matched_energy_frequency_same_frozen_mode": True,
            })
            rows.append(row)

    # Temporal convergence: same frozen mode, same amplitude, same physical
    # dimensionless horizon.  Only CFL subdivision changes.
    factors = [float(x) for x in cfg.get("temporal_refinement_factors", [1, 2])]
    freqs = []
    if cert is not None:
        freqs.append({
            "cfl_divisor": 1.0,
            "frequency_hat": float(cert.get("frequency", float("nan"))),
            "cycles": float(cert.get("cycles", 0.0)),
            "frequency_window_limited": bool(cert.get("frequency_window_limited", True)),
            "frequency_certified": bool(cert.get("frequency_certified", False)),
            "effective_t_final_hat": float(shared_t_final),
        })
    try:
        for fac in factors:
            if abs(fac - 1.0) <= 1e-12 and cert is not None:
                continue
            fq, _, _ = certify_frequency_horizon(
                X, offs, frozen_mode, first_eps, cfg,
                cfl_divisor=fac,
                auto=False,
                t_final_override=shared_t_final,
            )
            freqs.append({
                "cfl_divisor": fac,
                "frequency_hat": float(fq.get("frequency", float("nan"))),
                "cycles": float(fq.get("cycles", 0.0)),
                "frequency_window_limited": bool(fq.get("frequency_window_limited", True)),
                "frequency_certified": _frequency_window_resolved(
                    fq, cfg, target_cycles=cfg.get("target_frequency_cycles", 6.0)
                ),
                "effective_t_final_hat": float(shared_t_final),
            })
    except Exception as e:
        errors.append({"stage": "temporal_convergence", "error": repr(e), "traceback": traceback.format_exc()[-3000:]})

    min_cycles = float(cfg.get("gates", {}).get("min_cycles", 4.0))
    temporal_resolved = bool(freqs) and len(freqs) >= len(set(factors)) and all(
        (not q["frequency_window_limited"])
        and q["cycles"] >= min_cycles
        and np.isfinite(q["frequency_hat"])
        and q["frequency_hat"] > 0
        for q in freqs
    )
    temporal_rel = None
    ordered_freqs = sorted(freqs, key=lambda q: q["cfl_divisor"])
    if temporal_resolved and len(ordered_freqs) >= 2:
        temporal_rel = relerr(ordered_freqs[-1]["frequency_hat"], ordered_freqs[-2]["frequency_hat"])

    for row in rows:
        row["temporal_frequency_rel_change"] = temporal_rel if temporal_rel is not None else ""
        row["temporal_frequency_resolved"] = bool(temporal_resolved)

    tconv = {
        "frequency_hat_by_cfl_divisor": ordered_freqs,
        "shared_t_final_hat": float(shared_t_final),
        "all_refinements_frequency_resolved": bool(temporal_resolved),
        "highest_refinement_rel_change": temporal_rel,
    }
    mode_public = {
        "valid": bool(mode_valid),
        "normal_fraction": float(mode_diag["mode_normal_fraction"]),
        "pod_power_fraction": float(mode_diag["pod_power_fraction"]),
        "probe_t_final_hat": float(mode_diag["probe_t_final_hat"]),
    }
    return X, offs, reinfo, rows, tconv, mode_public, errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dataset")
    p.add_argument("--config", default="config/basic.json")
    p.add_argument("--out", default=None)
    p.add_argument("--selection", default=None, help="Private prequalified selection JSON; identities never enter blind scorer.")
    p.add_argument("--funnel-public", default=None)
    p.add_argument("--gpu-parity", default=None)
    a = p.parse_args()

    assert_blind_code_clean(Path(__file__).resolve().parents[1])
    cfg = load_json(a.config)
    assert_blind_config_clean(cfg)

    required_preflight = bool(cfg.get("require_funnel_preflight", True))
    preflight = {
        "required": required_preflight,
        "pass": (not required_preflight),
        "status": ("NOT_REQUIRED_VALIDATION" if not required_preflight else "MISSING"),
    }
    if a.funnel_public:
        fp = load_json(a.funnel_public)
        s1 = fp.get("stage1", {}); s2 = fp.get("stage2", {})
        funnel_ok = bool(
            int(fp.get("atlas_candidate_count", -1)) == int(cfg.get("funnel_expected_candidates", 2352))
            and int(fp.get("atlas_family_count", -1)) == int(cfg.get("funnel_expected_families", 49))
            and int(s1.get("survivor_count", -1)) == int(cfg.get("funnel_expected_families",49))*int(cfg.get("funnel_stage1_per_family",8))
            and int(s2.get("survivor_count", -1)) == int(cfg.get("funnel_expected_families",49))*int(cfg.get("funnel_stage2_per_family",2))
            and not bool(fp.get("selection_target_used", True))
        )
        backend = str(fp.get("backend_requested", ""))
        parity_required = backend == "sycl"
        parity_ok = True
        parity_meta = None
        if parity_required:
            if not a.gpu_parity:
                parity_ok = False
            else:
                parity_meta = load_json(a.gpu_parity)
                parity_ok = bool(parity_meta.get("pass", False))
        preflight = {
            "required": bool(cfg.get("require_funnel_preflight", True)),
            "pass": bool(funnel_ok and parity_ok),
            "funnel_ok": funnel_ok,
            "gpu_parity_required": parity_required,
            "gpu_parity_ok": parity_ok,
            "screening_backend": backend,
            "atlas_candidate_count": int(fp.get("atlas_candidate_count", -1)),
            "stage1_survivor_count": int(s1.get("survivor_count", -1)),
            "stage2_survivor_count": int(s2.get("survivor_count", -1)),
            "gpu_device_meta": s1.get("backend_meta", {}),
            "gpu_parity_summary": ({k: parity_meta.get(k) for k in ["candidate_count","max_relative_error","tolerance","pass"]} if parity_meta else None),
        }
    if preflight["required"] and not preflight["pass"]:
        raise SystemExit("FAIL CLOSED: PKLSA funnel/GPU parity preflight not certified")

    out = Path(a.out or f"Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs/basic_{nowstamp()}")
    out.mkdir(parents=True, exist_ok=True)
    files = discover(a.dataset)
    selection_meta = {}
    if a.selection:
        sel = load_json(a.selection)
        wanted = [Path(x["path"]).resolve() for x in sel.get("selected", [])]
        by_resolved = {f.resolve(): f for f in files}
        files = [by_resolved[w] for w in wanted if w in by_resolved]
        selection_meta = {str(Path(x["path"]).resolve()): x for x in sel.get("selected", [])}
    regex = cfg.get("source_regex")
    if regex:
        files = [f for f in files if re.search(regex, f.name, re.I)]
    files = files[: int(cfg.get("max_carriers", 6))]
    if not files:
        raise SystemExit("No candidate geometry files found")

    allrows = []
    public_cases = []
    private_cases = []
    expected = len(files) * len(cfg["resolution_ladder"]) * len(cfg["amplitudes"])

    for ci, f in enumerate(files):
        src_hash = sha256_file(f)
        for N in cfg["resolution_ladder"]:
            try:
                X, o, reinfo, rows, tconv, mode_public, case_errors = run_case(
                    f, cfg, int(N), cfg["amplitudes"]
                )
                geo_hash = geometry_sha256(X, o)
                for r in rows:
                    r.update({
                        "case_index": ci,
                        "source_name": f.name,
                        "source_path": str(f),
                        "source_sha256": src_hash,
                        "geometry_sha256": geo_hash,
                        "resolution_N": N,
                        "family_hint": f.stem,
                        "qualification_rank": selection_meta.get(str(f.resolve()), {}).get("qualification_rank", ""),
                        "qualification_score": selection_meta.get(str(f.resolve()), {}).get("qualification_score", ""),
                    })
                allrows += rows
                ok_rows = sum(str(r.get("row_status", "")).upper() == "OK" for r in rows)
                public_cases.append({
                    "case_index": ci,
                    "resolution_N": N,
                    "relative_equilibrium": reinfo,
                    "frozen_mode": mode_public,
                    "temporal_convergence": tconv,
                    "expected_rows": len(cfg["amplitudes"]),
                    "ok_rows": ok_rows,
                    "error_rows": len(rows) - ok_rows,
                    "status": "OK" if ok_rows == len(rows) else "PARTIAL",
                })
                private_cases.append({
                    "case_index": ci,
                    "source_name": f.name,
                    "source_path": str(f),
                    "source_sha256": src_hash,
                    "geometry_sha256": geo_hash,
                    "resolution_N": N,
                    "errors": case_errors,
                })
            except Exception as e:
                # Preserve coverage: emit one blindable error row per preregistered amplitude.
                err_rows = []
                for eps in cfg["amplitudes"]:
                    r = _blank_error_row(float(eps), "CASE_ERROR")
                    r.update({
                        "case_index": ci,
                        "source_name": f.name,
                        "source_path": str(f),
                        "source_sha256": src_hash,
                        "geometry_sha256": "",
                        "resolution_N": N,
                        "family_hint": f.stem,
                        "qualification_rank": selection_meta.get(str(f.resolve()), {}).get("qualification_rank", ""),
                        "qualification_score": selection_meta.get(str(f.resolve()), {}).get("qualification_score", ""),
                    })
                    err_rows.append(r)
                allrows += err_rows
                public_cases.append({
                    "case_index": ci,
                    "resolution_N": N,
                    "expected_rows": len(cfg["amplitudes"]),
                    "ok_rows": 0,
                    "error_rows": len(cfg["amplitudes"]),
                    "status": "ERROR",
                    "error_code": type(e).__name__,
                })
                private_cases.append({
                    "case_index": ci,
                    "source_name": f.name,
                    "source_path": str(f),
                    "source_sha256": src_hash,
                    "resolution_N": N,
                    "status": "ERROR",
                    "traceback": traceback.format_exc()[-3000:],
                })

    write_csv(out / "raw_observations.csv", allrows)
    ok_observations = sum(str(r.get("row_status", "")).upper() == "OK" for r in allrows)
    dump_json(out / "campaign.json", {
        "format": "SST-WP-CAMPAIGN-PUBLIC-4.0",
        "config": cfg,
        "native_available": NATIVE_AVAILABLE,
        "dataset_root_hash_hint": "identity withheld until reveal",
        "cases": public_cases,
        "selected_carrier_count": len(files),
        "expected_observations": int(expected),
        "observations": len(allrows),
        "ok_observations": int(ok_observations),
        "error_observations": int(len(allrows) - ok_observations),
        "coverage_complete": bool(len(allrows) == expected and ok_observations == expected),
        "blind_normalization": {
            "L_hat": 1.0,
            "Gamma_hat": 1.0,
            "SI_units_used": False,
            "SST_canonical_constants_used": False,
            "energy_definition": "E_hat = energy_sum/(8*pi)",
            "time_definition": "t_hat = Gamma*t/L^2 with L=Gamma=1",
            "action_definition": "matched frozen normal mode: J_hat = DeltaE_hat/f_hat or DeltaE_hat/omega_hat",
        },
        "topology_certified_by_this_package": False,
        "pklsa_funnel_preflight": preflight,
    })
    dump_json(out / "campaign_private.json", {
        "format": "SST-WP-CAMPAIGN-PRIVATE-4.0",
        "dataset": str(Path(a.dataset).resolve()),
        "cases": private_cases,
    })
    print(json.dumps({
        "out": str(out),
        "files": len(files),
        "expected_observations": expected,
        "observations": len(allrows),
        "ok_observations": ok_observations,
        "errors": len(allrows) - ok_observations,
        "native_available": NATIVE_AVAILABLE,
        "SST_canonical_constants_used": False,
        "SI_units_used": False,
    }, indent=2))


if __name__ == "__main__":
    main()
