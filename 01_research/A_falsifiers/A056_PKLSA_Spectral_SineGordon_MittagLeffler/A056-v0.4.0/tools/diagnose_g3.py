from __future__ import annotations

"""Read-only post-hoc diagnostics for A056-v0.4.0 Gate 3 model competition.

This tool intentionally has *no decision authority*.  It reuses the frozen v0.4.0
science functions and configuration to expose the model-comparison quantities that
were already computed internally before the fail-closed G3 decision.  It does not
modify provider inputs, gate ledgers, output manifests, reveal state, thresholds, or
the frozen protocol.

Holdout quantities are included only as post-hoc diagnostics.  When canonical G4 was
NOT_RUN_PREREQUISITE they MUST NOT be promoted to G4 evidence.
"""

from pathlib import Path
import argparse
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from a056_science.io import discover_cases, uniformity
from a056_science.numeric import phase_features
from a056_science.spectral import spectral_qualification, derived_ringdown
from a056_science.models import phase_model_competition, ringdown_competition
from a056_science.util import sha256_file


SCHEMA = "A056-G3-DIAGNOSTIC-READONLY-1"


def _jsonable(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _phase_payload(pm, cfg):
    best = min(pm, key=lambda k: pm[k]["discovery_bic"])
    sg = pm["SG"]
    condition_pass = bool(sg["design_condition"] <= cfg["design_condition_max"])
    delta_bic_pass = bool(sg["delta_bic_vs_best"] >= cfg["delta_bic_min"])
    coefficient_pass = bool(sg["physical_coefficients"])
    discovery_pass = bool(coefficient_pass and condition_pass and delta_bic_pass)
    holdout_ratio_pass = bool(sg["nrmse_ratio_vs_best"] <= cfg["nrmse_ratio_max"])
    holdout_abs_pass = bool(sg["confirmation_nrmse"] <= cfg.get("confirmation_nrmse_max", float("inf")))
    posthoc_confirmation_pass = bool(discovery_pass and holdout_ratio_pass and holdout_abs_pass)
    return {
        "best_discovery_model": best,
        "models": _jsonable(pm),
        "sg_candidate": {
            "delta_bic_vs_best": float(sg["delta_bic_vs_best"]),
            "coef": [float(x) for x in sg["coef"]],
            "a": float(sg["coef"][0]),
            "b": float(sg["coef"][1]),
            "design_condition": float(sg["design_condition"]),
            "physical_coefficients": coefficient_pass,
            "physical_coefficients_pass": coefficient_pass,
            "design_condition_pass": condition_pass,
            "delta_bic_pass": delta_bic_pass,
            "discovery_pass_without_g2": discovery_pass,
            "posthoc_holdout_nrmse": float(sg["confirmation_nrmse"]),
            "posthoc_holdout_nrmse_ratio_vs_best": float(sg["nrmse_ratio_vs_best"]),
            "posthoc_holdout_ratio_pass": holdout_ratio_pass,
            "posthoc_holdout_absolute_pass": holdout_abs_pass,
            "posthoc_confirmation_pass_without_g2": posthoc_confirmation_pass,
        },
    }


def _memory_payload(rm, cfg):
    best = min(rm, key=lambda k: rm[k]["bic"])
    ml = rm["ML"]
    alo, ahi = cfg["alpha_support_bounds"]
    delta_bic_pass = bool(ml["delta_bic_vs_best"] >= cfg["delta_bic_min"])
    alpha_support_pass = bool(float(alo) < ml["alpha"] < float(ahi))
    discovery_pass = bool(delta_bic_pass and alpha_support_pass)
    holdout_ratio_pass = bool(ml["nrmse_ratio_vs_best"] <= cfg["nrmse_ratio_max"])
    holdout_abs_pass = bool(ml["holdout_nrmse"] <= cfg.get("confirmation_nrmse_max", float("inf")))
    posthoc_confirmation_pass = bool(discovery_pass and holdout_ratio_pass and holdout_abs_pass)
    return {
        "best_discovery_model": best,
        "models": _jsonable(rm),
        "ml_candidate": {
            "delta_bic_vs_best": float(ml["delta_bic_vs_best"]),
            "alpha": float(ml["alpha"]),
            "tau": float(ml["tau"]),
            "alpha_support": [float(alo), float(ahi)],
            "alpha_support_pass": alpha_support_pass,
            "delta_bic_pass": delta_bic_pass,
            "discovery_pass_without_g2": discovery_pass,
            "posthoc_holdout_nrmse": float(ml["holdout_nrmse"]),
            "posthoc_holdout_nrmse_ratio_vs_best": float(ml["nrmse_ratio_vs_best"]),
            "posthoc_holdout_ratio_pass": holdout_ratio_pass,
            "posthoc_holdout_absolute_pass": holdout_abs_pass,
            "posthoc_confirmation_pass_without_g2": posthoc_confirmation_pass,
        },
    }


def diagnose_case(case, cfg):
    meta = case["meta"]
    t, s, phi = case["t"], case["s"], case["phi"]
    boundary = meta.get("boundary", "periodic")
    t_rel, dt = uniformity(t)
    s_rel, ds = uniformity(s)

    sm, q, _ = spectral_qualification(phi, cfg["spectral"], cfg["phase"]["discovery_fraction"])
    y, ss, ph = phase_features(phi, dt, ds, boundary, "python")
    pm = phase_model_competition(y, ss, ph, cfg["phase"]["discovery_fraction"])
    phase = _phase_payload(pm, cfg["phase"])

    ringdown_source = "provided"
    if case["ringdown"] is not None:
        rt = case["ringdown_t"] if case["ringdown_t"] is not None else t[: len(case["ringdown"])]
        rv = case["ringdown"]
    else:
        rt, rv = derived_ringdown(t, q)
        ringdown_source = "derived_pod_energy"

    memory = None
    ringdown_error = None
    try:
        rm, _, _ = ringdown_competition(rt, rv, cfg["ringdown"]["train_fraction"])
        memory = _memory_payload(rm, cfg["ringdown"])
    except Exception as exc:  # diagnostic must preserve the exact numerical failure
        ringdown_error = f"{type(exc).__name__}: {exc}"

    g2_pass = bool(sm["pass"])
    phase_discovery = bool(g2_pass and phase["sg_candidate"]["discovery_pass_without_g2"])
    memory_discovery = bool(g2_pass and memory is not None and memory["ml_candidate"]["discovery_pass_without_g2"])

    return {
        "opaque_id": meta.get("opaque_id", case["path"].stem),
        "input_sha256": case["sha256"],
        "metadata_sha256": case["meta_sha256"],
        "nt": int(len(t)),
        "ns": int(len(s)),
        "boundary": boundary,
        "t_uniform_rel": float(t_rel),
        "s_uniform_rel": float(s_rel),
        "g2": {
            "method": sm["method"],
            "pass": g2_pass,
            "blocking": _jsonable(sm["blocking"]),
            "legacy_raw_phase_pod_diagnostic": _jsonable(sm["legacy_raw_phase_pod_diagnostic"]),
        },
        "phase": phase,
        "memory": memory,
        "ringdown_source": ringdown_source,
        "ringdown_error": ringdown_error,
        "frozen_g3_reconstruction": {
            "phase_discovery_pass": phase_discovery,
            "memory_discovery_pass": memory_discovery,
            "any_candidate_pass": bool(phase_discovery or memory_discovery),
        },
        "posthoc_warning": "Holdout metrics are diagnostic only; this tool cannot retroactively execute or close G4.",
    }


def _flat_row(case):
    p = case["phase"]
    m = case["memory"]
    pm = p["models"]
    ml = m["ml_candidate"] if m else {}
    rm = m["models"] if m else {}
    sg = p["sg_candidate"]
    return {
        "opaque_id": case["opaque_id"],
        "g2_pass": case["g2"]["pass"],
        "phase_best_model": p["best_discovery_model"],
        "W_bic": pm["W"]["discovery_bic"],
        "KG_bic": pm["KG"]["discovery_bic"],
        "DUFFING_bic": pm["DUFFING"]["discovery_bic"],
        "SG_bic": pm["SG"]["discovery_bic"],
        "SG_delta_bic": sg["delta_bic_vs_best"],
        "SG_a": sg["a"],
        "SG_b": sg["b"],
        "SG_design_condition": sg["design_condition"],
        "SG_physical_coefficients": sg["physical_coefficients"],
        "phase_discovery_pass": case["frozen_g3_reconstruction"]["phase_discovery_pass"],
        "phase_posthoc_holdout_nrmse": sg["posthoc_holdout_nrmse"],
        "phase_posthoc_holdout_ratio": sg["posthoc_holdout_nrmse_ratio_vs_best"],
        "ringdown_source": case["ringdown_source"],
        "ringdown_best_model": m["best_discovery_model"] if m else "ERROR",
        "EXP_bic": rm.get("EXP", {}).get("bic"),
        "STRETCHED_bic": rm.get("STRETCHED", {}).get("bic"),
        "BIEXP_bic": rm.get("BIEXP", {}).get("bic"),
        "ML_bic": rm.get("ML", {}).get("bic"),
        "ML_delta_bic": ml.get("delta_bic_vs_best"),
        "ML_alpha": ml.get("alpha"),
        "ML_tau": ml.get("tau"),
        "memory_discovery_pass": case["frozen_g3_reconstruction"]["memory_discovery_pass"],
        "memory_posthoc_holdout_nrmse": ml.get("posthoc_holdout_nrmse"),
        "memory_posthoc_holdout_ratio": ml.get("posthoc_holdout_nrmse_ratio_vs_best"),
        "any_candidate_pass": case["frozen_g3_reconstruction"]["any_candidate_pass"],
        "ringdown_error": case["ringdown_error"],
    }


def main():
    ap = argparse.ArgumentParser(description="Read-only A056-v0.4.0 G3 model-competition diagnostic.")
    ap.add_argument("--input-dir", default="data/runtime_e010_filament_v040_m4")
    ap.add_argument("--config", default="configs/e010_real_score.json")
    ap.add_argument("--output", default="A056_G3_DIAGNOSTICS_READONLY.json")
    ap.add_argument("--csv-output", default="A056_G3_DIAGNOSTICS_READONLY.csv")
    args = ap.parse_args()

    root = ROOT
    inp = Path(args.input_dir)
    if not inp.is_absolute():
        inp = root / inp
    cp = Path(args.config)
    if not cp.is_absolute():
        cp = root / cp
    out = Path(args.output)
    if not out.is_absolute():
        out = root / out
    csv_out = Path(args.csv_output)
    if not csv_out.is_absolute():
        csv_out = root / csv_out

    if not inp.is_dir():
        raise FileNotFoundError(f"input directory not found: {inp}")
    cfg = json.loads(cp.read_text(encoding="utf-8"))
    cases = discover_cases(inp)
    if not cases:
        raise RuntimeError(f"no provider .npz cases found in {inp}")

    rows = [diagnose_case(case, cfg) for case in cases]
    payload = {
        "schema": SCHEMA,
        "a056_version": "v0.4.0",
        "decision_authority": "NONE_READ_ONLY_POSTHOC",
        "purpose": "Expose frozen G3 model-comparison margins without changing the canonical v0.4.0 gate result.",
        "input_dir": str(inp),
        "config": str(cp),
        "config_sha256": sha256_file(cp),
        "thresholds": {
            "phase": _jsonable(cfg["phase"]),
            "ringdown": _jsonable(cfg["ringdown"]),
            "spectral": _jsonable(cfg["spectral"]),
        },
        "case_count": len(rows),
        "reconstructed_phase_discovery_pass_count": int(sum(r["frozen_g3_reconstruction"]["phase_discovery_pass"] for r in rows)),
        "reconstructed_memory_discovery_pass_count": int(sum(r["frozen_g3_reconstruction"]["memory_discovery_pass"] for r in rows)),
        "reconstructed_any_candidate_pass_count": int(sum(r["frozen_g3_reconstruction"]["any_candidate_pass"] for r in rows)),
        "canonical_status_note": "This diagnostic does not alter G3. If the canonical ledger recorded G3=FAIL, it remains FAIL.",
        "g4_status_note": "Post-hoc holdout values are displayed for diagnosis only. They do not constitute a canonical G4 run when G4 was NOT_RUN_PREREQUISITE.",
        "cases": rows,
    }

    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    flat = [_flat_row(r) for r in rows]
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
        w.writeheader(); w.writerows(flat)

    print(json.dumps({
        "schema": SCHEMA,
        "decision_authority": payload["decision_authority"],
        "case_count": len(rows),
        "phase_discovery_pass_count": payload["reconstructed_phase_discovery_pass_count"],
        "memory_discovery_pass_count": payload["reconstructed_memory_discovery_pass_count"],
        "any_candidate_pass_count": payload["reconstructed_any_candidate_pass_count"],
        "json": str(out),
        "csv": str(csv_out),
    }, indent=2))


if __name__ == "__main__":
    main()
