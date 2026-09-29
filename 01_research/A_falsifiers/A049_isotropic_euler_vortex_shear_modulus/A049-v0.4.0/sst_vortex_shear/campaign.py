from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np

from .backend import energy_ratio_general, backend_name
from .reference import (
    fit_even_energy_coefficient,
    isotropy_tensor,
    transverse_residual,
    energy_ratio_helicity_pair,
    transverse_wave_ratio_from_A2,
    linearized_rest_euler_frequency,
)
from .sampling import paired_transverse_samples, shear_matrix
from .euler_spectral import (
    EulerSpectral3D,
    velocity_covariance_isotropy,
    helical_probe_field,
    probe_descriptor,
    probe_amplitude,
    fit_complex_mode,
)
from .vortex_field import (
    structured_hopf_tube_background,
    spectrum_matched_random_control,
    spectral_edge_fraction,
)

THEORY_A2 = 2.0 / 15.0


def _load_config(config_path):
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_csv(path, rows):
    rows = list(rows)
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _rel_l2(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.linalg.norm((a-b).ravel()) / max(np.linalg.norm(b.ravel()), 1e-300))


def verify_seal(blind_dir):
    blind = Path(blind_dir)
    seal = blind / "BLIND_SEAL_SHA256.txt"
    if not seal.exists():
        return False, ["BLIND_SEAL_SHA256.txt missing"]
    errors = []
    for line in seal.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        p = blind / rel
        if not p.exists():
            errors.append(f"missing:{rel}")
        elif _sha256(p) != digest:
            errors.append(f"hash:{rel}")
    return not errors, errors


def _static_born_campaign(cfg):
    gammas = np.asarray(cfg["strain_amplitudes"], dtype=float)
    planes = list(cfg["shear_planes"])
    n_pair, w_pair, n_base, e1, e2 = paired_transverse_samples(cfg["n_directions"])
    rows, fits = [], {}
    max_odd, max_helicity = 0.0, 0.0
    for plane in planes:
        rp, rm = [], []
        for g in gammas:
            fp, fm = shear_matrix(+g, plane), shear_matrix(-g, plane)
            ap = energy_ratio_general(n_pair, w_pair, fp)
            am = energy_ratio_general(n_pair, w_pair, fm)
            hp, hm = energy_ratio_helicity_pair(n_base, e1, e2, fp)
            rp.append(ap); rm.append(am)
            max_odd = max(max_odd, abs(0.5*(ap-am)))
            max_helicity = max(max_helicity, abs(hp-hm))
            rows.append({
                "plane": plane, "gamma": float(g), "R_plus": ap, "R_minus": am,
                "even_delta": 0.5*(ap+am)-1.0, "odd_component": 0.5*(ap-am),
                "helicity_plus_ratio": hp, "helicity_minus_ratio": hm,
            })
        fit = fit_even_energy_coefficient(gammas, rp, rm)
        fit["relative_error_vs_2_over_15"] = abs(fit["A2"]-THEORY_A2)/THEORY_A2
        fit["candidate_cT_over_urms"] = transverse_wave_ratio_from_A2(fit["A2"])
        fits[plane] = fit
    vals = np.array([fits[p]["A2"] for p in planes])
    A2 = float(vals.mean())
    return {
        "rows": rows,
        "transverse_residual": transverse_residual(n_pair, w_pair),
        "orientation_isotropy_fro": float(np.linalg.norm(isotropy_tensor(n_base)-np.eye(3)/3.0)),
        "A2_mean": A2,
        "A2_plane_relative_spread": float((vals.max()-vals.min())/abs(A2)),
        "candidate_cT_over_urms": math.sqrt(max(A2, 0.0)),
        "max_odd_energy_component": max_odd,
        "helicity_split_max_abs": max_helicity,
        "plane_fits": fits,
    }


