from __future__ import annotations

from pathlib import Path
from typing import Any

from .boltzmann import (
    boltzmann_occupation_audit,
    detailed_balance_audit,
    microcanonical_temperature,
    maximum_permutability_audit,
    permutability_audit,
    state_count_entropy_force,
)
from .constants import EV_J, K_B_J_PER_K, OMEGA_SST, P_SUBSTRATE_0
from .convergence import convergence_audit
from .coupling import infer_empirical_couplings, three_gate
from .gaps import classify_amplitude_scans
from .io import ffloat, fint, read_csv, read_json, write_json
from .ledger import energy_ledger_audit, taxonomy_guard
from .observables import kinetic_stress, orientation_Q, spectroscopy_bound
from .thermo import Level, discrete_partition
from .verlinde import (
    canonical_holographic_scale_check,
    entropy_displacement_audit,
    force_reference_audit,
    integrability_audit,
    newton_power_law_audit,
    potential_entropy_audit,
    screen_audit,
)


def _path(base: Path, files: dict[str, str], key: str) -> Path:
    return base / files.get(key, f"{key}.csv")


def _fail_rows(gate: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"gate": gate, **x} for x in rows if x.get("status") == "FAIL"]


def run_campaign(config_path: Path) -> dict[str, Any]:
    cfg = read_json(config_path)
    base = config_path.parent
    files = cfg.get("files", {})
    th = cfg.get("thresholds", {})
    caps = cfg.get("model_capabilities", {})
    claims = cfg.get("research_claims", {})

    # Legacy/Maxwell kinetic closure inputs.
    modes = read_csv(_path(base, files, "modes"))
    amplitude = read_csv(_path(base, files, "amplitude_scan"))
    encounters = read_csv(_path(base, files, "encounters"))
    convergence = read_csv(_path(base, files, "convergence"))
    spectroscopy = read_csv(_path(base, files, "spectroscopy"))
    orientation = read_csv(_path(base, files, "orientation"))
    momenta = read_csv(_path(base, files, "momenta"))
    ledger = read_csv(_path(base, files, "energy_ledger"))

    # v0.3 Boltzmann/Verlinde research-closure inputs.  All are optional.
    state_distribution = read_csv(_path(base, files, "state_distribution"))
    state_occupations = read_csv(_path(base, files, "state_occupations"))
    state_counts = read_csv(_path(base, files, "state_counts"))
    detailed_balance = read_csv(_path(base, files, "detailed_balance"))
    force_reference = read_csv(_path(base, files, "force_reference"))
    integrability = read_csv(_path(base, files, "integrability"))
    screens = read_csv(_path(base, files, "screens"))
    entropy_displacement = read_csv(_path(base, files, "entropy_displacement"))
    radial_force = read_csv(_path(base, files, "radial_force"))
    potential_entropy = read_csv(_path(base, files, "potential_entropy"))

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

    # ------------------------------------------------------------------
    # Boltzmann 1877 layer: count first, fit equilibrium second.
    # ------------------------------------------------------------------
    permutability = permutability_audit(state_distribution)
    maximum_permutability = maximum_permutability_audit(
        state_distribution, permutability,
        float(th.get("maximum_permutability_logP_tol", 1e-9)),
        float(th.get("macrostate_energy_rel_tol", 1e-9)),
    )
    boltzmann_fit = boltzmann_occupation_audit(
        state_occupations,
        T,
        float(th.get("boltzmann_temperature_rel_tol", 0.10)),
        float(th.get("boltzmann_min_r2", 0.98)),
    )
    db_results = detailed_balance_audit(
        detailed_balance,
        T,
        float(th.get("detailed_balance_log_ratio_tol", 0.20)),
    )
    entropy_force = state_count_entropy_force(state_counts, T)
    micro_T = microcanonical_temperature(state_counts)

    # ------------------------------------------------------------------
    # Conditional Verlinde/SST bridge layer.
    # ------------------------------------------------------------------
    force_match = force_reference_audit(
        entropy_force,
        force_reference,
        float(th.get("entropic_force_rel_tol", 0.10)),
    )
    integ_results = integrability_audit(
        integrability,
        float(th.get("integrability_cross_sine_tol", 0.05)),
    )
    screen_results = screen_audit(
        screens,
        float(th.get("screen_area_slope_tol", 0.05)),
        float(th.get("equipartition_rel_tol", 0.10)),
        float(th.get("screen_G_rel_tol", 0.10)),
    )
    entropy_disp_results = entropy_displacement_audit(
        entropy_displacement,
        float(th.get("entropy_displacement_rel_tol", 0.10)),
    )
    radial_results = newton_power_law_audit(
        radial_force,
        float(th.get("newton_force_slope_tol", 0.10)),
    )
    potential_entropy_results = potential_entropy_audit(
        potential_entropy,
        float(th.get("potential_entropy_rel_tol", 0.10)),
    )

    physical_failures = []
    physical_failures += [{"gate": "GAP", **x} for x in hard_gap_failures]
    physical_failures += _fail_rows("THERMODYNAMIC", thermo)
    physical_failures += _fail_rows("SPECTROSCOPIC", spec_results)

    numerical_failures = []
    numerical_failures += _fail_rows("CONVERGENCE", conv_results)
    numerical_failures += _fail_rows("ENERGY_LEDGER", ledger_results)
    numerical_failures += _fail_rows("TAXONOMY", taxonomy)

    # Research-closure failures are conditional on explicit preregistered claims.
    closure_failures = []
    if bool(claims.get("boltzmann_equilibrium", False)):
        closure_failures += _fail_rows("MAXIMUM_PERMUTABILITY", maximum_permutability)
        closure_failures += _fail_rows("BOLTZMANN_EQUILIBRIUM", boltzmann_fit)
        closure_failures += _fail_rows("DETAILED_BALANCE", db_results)
    if bool(claims.get("entropic_pressure_force_equivalence", False)):
        closure_failures += _fail_rows("ENTROPIC_PRESSURE_FORCE", force_match)
        closure_failures += _fail_rows("PRESSURE_ENTROPY_INTEGRABILITY", integ_results)
    if bool(claims.get("verlinde_entropy_displacement", False)):
        closure_failures += _fail_rows("VERLINDE_ENTROPY_DISPLACEMENT", entropy_disp_results)
    if bool(claims.get("verlinde_holographic_screen", False)):
        closure_failures += _fail_rows("VERLINDE_SCREEN", screen_results)
    if bool(claims.get("newton_inverse_square", False)):
        closure_failures += _fail_rows("NEWTON_INVERSE_SQUARE", radial_results)
    if bool(claims.get("verlinde_potential_entropy", False)):
        closure_failures += _fail_rows("VERLINDE_POTENTIAL_ENTROPY", potential_entropy_results)

    kind = str(cfg.get("dataset_kind", "physical")).lower()
    if kind != "physical":
        overall = "DEMO_ONLY"
    elif physical_failures:
        overall = "FALSIFIER_TRIGGERED"
    elif closure_failures:
        overall = "RESEARCH_CLOSURE_FAILURE"
    elif numerical_failures:
        overall = "NUMERICAL_OR_CLOSURE_FAILURE"
    else:
        overall = "NO_FALSIFIER_TRIGGERED_NOT_VALIDATION"

    return {
        "campaign_id": cfg.get("campaign_id", config_path.stem),
        "dataset_kind": kind,
        "overall_verdict": overall,
        "research_claims": claims,
        "conditions": {
            "temperature_K": T,
            "kBT_eV": K_B_J_PER_K * T / EV_J,
            "observation_time_s": t_obs,
            "drive_energy_eV": drive,
        },
        "canonical_scale_checks": {
            "p_substrate_0_Pa": P_SUBSTRATE_0,
            "omega_sst_rad_s": OMEGA_SST,
            "holographic_core_hierarchy": canonical_holographic_scale_check(),
            "note": "Scale checks only; not knot-gas pressure, mode gaps, or proof of holography.",
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
        "boltzmann": {
            "permutability": permutability,
            "maximum_permutability": maximum_permutability,
            "occupation_fit": boltzmann_fit,
            "detailed_balance": db_results,
            "entropy_force": entropy_force,
            "microcanonical_temperature": micro_T,
        },
        "verlinde_bridge": {
            "force_match": force_match,
            "integrability": integ_results,
            "screen_audit": screen_results,
            "entropy_displacement": entropy_disp_results,
            "newton_power_law": radial_results,
            "potential_entropy": potential_entropy_results,
        },
        "physical_failures": physical_failures,
        "research_closure_failures": closure_failures,
        "numerical_failures": numerical_failures,
        "interpretation_guard": (
            "Absence of triggered falsifiers is not evidence that SST is correct. "
            "Boltzmann/Verlinde gates are conditional bridge tests and become failures only when the corresponding research_claim is preregistered true."
        ),
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

    lines += ["", "## Research-closure failures", ""]
    if result["research_closure_failures"]:
        for x in result["research_closure_failures"]:
            lines.append(f"- **FAIL [{x['gate']}]** `{x.get('series_id',x.get('screen_series_id',x.get('sample_id',x.get('ensemble_id',x.get('macrostate_id',x.get('transition_id',''))))))}`")
    else:
        lines.append("- None triggered for the preregistered optional Boltzmann/Verlinde claims.")

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

    lines += ["", "## Boltzmann 1877 state-counting layer", ""]
    b=result["boltzmann"]
    lines.append(f"- Permutability distributions: {len(b['permutability'])}")
    lines.append(f"- Maximum-permutability macrostate tests: {len(b['maximum_permutability'])}")
    lines.append(f"- Boltzmann occupation fits: {len(b['occupation_fit'])}")
    lines.append(f"- Detailed-balance rows: {len(b['detailed_balance'])}")
    lines.append(f"- Entropy-force derivative rows: {len(b['entropy_force'])}")
    lines.append(f"- Microcanonical-temperature estimates: {len(b['microcanonical_temperature'])}")
    if b["occupation_fit"]:
        lines += ["", "| Ensemble | Knot | T_fit K | rel T error | R2 | KL nats | Status |", "|---|---|---:|---:|---:|---:|---|"]
        for x in b["occupation_fit"]:
            if "T_fit_K" in x:
                lines.append(f"| {x['ensemble_id']} | {x['knot']} | {x['T_fit_K']:.9g} | {x['relative_T_error']:.6g} | {x['r2']:.6g} | {x['KL_observed_vs_reference_nats']:.6g} | {x['status']} |")

    lines += ["", "## Boltzmann–Verlinde–SST bridge", ""]
    v=result["verlinde_bridge"]
    lines.append(f"- Entropic-force vs independent pressure/hydrodynamic force comparisons: {len(v['force_match'])}")
    lines.append(f"- Pressure/temperature integrability checks: {len(v['integrability'])}")
    lines.append(f"- Holographic-screen series: {len(v['screen_audit'])}")
    lines.append(f"- Entropy-displacement postulate rows: {len(v['entropy_displacement'])}")
    lines.append(f"- Inverse-square radial series: {len(v['newton_power_law'])}")
    lines.append(f"- Potential/entropy rows: {len(v['potential_entropy'])}")
    if v["force_match"]:
        lines += ["", "| Series | x m | F_ent N | F_hyd N | rel error | sign | Status |", "|---|---:|---:|---:|---:|---|---|"]
        for x in v["force_match"]:
            lines.append(f"| {x['series_id']} | {x['x_m']:.9g} | {x['F_entropic_N']:.9g} | {x['F_hyd_N']:.9g} | {x['relative_symmetric_error']:.6g} | {x['sign_match']} | {x['status']} |")

    lines += ["", "## Spectroscopy", ""]
    if result["spectroscopy"]:
        lines += ["| Observable | Bound eV | Empirical limit eV | Status |", "|---|---:|---:|---|"]
        for s in result["spectroscopy"]:
            lines.append(f"| {s['observable_id']} | {s['predicted_bound_eV']:.9g} | {s['empirical_limit_eV']} | {s['status']} |")
    else:
        lines.append("No spectroscopy rows supplied.")

    h=result["canonical_scale_checks"]["holographic_core_hierarchy"]
    lines += [
        "", "## Canonical scale checks", "",
        f"- 0.5 rho_f v_swirl^2 = {result['canonical_scale_checks']['p_substrate_0_Pa']:.9g} Pa",
        f"- v_swirl/r_c = {result['canonical_scale_checks']['omega_sst_rad_s']:.9g} s^-1",
        f"- (r_c/l_P)^2 = {h['r_c2_over_lP2']:.9g}",
        f"- G from one holographic bit per r_c^2 = {h['G_if_one_bit_per_r_c2_SI']:.9g} m^3 kg^-1 s^-2",
        "- The holographic quantities are hierarchy diagnostics only; they are not canonized SST identifications.",
        "",
    ]
    return "\n".join(lines)


def save_campaign(result: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "report.json", result)
    (out_dir / "report.md").write_text(render_markdown(result), encoding="utf-8")
