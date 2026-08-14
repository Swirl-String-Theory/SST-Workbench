from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import EV_J, K_B_J_PER_K, OMEGA_SST, P_SUBSTRATE_0
from .convergence import convergence_audit
from .coupling import infer_empirical_couplings, three_gate
from .gaps import classify_amplitude_scans
from .io import ffloat, fint, read_csv, read_json, write_json
from .ledger import energy_ledger_audit, taxonomy_guard
from .observables import kinetic_stress, orientation_Q, spectroscopy_bound
from .thermo import Level, discrete_partition


def _path(base: Path, files: dict[str, str], key: str) -> Path:
    return base / files.get(key, f"{key}.csv")


def run_campaign(config_path: Path) -> dict[str, Any]:
    cfg = read_json(config_path)
    base = config_path.parent
    files = cfg.get("files", {})
    th = cfg.get("thresholds", {})
    caps = cfg.get("model_capabilities", {})

    modes = read_csv(_path(base, files, "modes"))
    amplitude = read_csv(_path(base, files, "amplitude_scan"))
    encounters = read_csv(_path(base, files, "encounters"))
    convergence = read_csv(_path(base, files, "convergence"))
    spectroscopy = read_csv(_path(base, files, "spectroscopy"))
    orientation = read_csv(_path(base, files, "orientation"))
    momenta = read_csv(_path(base, files, "momenta"))
    ledger = read_csv(_path(base, files, "energy_ledger"))

    gap_results = classify_amplitude_scans(
        amplitude,
        float(th.get("gap_abs_floor_eV", 1e-12)),
        float(th.get("gap_rel_intercept_tol", 0.05)),
    )
    gap_lookup = {(r["knot"], r["mode_id"]): r for r in gap_results}
    empirical_coupling = infer_empirical_couplings(
        encounters,
        float(th.get("coupling_sigma_threshold", 5.0)),
        float(th.get("min_transfer_fraction", 1e-4)),
    )
    coupling_lookup = {(r["knot"], r["mode_id"]): r for r in empirical_coupling}

    T = float(cfg.get("temperature_K", 300.0))
    t_obs = float(cfg.get("observation_time_s", 1.0))
    drive = float(cfg.get("drive_energy_eV", 0.0))
    coupling_threshold = float(th.get("coupling_norm_threshold", 1e-4))

    mode_audit = []
    thermal_levels_by_knot: dict[str, list[Level]] = {}
    hard_gap_failures = []
    for r in modes:
        knot, mode_id = r["knot"], r["mode_id"]
        gap_claim = ffloat(r, "gap_eV")
        gap_status = (r.get("gap_status") or "unknown").strip().lower()
        tau = ffloat(r, "tau_s")
        c_norm = ffloat(r, "coupling_norm")
        empirical = coupling_lookup.get((knot, mode_id))
        if c_norm is None and empirical is not None:
            c_norm = empirical["median_transfer_fraction"]
        gates = three_gate(c_norm, gap_claim, tau, drive, t_obs, coupling_threshold)
        kbt_eV = K_B_J_PER_K * T / EV_J
        thermal_active = None if gap_claim is None else bool(gap_claim <= kbt_eV and gates["coupling_gate"] and (tau is not None and tau <= t_obs))

        scan = gap_lookup.get((knot, mode_id))
        gap_claim_failure = False
        if gap_claim is not None and gap_claim > 0 and scan and scan.get("status") == "CONTINUOUS_TO_ZERO":
            gap_claim_failure = True
            hard_gap_failures.append({"knot": knot, "mode_id": mode_id, "claimed_gap_eV": gap_claim, "scan": scan})
        if gap_status == "continuous" and gap_claim not in (None, 0.0):
            gap_claim_failure = True

        # Only dynamically connected/equilibrating levels enter the observed-equilibrium
        # partition audit. The Boltzmann factor itself handles whether Delta >> kBT.
        if (
            gap_claim is not None
            and gap_claim > 0
            and gap_status in {"true_gap", "discrete", "activation"}
            and gates["coupling_gate"] is True
            and tau is not None
            and tau <= t_obs
        ):
            thermal_levels_by_knot.setdefault(knot, []).append(Level(gap_claim, max(1, fint(r, "degeneracy", 1))))

        mode_audit.append({
            "knot": knot,
            "mode_id": mode_id,
            "family": r.get("family", ""),
            "omega_rad_s": ffloat(r, "omega_rad_s"),
            "gap_eV": gap_claim,
            "gap_status": gap_status,
            "tau_s": tau,
            "coupling_norm": c_norm,
            "three_gate": gates,
            "thermal_active": thermal_active,
            "gap_claim_failure": gap_claim_failure,
        })

    thermo = []
    cv_limit = th.get("cv_limit_kB_per_knot")
    for knot, levels in sorted(thermal_levels_by_knot.items()):
        result = discrete_partition(levels, T)
        status = "INDETERMINATE" if cv_limit is None else ("FAIL" if result["Cv_over_kB"] > float(cv_limit) else "PASS")
        thermo.append({"knot": knot, **result, "limit_Cv_over_kB": cv_limit, "status": status})

    spec_results = spectroscopy_bound(spectroscopy)
    conv_results = convergence_audit(convergence, float(th.get("convergence_rel_tol", 0.05)))
    orient_results = orientation_Q(orientation)
    q_limit = float(th.get("isotropy_Q_frobenius_limit", 0.05))
    for r in orient_results:
        if "Q_frobenius" in r:
            r["limit"] = q_limit
            r["status"] = "PASS" if r["Q_frobenius"] <= q_limit else "FAIL"
    stress_results = kinetic_stress(momenta)
    ledger_results = energy_ledger_audit(ledger, float(th.get("energy_conservation_rel_tol", 1e-6)))
    taxonomy = taxonomy_guard(modes, bool(caps.get("finite_core_resolved", False)), bool(caps.get("material_frame_resolved", False)))

    physical_failures = []
    physical_failures += [{"gate": "GAP", **x} for x in hard_gap_failures]
    physical_failures += [{"gate": "THERMODYNAMIC", **x} for x in thermo if x["status"] == "FAIL"]
    physical_failures += [{"gate": "SPECTROSCOPIC", **x} for x in spec_results if x["status"] == "FAIL"]
    numerical_failures = []
    numerical_failures += [{"gate": "CONVERGENCE", **x} for x in conv_results if x.get("status") == "FAIL"]
    numerical_failures += [{"gate": "ENERGY_LEDGER", **x} for x in ledger_results if x.get("status") == "FAIL"]
    numerical_failures += [{"gate": "TAXONOMY", **x} for x in taxonomy if x.get("status") == "FAIL"]

    kind = str(cfg.get("dataset_kind", "physical")).lower()
    if kind != "physical":
        overall = "DEMO_ONLY"
    elif physical_failures:
        overall = "FALSIFIER_TRIGGERED"
    elif numerical_failures:
        overall = "NUMERICAL_OR_CLOSURE_FAILURE"
    else:
        overall = "NO_FALSIFIER_TRIGGERED_NOT_VALIDATION"

    return {
        "campaign_id": cfg.get("campaign_id", config_path.stem),
        "dataset_kind": kind,
        "overall_verdict": overall,
        "conditions": {
            "temperature_K": T,
            "kBT_eV": K_B_J_PER_K * T / EV_J,
            "observation_time_s": t_obs,
            "drive_energy_eV": drive,
        },
        "canonical_scale_checks": {
            "p_substrate_0_Pa": P_SUBSTRATE_0,
            "omega_sst_rad_s": OMEGA_SST,
            "note": "scale checks only; not knot-gas pressure or mode gaps",
        },
        "mode_audit": mode_audit,
        "gap_scan": gap_results,
        "empirical_coupling": empirical_coupling,
        "thermodynamics": thermo,
        "spectroscopy": spec_results,
        "convergence": conv_results,
        "orientation_isotropy": orient_results,
        "kinetic_stress": stress_results,
        "energy_ledger": ledger_results,
        "taxonomy_guard": taxonomy,
        "physical_failures": physical_failures,
        "numerical_failures": numerical_failures,
        "interpretation_guard": "Absence of triggered falsifiers is not evidence that SST is correct.",
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Maxwell–SST falsifier report — {result['campaign_id']}",
        "",
        f"**Dataset:** `{result['dataset_kind']}`  ",
        f"**Verdict:** `{result['overall_verdict']}`",
        "",
        "> Absence of a triggered falsifier is **not** validation of SST.",
        "",
        "## Conditions",
        "",
        f"- T = {result['conditions']['temperature_K']:.9g} K",
        f"- kBT = {result['conditions']['kBT_eV']:.9g} eV",
        f"- observation time = {result['conditions']['observation_time_s']:.9g} s",
        f"- drive energy = {result['conditions']['drive_energy_eV']:.9g} eV",
        "",
        "## Physical falsifiers",
        "",
    ]
    if result["physical_failures"]:
        for x in result["physical_failures"]:
            lines.append(f"- **FAIL [{x['gate']}]** `{x.get('knot','')}/{x.get('mode_id',x.get('observable_id',''))}`")
    else:
        lines.append("- None triggered by the supplied data.")
    lines += ["", "## Numerical / closure failures", ""]
    if result["numerical_failures"]:
        for x in result["numerical_failures"]:
            lines.append(f"- **FAIL [{x['gate']}]** `{x.get('knot','')}/{x.get('mode_id',x.get('interaction_id',''))}`")
    else:
        lines.append("- None triggered by the supplied data.")
    lines += ["", "## Mode ledger", "", "| Knot | Mode | Family | Gap eV | Coupling | tau s | 3-gate active | Gap claim fail |", "|---|---|---|---:|---:|---:|---|---|"]
    for m in result["mode_audit"]:
        lines.append(
            f"| {m['knot']} | {m['mode_id']} | {m['family']} | {m['gap_eV'] if m['gap_eV'] is not None else ''} | "
            f"{m['coupling_norm'] if m['coupling_norm'] is not None else ''} | {m['tau_s'] if m['tau_s'] is not None else ''} | "
            f"{m['three_gate']['active']} | {m['gap_claim_failure']} |"
        )
    lines += ["", "## Thermodynamics", ""]
    if result["thermodynamics"]:
        lines += ["| Knot | Cv/kB | Limit | Status |", "|---|---:|---:|---|"]
        for t in result["thermodynamics"]:
            lines.append(f"| {t['knot']} | {t['Cv_over_kB']:.9g} | {t['limit_Cv_over_kB']} | {t['status']} |")
    else:
        lines.append("No declared discrete/gapped internal levels available for a partition-function audit.")
    lines += ["", "## Spectroscopy", ""]
    if result["spectroscopy"]:
        lines += ["| Observable | Bound eV | Empirical limit eV | Status |", "|---|---:|---:|---|"]
        for s in result["spectroscopy"]:
            lines.append(f"| {s['observable_id']} | {s['predicted_bound_eV']:.9g} | {s['empirical_limit_eV']} | {s['status']} |")
    else:
        lines.append("No spectroscopy rows supplied.")
    lines += ["", "## Canonical scale checks", "", f"- 0.5 rho_f v_swirl^2 = {result['canonical_scale_checks']['p_substrate_0_Pa']:.9g} Pa", f"- v_swirl/r_c = {result['canonical_scale_checks']['omega_sst_rad_s']:.9g} s^-1", "- These are scale checks only, not a knot-gas pressure or a mode gap.", ""]
    return "\n".join(lines)


def save_campaign(result: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "report.json", result)
    (out_dir / "report.md").write_text(render_markdown(result), encoding="utf-8")