def _dynamic_probe_set(grid, dc, reduced=False):
    amp = float(dc["probe_amplitude"])
    if reduced:
        axis = dc["secondary_axis"]
        mode = int(dc["primary_mode"])
        descs = [probe_descriptor(grid, axis, mode, h) for h in (-1, +1)]
        probes = [helical_probe_field(grid, axis, mode, h, amp) for h in (-1, +1)]
        return np.stack(probes), descs
    probes, descs = [], []
    for axis in dc["primary_axes"]:
        for h in (-1, +1):
            probes.append(helical_probe_field(grid, axis, int(dc["primary_mode"]), h, amp))
            descs.append(probe_descriptor(grid, axis, int(dc["primary_mode"]), h))
    for h in (-1, +1):
        probes.append(helical_probe_field(grid, dc["secondary_axis"], int(dc["secondary_mode"]), h, amp))
        descs.append(probe_descriptor(grid, dc["secondary_axis"], int(dc["secondary_mode"]), h))
    return np.stack(probes), descs


def _build_background(grid, cfg, kind):
    dc = cfg["structured_dynamic"]
    structured, meta = structured_hopf_tube_background(grid, dc, seed=int(cfg["seed"]))
    if kind == "structured":
        return structured, meta
    if kind == "spectrum_matched_random_control":
        ctrl = spectrum_matched_random_control(grid, structured, int(cfg["seed"]) + 991)
        meta = dict(meta)
        meta["control"] = "same shell-energy spectrum, randomized divergence-free phases"
        return ctrl, meta
    raise ValueError(kind)


def _fit_probes(times, amps, descs, reference_speed, urms0, cfg):
    qtol = cfg["wave_qualification"]
    dc = cfg["structured_dynamic"]
    fits, rows = [], []
    for i, desc in enumerate(descs):
        fit = fit_complex_mode(times, amps[i], float(dc["fit_min_relative_amplitude"]))
        c_abs = fit["omega_abs"] / max(desc["k"], 1e-300)
        c_ref = c_abs / max(reference_speed, 1e-300)
        c_urms = c_abs / max(urms0, 1e-300)
        damping_ratio = abs(fit["log_amplitude_rate"]) / max(fit["omega_abs"], 1e-300)
        qualified = (
            fit["phase_fit_r2"] >= float(qtol["phase_fit_r2_min"])
            and fit["coherent_fit_fraction"] >= float(qtol["coherent_fit_fraction_min"])
            and c_ref >= float(qtol["c_over_reference_min"])
            and damping_ratio <= float(qtol["damping_over_omega_max"])
        )
        rec = {
            "axis": desc["axis"], "mode": desc["mode"], "helicity": desc["helicity"], "k": desc["k"],
            **fit, "c_abs_blind": c_abs, "c_over_reference": c_ref, "c_over_urms": c_urms,
            "damping_over_omega": damping_ratio, "wave_qualified": bool(qualified),
        }
        fits.append(rec)
        for t, a in zip(times, amps[i]):
            rows.append({
                "axis": desc["axis"], "mode": desc["mode"], "helicity": desc["helicity"],
                "time": float(t), "amplitude_real": float(np.real(a)), "amplitude_imag": float(np.imag(a)),
                "amplitude_abs_rel": float(abs(a)/max(abs(amps[i][0]),1e-300)),
                "phase_rel_rad": float(np.angle(a/amps[i][0])),
            })
    return fits, rows


def _aggregate_wave_metrics(fits, dc):
    primary_mode, secondary_mode = int(dc["primary_mode"]), int(dc["secondary_mode"])
    primary = [r for r in fits if r["mode"] == primary_mode]
    secondary = [r for r in fits if r["mode"] == secondary_mode]
    pvals = np.array([r["c_over_reference"] for r in primary], dtype=float)
    svals = np.array([r["c_over_reference"] for r in secondary], dtype=float)
    pmed = float(np.median(pvals)) if len(pvals) else math.nan
    smed = float(np.median(svals)) if len(svals) else math.nan

    axis_means = []
    for axis in dc["primary_axes"]:
        pair = [r["c_over_reference"] for r in primary if r["axis"] == axis]
        if pair:
            axis_means.append(float(np.mean(pair)))
    direction_spread = (
        float((max(axis_means)-min(axis_means))/max(abs(float(np.mean(axis_means))),1e-300))
        if len(axis_means) >= 2 else math.inf
    )

    helicity_splits = []
    for mode in sorted(set(r["mode"] for r in fits)):
        for axis in sorted(set(r["axis"] for r in fits if r["mode"] == mode)):
            pair = [r for r in fits if r["mode"] == mode and r["axis"] == axis]
            if len(pair) == 2:
                a, b = pair
                helicity_splits.append(
                    abs(a["c_over_reference"]-b["c_over_reference"])
                    / max(0.5*(a["c_over_reference"]+b["c_over_reference"]),1e-300)
                )
    helicity_split = max(helicity_splits, default=math.inf)
    dispersion = abs(pmed-smed)/max(abs(pmed),1e-300) if len(svals) else math.inf
    return {
        "primary_c_over_reference_median": pmed,
        "secondary_c_over_reference_median": smed,
        "candidate_bulk_cT_over_reference": 0.5*(pmed+smed) if np.isfinite(pmed) and np.isfinite(smed) else None,
        "direction_spread_relative": direction_spread,
        "helicity_split_relative": float(helicity_split),
        "dispersion_relative": float(dispersion),
    }


