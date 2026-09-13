"""Prediction-locked nested phase accounting and residual scoring."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from . import __version__
from .holonomy import forbid_double_counted_holonomy, holonomy_record
from .phase_contract import (
    carrier_derived_phase,
    classify_target_independence,
    classify_tau_independence,
    convention_bridge,
    identity_fields,
    signed_omega,
    wrap_phase,
)
from .table_io import write_json, write_parquet

SMALL_EXPORT_NAMES = (
    "PHASE_ACCOUNTING_CERTIFICATE.json",
    "PHASE_RESIDUAL_CERTIFICATE.json",
    "FROZEN_CASE_INVENTORY.json",
    "phase_decomposition_summary.parquet.json",
)

MISSING_CASES = "INDETERMINATE_MISSING_BASELINE_CASES"
NO_INDEPENDENT_PHASE = "INDETERMINATE_NO_INDEPENDENT_PHASE_TARGET"
NONINDEPENDENT_TAU = "INDETERMINATE_NONINDEPENDENT_RETURN_TIME"
NO_INDEPENDENT_EVENT = "INDETERMINATE_NO_INDEPENDENT_RETURN_EVENT"
INSUFFICIENT_CLUSTERS = "INDETERMINATE_INSUFFICIENT_CLUSTERS"
ACCOUNTING_OK = "ACCOUNTING_IDENTITY_CONFIRMED"
ACCOUNTING_FAIL = "ACCOUNTING_IDENTITY_FAILED"
PRED_MODELS = ("PRED_M0", "PRED_M1", "PRED_M2", "PRED_M3")
ACCOUNT_MODELS = ("ACCOUNT_M0", "ACCOUNT_M1", "ACCOUNT_M2", "ACCOUNT_M3")
DEFAULT_THRESHOLDS = {
    "skill_pass": 0.30,
    "ci_lower_min": 0.0,
    "median_abs_R_floor_rad": 0.35,
    "median_abs_R_sigma_factor": 2.0,
    "n_bootstrap": 2000,
    "bootstrap_seed": 20260913,
    "min_carriers": 2,
    "min_overlap": 0.10,
    "phase_uncertainty_max_rad": 0.35,
    "phase_uncertainty_source": "delay.wavepacket_return.phase_uncertainty_max_rad",
}


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def circular_mean(phis: Iterable[float]) -> float:
    z = np.exp(1j * np.asarray(list(phis), dtype=float))
    if z.size == 0:
        return float("nan")
    return float(np.angle(np.mean(z)))


def wrapped_residual(target: float, pred: float) -> float:
    return wrap_phase(float(target) - float(pred))


def crmse(residuals: Iterable[float]) -> float:
    r = np.asarray(list(residuals), dtype=float)
    if r.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean(r ** 2)))


def skill_score(crmse_m: float, crmse_m0: float) -> float:
    if not np.isfinite(crmse_m) or not np.isfinite(crmse_m0) or abs(crmse_m0) < 1e-30:
        return float("nan")
    return 1.0 - float(crmse_m) / float(crmse_m0)


def predict_nested(
    *,
    omega_adv_ref: float,
    omega_intr_ref: float,
    omega_adv_closed: float,
    omega_intr_closed: float,
    tau: float,
    phi_null: float,
) -> dict[str, float]:
    return {
        "PRED_M0": wrap_phase(phi_null),
        "PRED_M1": wrap_phase(-float(omega_adv_ref) * float(tau)),
        "PRED_M2": wrap_phase(-(float(omega_adv_ref) + float(omega_intr_ref)) * float(tau)),
        "PRED_M3": wrap_phase(-(float(omega_adv_closed) + float(omega_intr_closed)) * float(tau)),
    }


def account_nested(
    *,
    omega_adv_ref: float,
    omega_intr_ref: float,
    omega_adv_closed: float,
    omega_intr_closed: float,
    tau_synthetic: float,
    phi_null: float,
) -> dict[str, float]:
    pred = predict_nested(
        omega_adv_ref=omega_adv_ref,
        omega_intr_ref=omega_intr_ref,
        omega_adv_closed=omega_adv_closed,
        omega_intr_closed=omega_intr_closed,
        tau=tau_synthetic,
        phi_null=phi_null,
    )
    return {name.replace("PRED", "ACCOUNT"): val for name, val in pred.items()}


def phase_blind_return(
    t: np.ndarray,
    envelope: np.ndarray,
    *,
    window: tuple[float, float],
    tau_min: float,
    predicted_omega: float | None = None,
    predicted_vg: float | None = None,
    synthetic_wavepacket: bool = False,
) -> dict[str, Any]:
    if predicted_omega is not None or predicted_vg is not None or synthetic_wavepacket:
        return {
            "available": False,
            "reason": NONINDEPENDENT_TAU,
            "tau_return_independence": classify_tau_independence(
                predicted_omega_used=predicted_omega is not None,
                predicted_group_velocity_used=predicted_vg is not None,
                synthetic_wavepacket_used=synthetic_wavepacket,
                raw_trajectory=True,
            ),
        }
    t = np.asarray(t, dtype=float)
    env = np.asarray(envelope, dtype=float)
    lo, hi = window
    mask = (t >= lo) & (t <= hi) & (t > float(tau_min))
    if not np.any(mask):
        return {"available": False, "reason": NO_INDEPENDENT_EVENT}
    idx = int(np.flatnonzero(mask)[int(np.argmax(env[mask]))])
    ties = np.flatnonzero(mask & (env == env[idx]))
    idx = int(ties[0])
    return {
        "available": True,
        "tau_return_independent": float(t[idx]),
        "coherence": float(env[idx] / max(float(np.max(np.abs(env))), 1e-30)),
        "tau_return_independence": classify_tau_independence(
            predicted_omega_used=False,
            predicted_group_velocity_used=False,
            synthetic_wavepacket_used=False,
            raw_trajectory=True,
            search_window_source="protocol_fixed_or_training_only",
        ),
    }


def independent_return_phase(a0: complex, a_return: complex) -> float:
    return wrap_phase(float(np.angle(complex(a_return) * np.conj(complex(a0)))))


def reject_omega_demodulation(signal: np.ndarray, omega: float, t: np.ndarray) -> None:
    raise ValueError("predicted-omega demodulation is forbidden for an independent target")


def leave_one_carrier_folds(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = sorted({r["carrier_group_token"] for r in rows})
    folds = []
    for held in tokens:
        train = [r for r in rows if r["carrier_group_token"] != held]
        test = [r for r in rows if r["carrier_group_token"] == held]
        phi_null = circular_mean(r["phi_target_independent"] for r in train if r.get("phi_target_independent") is not None)
        folds.append({"held_out": held, "train_tokens": [r["carrier_group_token"] for r in train], "test": test, "phi_null": phi_null})
    return folds


def clustered_bootstrap(values_by_cluster: dict[str, list[float]], stat, *, n: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    keys = list(values_by_cluster)
    if not keys:
        return {"mean": float("nan"), "ci_lower": float("nan"), "ci_upper": float("nan")}
    samples = []
    for _ in range(int(n)):
        draw_keys = rng.choice(keys, size=len(keys), replace=True)
        drawn = [v for k in draw_keys for v in values_by_cluster[k]]
        samples.append(stat(drawn))
    arr = np.asarray(samples, dtype=float)
    return {
        "mean": float(np.nanmean(arr)),
        "ci_lower": float(np.nanpercentile(arr, 2.5)),
        "ci_upper": float(np.nanpercentile(arr, 97.5)),
    }


def independence_gates_pass(target: dict[str, Any], tau: dict[str, Any]) -> bool:
    ok_target = target.get("class") in {
        "fully_model_independent_time_domain",
        "independent_time_domain_given_frozen_spatial_mode",
    } and not target.get("predicted_omega_used_in_extraction") and not target.get("predicted_vg_used_in_extraction")
    if target.get("class") == "fully_model_independent_time_domain" and target.get("spatial_mode_basis_source") == "model_conditioned_frozen":
        ok_target = False
    ok_tau = tau.get("class") == "raw_trajectory_phase_blind" and not (
        tau.get("predicted_omega_used")
        or tau.get("predicted_group_velocity_used")
        or tau.get("synthetic_wavepacket_used")
        or tau.get("l_over_vg_used")
    )
    return bool(ok_target and ok_tau)


def score_models(rows: list[dict[str, Any]], thresholds: dict[str, Any]) -> dict[str, Any]:
    residuals = {name: [] for name in PRED_MODELS}
    by_cluster: dict[str, dict[str, list[float]]] = {name: {} for name in PRED_MODELS}
    for row in rows:
        token = row["carrier_group_token"]
        for name in PRED_MODELS:
            r = wrapped_residual(row["phi_target_independent"], row["predictions"][name])
            residuals[name].append(r)
            by_cluster[name].setdefault(token, []).append(r)
    crmses = {name: crmse(residuals[name]) for name in PRED_MODELS}
    skills = {name: skill_score(crmses[name], crmses["PRED_M0"]) for name in PRED_MODELS}
    med_abs = {name: float(np.median(np.abs(residuals[name]))) if residuals[name] else float("nan") for name in PRED_MODELS}
    n_boot = int(thresholds["n_bootstrap"])
    seed = int(thresholds["bootstrap_seed"])

    def skill_from(res_m, res_0):
        return skill_score(crmse(res_m), crmse(res_0))

    boot = {}
    for name in PRED_MODELS:
        keys = list(by_cluster[name])
        paired = {k: (by_cluster[name][k], by_cluster["PRED_M0"][k]) for k in keys}

        def stat(pairs, _name=name):
            rm = [v for a, _b in pairs for v in a]
            r0 = [v for _a, b in pairs for v in b]
            return skill_from(rm, r0)

        rng = np.random.default_rng(seed)
        samples = []
        if keys:
            items = list(paired.values())
            for _ in range(n_boot):
                draw = [items[i] for i in rng.integers(0, len(items), size=len(items))]
                samples.append(stat(draw))
        arr = np.asarray(samples, dtype=float) if samples else np.array([np.nan])
        boot[name] = {
            "mean": float(np.nanmean(arr)),
            "ci_lower": float(np.nanpercentile(arr, 2.5)),
            "ci_upper": float(np.nanpercentile(arr, 97.5)),
        }
    sigma = float(np.median([row.get("phase_uncertainty_rad") or np.nan for row in rows]))
    floor = max(float(thresholds["median_abs_R_floor_rad"]), float(thresholds["median_abs_R_sigma_factor"]) * (sigma if np.isfinite(sigma) else 0.0))
    m3_pass = (
        skills["PRED_M3"] >= float(thresholds["skill_pass"])
        and boot["PRED_M3"]["ci_lower"] > float(thresholds["ci_lower_min"])
        and med_abs["PRED_M3"] <= floor
    )
    return {
        "crmse": crmses,
        "skill": skills,
        "median_abs_R": med_abs,
        "bootstrap": boot,
        "median_phase_uncertainty_rad": sigma,
        "median_abs_R_limit": floor,
        "pred_m3_numeric_pass": bool(m3_pass),
        "n_rows": len(rows),
        "n_clusters": len({r["carrier_group_token"] for r in rows}),
    }


def find_sealed_cases(*roots: Path | str) -> list[Path]:
    from .historical import find_sealed_cases as _find

    if not roots:
        return []
    return _find(*roots)


def load_thresholds(pack_root: Path | None = None) -> dict[str, Any]:
    thr = dict(DEFAULT_THRESHOLDS)
    if pack_root:
        path = Path(pack_root) / "THRESHOLDS_FROZEN.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            thr.update(data.get("phase_residual") or {})
    return thr


def _empty_tables() -> dict[str, list[dict[str, Any]]]:
    return {
        "phase_contract": [],
        "dispersion_contract": [],
        "return_time_contract": [],
        "phase_predictor_inputs": [],
        "blind_phase_predictions": [],
        "phase_decomposition_summary": [],
    }


def pack_export_dir(pack_root: Path | str | None) -> Path | None:
    if pack_root is None:
        return None
    root = Path(pack_root)
    if (root / "project.json").is_file() and (root / "src").is_dir():
        return root / "exports"
    return None


def copy_small_exports(dest: Path, export_dir: Path | None) -> list[str]:
    if export_dir is None:
        return []
    export_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in SMALL_EXPORT_NAMES:
        src = Path(dest) / name
        if src.is_file():
            target = export_dir / name
            target.write_bytes(src.read_bytes())
            copied.append(name)
    return copied


def emit_certificates(
    out: Path,
    *,
    accounting_status: str,
    residual_status: str,
    thresholds: dict[str, Any],
    tables: dict[str, list[dict[str, Any]]] | None = None,
    extra: dict[str, Any] | None = None,
    export_dir: Path | None = None,
) -> dict[str, Any]:
    tables = tables or _empty_tables()
    dest = Path(out) / "paper_upgrade"
    dest.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        write_parquet(dest / f"{name}.parquet", rows)
    payload = dict(extra or {})
    accounting = {
        "schema": "SST-PHASE-ACCOUNTING-CERTIFICATE-1.0",
        "status": accounting_status,
        "scientific_pass": False,
        "note": "Derived Phi_loop / Phi_carrier matching ACCOUNT_M3 is an implementation identity, never a residual PASS.",
        "code_hash": sha256_obj({"module": "residual", "version": __version__}),
        **payload,
    }
    residual = {
        "schema": "SST-PHASE-RESIDUAL-CERTIFICATE-1.0",
        "status": residual_status,
        "scientific_pass": residual_status == "PASS",
        "blindness_class": "RETROSPECTIVE_PREDICTION_LOCKED",
        "thresholds": thresholds,
        "code_hash": sha256_obj({"module": "residual", "version": __version__, "thresholds": thresholds}),
        **payload,
    }
    accounting["sha256"] = sha256_obj({k: v for k, v in accounting.items() if k != "sha256"})
    residual["sha256"] = sha256_obj({k: v for k, v in residual.items() if k != "sha256"})
    write_json(dest / "PHASE_ACCOUNTING_CERTIFICATE.json", accounting)
    write_json(dest / "PHASE_RESIDUAL_CERTIFICATE.json", residual)
    copied = copy_small_exports(dest, export_dir)
    return {"accounting": accounting, "residual": residual, "copied_exports": copied}


def run_phase_residual(
    out: Path | str,
    *,
    pack_root: Path | str | None = None,
    cfg: dict[str, Any] | None = None,
    historical_roots: list[Path | str] | None = None,
    search_default_historical: bool = True,
) -> dict[str, Any]:
    from .historical import (
        accounting_status_from_rows,
        discover_case_paths,
        load_historical_cases,
        residual_status_from_rows,
        rows_to_tables,
        sibling_version_counts,
    )

    out = Path(out)
    cfg = cfg or {}
    pack = Path(pack_root).resolve() if pack_root else Path(__file__).resolve().parents[2]
    thresholds = load_thresholds(pack)
    discovered = discover_case_paths(
        out,
        pack_root=pack,
        historical_roots=historical_roots,
        search_default_historical=search_default_historical,
    )
    cases = discovered["paths"]
    extra = {
        "execution_phase": "P2.5",
        "n_sealed_cases": len(cases),
        "case_source": discovered["source"],
        "case_roots": [
            str(Path(root).resolve().relative_to(pack.parent)).replace("\\", "/")
            if Path(root).resolve().is_relative_to(pack.parent)
            else root
            for root in discovered["roots"]
        ],
        "k_ref_eigensolve": "not_performed_reanalysis_only",
        "target_dependency_dag": [
            "omega(k)",
            "tau_return_synthetic",
            "synthetic_wavepacket_envelope",
            "phi_loop=wrap(-omega*tau+arg(envelope))",
        ],
        "tau_dependency_dag": ["vg(k)", "L_hat/|vg|", "synthetic_wavepacket"],
    }
    export_dir = pack_export_dir(pack)
    if not cases:
        extra["sibling_version_counts"] = sibling_version_counts(pack.parent)
        return emit_certificates(
            out,
            accounting_status=MISSING_CASES,
            residual_status=MISSING_CASES,
            thresholds=thresholds,
            extra=extra,
            export_dir=export_dir,
        )
    loaded = load_historical_cases(cases, relative_to=pack.parent)
    rows = loaded["rows"]
    tables = rows_to_tables(rows)
    residual_status, secondary = residual_status_from_rows(rows)
    accounting_status = accounting_status_from_rows(rows)
    if residual_status == "EVALUABLE":
        scored = score_independent_fixture(
            [
                {
                    "carrier_group_token": row["carrier_group_token"],
                    "phi_target_independent": row.get("phi_target_independent"),
                    "predictions": row.get("predictions") or {},
                    "phase_uncertainty_rad": row.get("phase_uncertainty_rad"),
                    "target_independence": row["target_independence"],
                    "tau_return_independence": row["tau_return_independence"],
                }
                for row in rows
            ],
            thresholds,
        )
        residual_status = scored["status"]
        extra["independent_score"] = {k: v for k, v in scored.items() if k != "status"}
    extra.update(
        {
            "n_analysis_rows": len(rows),
            "n_skipped": len(loaded["skipped"]),
            "n_evaluable_accounting": sum(1 for row in rows if row.get("evaluable_accounting")),
            "n_accounting_confirmed": sum(1 for row in rows if row.get("accounting_identity") == ACCOUNTING_OK),
            "n_accounting_failed": sum(1 for row in rows if row.get("accounting_identity") == ACCOUNTING_FAIL),
            "secondary_residual_reasons": secondary,
            "pred_m_scored": residual_status in {"PASS", "FAIL"},
            "sibling_version_counts": sibling_version_counts(pack.parent),
            "inventory_sha256": sha256_obj(loaded["inventory"]),
        }
    )
    dest = Path(out) / "paper_upgrade"
    dest.mkdir(parents=True, exist_ok=True)
    write_json(
        dest / "FROZEN_CASE_INVENTORY.json",
        {
            "cases": loaded["inventory"],
            "skipped": loaded["skipped"],
            "source": discovered["source"],
            "roots": extra["case_roots"],
        },
    )
    return emit_certificates(
        out,
        accounting_status=accounting_status,
        residual_status=residual_status,
        thresholds=thresholds,
        tables=tables,
        extra=extra,
        export_dir=export_dir,
    )


def score_independent_fixture(rows: list[dict[str, Any]], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    if not rows:
        return {"status": NO_INDEPENDENT_PHASE, "scientific_pass": False}
    target = rows[0]["target_independence"]
    tau = rows[0]["tau_return_independence"]
    if not independence_gates_pass(target, tau):
        if target.get("class") == "derived_from_predictors":
            return {"status": NO_INDEPENDENT_PHASE, "scientific_pass": False}
        return {"status": NONINDEPENDENT_TAU, "scientific_pass": False}
    tokens = {r["carrier_group_token"] for r in rows}
    if len(tokens) < int(thresholds["min_carriers"]):
        return {"status": INSUFFICIENT_CLUSTERS, "scientific_pass": False}
    stats = score_models(rows, thresholds)
    status = "PASS" if stats["pred_m3_numeric_pass"] else "FAIL"
    return {"status": status, "scientific_pass": status == "PASS", **stats}


def accounting_identity_status(phi_loop: float, account_m3: float, tol: float = 1e-10) -> str:
    return ACCOUNTING_OK if abs(wrapped_residual(phi_loop, account_m3)) <= tol else ACCOUNTING_FAIL