def _run_dynamic(cfg, kind="structured", n_override=None, reduced=False, t_final_override=None):
    dc = cfg["structured_dynamic"]
    n = int(n_override or dc["grid_n"])
    grid = EulerSpectral3D(n=n, length=float(dc["domain_length"]))
    u, meta = _build_background(grid, cfg, kind)
    cov, cov_iso = velocity_covariance_isotropy(grid, u)
    e0 = grid.energy(u); urms0 = grid.urms(u); div0 = grid.divergence_fourier_rel(u)
    edge0 = spectral_edge_fraction(grid, u)
    reference_speed = float(meta["reference_speed"])
    probes, descs = _dynamic_probe_set(grid, dc, reduced=reduced)
    d = probes.copy(); divd0 = grid.divergence_fourier_rel(d)

    dt = float(dc["dt"])
    t_final = float(t_final_override if t_final_override is not None else dc["t_final"])
    if reduced:
        t_final = min(t_final, float(dc["coarse_t_final"]))
    steps = int(round(t_final/dt)); stride = int(dc["sample_stride"])
    times = [0.0]; amps = [[probe_amplitude(d, desc, i)] for i, desc in enumerate(descs)]
    energies = [e0]; max_div = max(div0, divd0)
    for step in range(1, steps+1):
        u, d = grid.rk4_step(u, d, dt)
        if step % stride == 0 or step == steps:
            times.append(step*dt); energies.append(grid.energy(u))
            max_div = max(max_div, grid.divergence_fourier_rel(u), grid.divergence_fourier_rel(d))
            for i, desc in enumerate(descs):
                amps[i].append(probe_amplitude(d, desc, i))

    # Independent one-step/two-half consistency from the exact same initial state.
    u0, _ = _build_background(grid, cfg, kind)
    d0, _ = _dynamic_probe_set(grid, dc, reduced=reduced)
    u1, d1 = grid.rk4_step(u0, d0, dt)
    uh, dh = grid.rk4_step(u0, d0, 0.5*dt)
    u2, d2 = grid.rk4_step(uh, dh, 0.5*dt)
    rk_rel = max(_rel_l2(u1,u2), _rel_l2(d1,d2))

    fits, rows = _fit_probes(times, amps, descs, reference_speed, urms0, cfg)
    agg = _aggregate_wave_metrics(fits, dc)
    return {
        "kind": kind, "n": n, "background_meta": meta,
        "background_urms_initial": urms0, "background_covariance_normalized": cov.tolist(),
        "background_covariance_isotropy_fro": cov_iso,
        "initial_divergence_rel": div0, "initial_probe_divergence_rel": divd0,
        "max_divergence_rel": max_div, "base_energy_initial": e0,
        "base_energy_drift_rel_max": float(np.max(np.abs(np.asarray(energies)-e0))/max(e0,1e-300)),
        "rk4_one_step_vs_two_half_rel_l2": rk_rel,
        "spectral_edge_energy_fraction_initial": edge0,
        "spectral_edge_energy_fraction_final": spectral_edge_fraction(grid, u),
        "reference_speed": reference_speed,
        "probe_fits": fits, "probe_rows": rows,
        "qualified_probe_count": int(sum(r["wave_qualified"] for r in fits)),
        "probe_count": len(fits), "all_probes_qualified": bool(all(r["wave_qualified"] for r in fits)),
        **agg,
    }


def _relative_equilibrium_diagnostic(cfg, n_override=None):
    dc = cfg["structured_dynamic"]
    rc = cfg["relative_equilibrium"]
    n = int(n_override or dc["grid_n"])
    grid = EulerSpectral3D(n=n, length=float(dc["domain_length"]))
    u0, meta = _build_background(grid, cfg, "structured")
    U, translation_residual, rhs_rate = grid.relative_equilibrium_translation_fit(u0)
    dt = float(dc["dt"])
    t_final = float(rc["diagnostic_time"])
    steps = int(round(t_final / dt))
    u = u0.copy()
    for _ in range(steps):
        u = grid.rk4_base_step(u, dt)
    expected = grid.translate_state(u0, U, steps * dt)
    comoving_change = _rel_l2(u, expected)
    raw_change = _rel_l2(u, u0)
    return {
        "n": n,
        "translation_velocity_blind": U.tolist(),
        "translation_speed_blind": float(np.linalg.norm(U)),
        "translation_residual_rel_l2": translation_residual,
        "base_rhs_rate_blind": rhs_rate,
        "diagnostic_time": steps * dt,
        "raw_state_change_rel_l2": raw_change,
        "comoving_state_change_rel_l2": comoving_change,
        "spectral_edge_energy_fraction_initial": spectral_edge_fraction(grid, u0),
        "spectral_edge_energy_fraction_final": spectral_edge_fraction(grid, u),
        "reference_speed": float(meta["reference_speed"]),
    }


def _run_frozen_dynamic(cfg):
    dc = cfg["structured_dynamic"]
    fc = cfg["frozen_background"]
    grid = EulerSpectral3D(n=int(dc["grid_n"]), length=float(dc["domain_length"]))
    u, meta = _build_background(grid, cfg, "structured")
    urms0 = grid.urms(u)
    reference_speed = float(meta["reference_speed"])
    probes, descs = _dynamic_probe_set(grid, dc, reduced=False)
    d = probes.copy()
    dt = float(dc["dt"])
    t_final = float(fc["t_final"])
    stride = int(fc.get("sample_stride", dc["sample_stride"]))
    steps = int(round(t_final / dt))
    times = [0.0]
    amps = [[probe_amplitude(d, desc, i)] for i, desc in enumerate(descs)]
    max_div = grid.divergence_fourier_rel(d)
    for step in range(1, steps + 1):
        d = grid.rk4_tangent_frozen_step(u, d, dt)
        if step % stride == 0 or step == steps:
            times.append(step * dt)
            max_div = max(max_div, grid.divergence_fourier_rel(d))
            for i, desc in enumerate(descs):
                amps[i].append(probe_amplitude(d, desc, i))
    fits, rows = _fit_probes(times, amps, descs, reference_speed, urms0, cfg)
    agg = _aggregate_wave_metrics(fits, dc)
    return {
        "kind": "frozen_structured",
        "n": grid.n,
        "background_urms_initial": urms0,
        "reference_speed": reference_speed,
        "max_probe_divergence_rel": max_div,
        "probe_fits": fits,
        "probe_rows": rows,
        "qualified_probe_count": int(sum(r["wave_qualified"] for r in fits)),
        "probe_count": len(fits),
        "all_probes_qualified": bool(all(r["wave_qualified"] for r in fits)),
        **agg,
    }


def run_blind_campaign(config_path, out_dir):
    cfg = _load_config(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tol, wq = cfg["tolerances"], cfg["wave_qualification"]
    dc, rc = cfg["structured_dynamic"], cfg["relative_equilibrium"]

    # Cheap, target-free prequalification first.  v0.4.1 deliberately does
    # not spend the expensive tangent-wave budget on a background that is not
    # an approximate Euler relative equilibrium.
    born = _static_born_campaign(cfg)
    rel_eq = _relative_equilibrium_diagnostic(cfg)
    rel_eq_hi = _relative_equilibrium_diagnostic(
        cfg, n_override=int(rc["resolution_check_grid_n"])
    )

    kprobe = np.array([1.0, 2.0, -3.0])
    uprobe = np.cross(kprobe, np.array([0.3, -0.4, 0.8]))
    uprobe /= np.linalg.norm(uprobe)
    rest_accel, rest_trans = linearized_rest_euler_frequency(kprobe, uprobe)

    rel_eq_ok = (
        rel_eq["translation_residual_rel_l2"] <= float(rc["translation_residual_max"])
        and rel_eq["comoving_state_change_rel_l2"] <= float(rc["comoving_change_rel_max"])
    )
    rel_eq_resolution_delta = abs(
        rel_eq_hi["translation_residual_rel_l2"]
        - rel_eq["translation_residual_rel_l2"]
    )
    rel_eq_resolution_stable = (
        rel_eq_resolution_delta <= float(rc["resolution_residual_delta_max"])
    )

    qualification = {
        "Q01_STATIC_TRANSVERSE_SAMPLING": born["transverse_residual"] < tol["static_transverse_max_abs"],
        "Q02_STATIC_A2_RECOVERY": abs(born["A2_mean"] - THEORY_A2) / THEORY_A2 < tol["static_A2_relative_error_max"],
        "Q03_REL_EQ_INITIAL_SPECTRAL_RESOLUTION": rel_eq["spectral_edge_energy_fraction_initial"] < tol["spectral_edge_energy_fraction_initial_max"],
        "Q04_REL_EQ_RESOLUTION_CHECK_INITIAL_SPECTRAL_RESOLUTION": rel_eq_hi["spectral_edge_energy_fraction_initial"] < tol["spectral_edge_energy_fraction_initial_max"],
        "Q05_BARE_REST_EULER_NO_WAVE": rest_accel < tol["rest_euler_operator_abs_max"],
        "Q06_REL_EQ_RESIDUAL_RESOLUTION_STABILITY": rel_eq_resolution_stable,
    }
    qualification = {k: bool(v) for k, v in qualification.items()}
    preconditions = {
        "P01_BACKGROUND_TRANSLATION_RESIDUAL": rel_eq["translation_residual_rel_l2"] <= float(rc["translation_residual_max"]),
        "P02_BACKGROUND_COMOVING_PERSISTENCE": rel_eq["comoving_state_change_rel_l2"] <= float(rc["comoving_change_rel_max"]),
        "P03_BACKGROUND_RELATIVE_EQUILIBRIUM": rel_eq_ok,
    }
    preconditions = {k: bool(v) for k, v in preconditions.items()}

    # Expensive wave stage is conditional by design.
    wave_stage_executed = bool(all(qualification.values()) and rel_eq_ok)
    structured = coarse = control = frozen = None
    if wave_stage_executed:
        structured = _run_dynamic(cfg, kind="structured", reduced=False)
        coarse = _run_dynamic(
            cfg, kind="structured",
            n_override=int(dc["coarse_grid_n"]), reduced=True,
        )
        control = _run_dynamic(
            cfg, kind="spectrum_matched_random_control", reduced=True,
            t_final_override=float(dc["control_t_final"]),
        )
        frozen = _run_frozen_dynamic(cfg)

        dynamic_qualification = {
            "Q07_STRUCTURED_GEOMETRY_ORIENTATION_ISOTROPY": structured["background_meta"]["orientation_isotropy_fro"] < tol["structured_initial_isotropy_fro_max"],
            "Q08_STRUCTURED_VELOCITY_COVARIANCE_ISOTROPY": structured["background_covariance_isotropy_fro"] < tol["structured_initial_isotropy_fro_max"],
            "Q09_DYNAMIC_INCOMPRESSIBILITY": structured["max_divergence_rel"] < tol["dynamic_divergence_rel_max"],
            "Q10_DYNAMIC_ENERGY_CONSERVATION": structured["base_energy_drift_rel_max"] < tol["dynamic_energy_drift_rel_max"],
            "Q11_RK4_LOCAL_CONVERGENCE": structured["rk4_one_step_vs_two_half_rel_l2"] < tol["rk4_local_convergence_rel_max"],
            "Q12_INITIAL_SPECTRAL_RESOLUTION": structured["spectral_edge_energy_fraction_initial"] < tol["spectral_edge_energy_fraction_initial_max"],
        }
        qualification.update({k: bool(v) for k, v in dynamic_qualification.items()})

        wave_exists = structured["all_probes_qualified"]
        isotropic = wave_exists and structured["direction_spread_relative"] <= float(wq["direction_spread_relative_max"])
        helicity = wave_exists and structured["helicity_split_relative"] <= float(wq["helicity_split_relative_max"])
        dispersion = wave_exists and structured["dispersion_relative"] <= float(wq["dispersion_relative_max"])
        coarse_same_sign = coarse["all_probes_qualified"] == structured["all_probes_qualified"]
        control_not_better = control["qualified_probe_count"] <= structured["qualified_probe_count"]
        hypothesis = {
            "H01_COHERENT_STRUCTURED_BULK_TRANSVERSE_POLE": wave_exists,
            "H02_DIRECTION_ISOTROPY": isotropic,
            "H03_HELICITY_DEGENERACY": helicity,
            "H04_APPROX_LINEAR_DISPERSION": dispersion,
            "H05_COARSE_RESOLUTION_SAME_QUALIFICATION_SIGN": coarse_same_sign,
            "H06_STRUCTURED_RESPONSE_NOT_WEAKER_THAN_SPECTRUM_MATCHED_RANDOM_CONTROL": control_not_better,
            "H07_FROZEN_BACKGROUND_COHERENT_POLE_DIAGNOSTIC": frozen["all_probes_qualified"],
        }
        hypothesis = {k: bool(v) for k, v in hypothesis.items()}
        core = all(hypothesis[k] for k in (
            "H01_COHERENT_STRUCTURED_BULK_TRANSVERSE_POLE",
            "H02_DIRECTION_ISOTROPY",
            "H03_HELICITY_DEGENERACY",
            "H04_APPROX_LINEAR_DISPERSION",
        ))
        chi = structured["candidate_bulk_cT_over_reference"] if core else None
    else:
        hypothesis = {
            "H01_COHERENT_STRUCTURED_BULK_TRANSVERSE_POLE": False,
            "H02_DIRECTION_ISOTROPY": False,
            "H03_HELICITY_DEGENERACY": False,
            "H04_APPROX_LINEAR_DISPERSION": False,
            "H05_COARSE_RESOLUTION_SAME_QUALIFICATION_SIGN": False,
            "H06_STRUCTURED_RESPONSE_NOT_WEAKER_THAN_SPECTRUM_MATCHED_RANDOM_CONTROL": False,
            "H07_FROZEN_BACKGROUND_COHERENT_POLE_DIAGNOSTIC": False,
        }
        core = False
        chi = None

    numerically_ok = all(qualification.values())
    if not numerically_ok:
        pipeline = "PREQUALIFICATION_FAILED"
        research = "INCONCLUSIVE_NUMERICAL_QUALIFICATION_FAILED"
    elif not rel_eq_ok:
        pipeline = "PREQUALIFICATION_QUALIFIED_WAVE_STAGE_SKIPPED"
        research = "INCONCLUSIVE_BACKGROUND_NOT_RELATIVE_EQUILIBRIUM_AT_V0.4.1"
    else:
        pipeline = "PIPELINE_QUALIFIED"
        research = (
            "SUPPORTED_STRUCTURED_EULER_BULK_TRANSVERSE_POLE_AT_V0.4.1_RESOLUTION"
            if core else
            "NO_QUALIFIED_STRUCTURED_EULER_BULK_TRANSVERSE_POLE_AT_V0.4.1_RESOLUTION"
        )

    blind_wave_gate = {
        "target_free_blind_observable": "chi_wave = c_T / v_ref",
        "reference_speed_definition": "Gamma_eff/(2*pi*sigma) after u_rms normalization",
        "wave_stage_executed": wave_stage_executed,
        "wave_qualified_before_any_external_target_comparison": bool(core),
        "chi_wave_if_qualified": chi,
        "target_values_present_in_blind_config": False,
        "guard": (
            "Master-Factor and particle-mass targets are reveal-only. v0.4.1 also requires "
            "the explicit Euler background to pass the relative-equilibrium precondition before "
            "the expensive wave stage is interpreted or, when the precondition fails, even executed."
        ),
    }

    def slim(obj):
        if obj is None:
            return {"executed": False, "reason": "relative-equilibrium precondition failed"}
        return {k: v for k, v in obj.items() if k != "probe_rows"}

    summary = {
        "catalog_id": "A049",
        "falsifier": "A049_isotropic_euler_vortex_shear_modulus_falsifier",
        "version": cfg["version"],
        "blind": True,
        "backend": backend_name(),
        "pipeline_status": pipeline,
        "research_question_status": research,
        "scope_guard": (
            "v0.4.1 is a qualification-first patch. A non-stationary structured Euler background "
            "cannot be used to make a physical claim about a bulk normal mode. The background is "
            "therefore tested against the translational relative-equilibrium condition before the "
            "costly evolving and frozen tangent-wave stages are run."
        ),
        "static_born_carry_forward": born,
        "relative_equilibrium_diagnostic": rel_eq,
        "relative_equilibrium_resolution_check": rel_eq_hi,
        "relative_equilibrium_resolution_delta": rel_eq_resolution_delta,
        "wave_stage_executed": wave_stage_executed,
        "structured_dynamic": slim(structured),
        "coarse_structured_control": slim(coarse),
        "spectrum_matched_random_control": slim(control),
        "frozen_background_tangent_diagnostic": slim(frozen),
        "bare_rest_euler_control": {
            "acceleration_operator_abs": rest_accel,
            "transverse_residual": rest_trans,
        },
        "qualification_gates": qualification,
        "precondition_gates": preconditions,
        "hypothesis_gates": hypothesis,
        "hypothesis_evaluation_status": (
            "EXECUTED" if wave_stage_executed else "NOT_EVALUATED_PRECONDITION_FAILED"
        ),
        "target_free_wave_hierarchy_gate": blind_wave_gate,
    }
    (out / "blind_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_csv(out / "static_born_scan.csv", born["rows"])
    if wave_stage_executed:
        _write_csv(out / "structured_probe_timeseries.csv", structured["probe_rows"])
        _write_csv(out / "coarse_structured_probe_timeseries.csv", coarse["probe_rows"])
        _write_csv(out / "spectrum_matched_random_control_timeseries.csv", control["probe_rows"])
        _write_csv(out / "frozen_background_probe_timeseries.csv", frozen["probe_rows"])

    report = [
        "# A049 v0.4.1 blind report", "",
        f"Backend: **{summary['backend']}**",
        f"Pipeline: **{pipeline}**",
        f"Research question: **{research}**", "",
        "## Relative-equilibrium prequalification", "",
        f"- primary grid N = {rel_eq['n']}",
        f"- fitted translation velocity = {rel_eq['translation_velocity_blind']}",
        f"- translation residual = {rel_eq['translation_residual_rel_l2']:.6e}",
        f"- raw state change at t={rel_eq['diagnostic_time']:.3f} = {rel_eq['raw_state_change_rel_l2']:.6e}",
        f"- co-moving state change = {rel_eq['comoving_state_change_rel_l2']:.6e}",
        f"- higher-resolution grid N = {rel_eq_hi['n']}",
        f"- higher-resolution translation residual = {rel_eq_hi['translation_residual_rel_l2']:.6e}",
        f"- residual resolution delta = {rel_eq_resolution_delta:.6e}",
        f"- wave stage executed = {wave_stage_executed}", "",
        "## Qualification gates", "",
    ]
    for k, v in qualification.items():
        report.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    report += ["", "## Precondition gates", ""]
    for k, v in preconditions.items():
        report.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    report += ["", "## Hypothesis gates", ""]
    if wave_stage_executed:
        for k, v in hypothesis.items():
            report.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    else:
        report.append("- NOT EVALUATED: relative-equilibrium precondition failed; expensive wave stage intentionally skipped.")
    report += [
        "", "## Target-free hierarchy observable", "",
        f"- qualified before reveal = {blind_wave_gate['wave_qualified_before_any_external_target_comparison']}",
        f"- chi_wave = {chi if chi is not None else 'NOT_REACHED'}", "",
        "## Scope guard", "", summary["scope_guard"],
    ]
    (out / "blind_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return summary
