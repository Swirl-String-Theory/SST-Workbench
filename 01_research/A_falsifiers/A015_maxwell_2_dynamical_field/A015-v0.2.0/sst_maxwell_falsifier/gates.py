from __future__ import annotations
import numpy as np
from .metrics import EPS, fit_affine, fit_powerlaw, nrmse, rms


def _invalid(name, reasons, metrics=None):
    return {"gate": name, "status": "INVALID", "reasons": list(reasons), "metrics": metrics or {}}


def _finish(name, conditions, metrics, notes=None):
    failed = [k for k, ok in conditions.items() if not bool(ok)]
    return {
        "gate": name,
        "status": "PASS" if not failed else "FAIL",
        "failed_conditions": failed,
        "conditions": {k: bool(v) for k, v in conditions.items()},
        "metrics": metrics,
        "notes": notes or []
    }


def transverse_gate(arr, meta, cfg):
    required = ["kvec", "omega", "Avec"]
    missing = [k for k in required if k not in arr]
    if missing:
        return _invalid("DFC-T", [f"missing array {k}" for k in missing])
    invalid_flags = []
    for k in ["projector_applied", "gauge_reduced_input", "divergence_constraint_enforced"]:
        if meta.get(k, None) is not False:
            invalid_flags.append(f"metadata must declare {k}=false")
    if invalid_flags:
        return _invalid("DFC-T", invalid_flags)

    kvec = np.asarray(arr["kvec"], float)
    omega = np.asarray(arr["omega"], float).reshape(-1)
    Avec = np.asarray(arr["Avec"])
    if kvec.ndim != 2 or kvec.shape[1] != 3 or Avec.shape != kvec.shape or len(omega) != len(kvec):
        return _invalid("DFC-T", ["kvec and Avec must be Nx3 and omega must be N"])
    kmag = np.linalg.norm(kvec, axis=1)
    valid = kmag > 0
    if np.count_nonzero(valid) < 8:
        return _invalid("DFC-T", ["fewer than 8 nonzero-k modes"])
    khat = np.zeros_like(kvec)
    khat[valid] = kvec[valid] / kmag[valid, None]
    denom = np.sum(np.abs(Avec) ** 2, axis=1)
    dot = np.sum(khat * Avec, axis=1)
    lf = np.abs(dot) ** 2 / np.maximum(denom, EPS)
    power = np.asarray(arr.get("mode_power", denom), float).reshape(-1)
    if len(power) != len(omega):
        return _invalid("DFC-T", ["mode_power must be N"])

    t = cfg["thresholds"]["transverse"]
    maxw = float(np.max(np.abs(omega)))
    if maxw <= 0:
        return _invalid("DFC-T", ["all mode frequencies are zero"])
    rad = valid & (np.abs(omega) > t["radiative_frequency_fraction"] * maxw)
    trans = rad & (lf <= t["transverse_mode_lf_max"])
    if np.count_nonzero(trans) < 6:
        return _invalid("DFC-T", ["fewer than 6 transverse-dominated radiative modes"])

    rad_long_power = float(np.sum(power[rad] * lf[rad]) / max(np.sum(power[rad]), EPS))
    a, b, r2 = fit_affine(kmag[trans] ** 2, omega[trans] ** 2)
    cfit = float(np.sqrt(a)) if a > 0 else float("nan")
    kmed = float(np.median(kmag[trans]))
    gap_ratio = float(abs(b) / max(a * kmed * kmed, EPS)) if a > 0 else float("inf")
    long_dom = rad & (lf >= t["longitudinal_dominated_lf_min"])
    phase_speed = np.zeros_like(omega)
    phase_speed[valid] = np.abs(omega[valid]) / kmag[valid]
    long_fast = long_dom & np.isfinite(cfit) & (phase_speed >= t["longitudinal_phase_speed_fraction_min"] * cfit)

    equip = None
    if "E_kin" in arr and "E_el" in arr:
        ek = np.asarray(arr["E_kin"], float).reshape(-1)
        ee = np.asarray(arr["E_el"], float).reshape(-1)
        if len(ek) == len(omega) and len(ee) == len(omega):
            emask = trans & (ek > 0) & (ee > 0)
            if np.any(emask):
                equip = float(np.median(np.abs(np.log(ek[emask] / ee[emask]))))

    conditions = {
        "radiative_longitudinal_power": rad_long_power <= t["radiative_longitudinal_power_max"],
        "transverse_dispersion_r2": r2 >= t["dispersion_r2_min"],
        "transverse_gap_ratio": gap_ratio <= t["transverse_gap_ratio_max"],
        "no_fast_longitudinal_branch": not bool(np.any(long_fast)),
    }
    if equip is not None:
        conditions["wave_equipartition"] = equip <= t["equipartition_median_abs_log_ratio_max"]

    metrics = {
        "n_modes": int(len(omega)),
        "n_radiative": int(np.count_nonzero(rad)),
        "n_transverse_fit": int(np.count_nonzero(trans)),
        "n_fast_longitudinal": int(np.count_nonzero(long_fast)),
        "radiative_longitudinal_power_fraction": rad_long_power,
        "dispersion_a_speed_squared": a,
        "dispersion_b_gap_squared": b,
        "transverse_speed_blind": cfit,
        "dispersion_r2": r2,
        "transverse_gap_ratio": gap_ratio,
        "equipartition_median_abs_log_ratio": equip,
        "unit_system": meta.get("unit_system", "unspecified")
    }
    return _finish("DFC-T", conditions, metrics, ["No external value of c is used in this gate."])


def _fit_K(xi, P):
    B, *_ = np.linalg.lstsq(xi, P, rcond=None)  # xi @ B = P
    return B


def displacement_gate(arr, meta, cfg):
    required = ["kvec", "omega", "xi", "P", "J", "rho_bound"]
    missing = [k for k in required if k not in arr]
    if missing:
        return _invalid("DFC-D", [f"missing array {k}" for k in missing])
    independent_flags = ["xi_independent", "P_independent", "J_independent", "rho_bound_independent"]
    bad = [f"metadata must declare {k}=true" for k in independent_flags if meta.get(k, None) is not True]
    if bad:
        return _invalid("DFC-D", bad)

    kvec = np.asarray(arr["kvec"], float)
    omega = np.asarray(arr["omega"], float).reshape(-1)
    xi = np.asarray(arr["xi"])
    P = np.asarray(arr["P"])
    J = np.asarray(arr["J"])
    rho = np.asarray(arr["rho_bound"]).reshape(-1)
    n = len(omega)
    if any(x.shape != (n, 3) for x in [kvec, xi, P, J]) or len(rho) != n:
        return _invalid("DFC-D", ["kvec, xi, P, J must be Nx3 and rho_bound must be N"])
    if n < 30:
        return _invalid("DFC-D", ["at least 30 samples are required for train/holdout testing"])

    rng = np.random.default_rng(int(cfg["split_seed"]))
    idx = rng.permutation(n)
    ntrain = max(9, int(round(cfg["train_fraction"] * n)))
    tr, te = idx[:ntrain], idx[ntrain:]
    if len(te) < 6:
        return _invalid("DFC-D", ["holdout set has fewer than 6 samples"])
    B = _fit_K(xi[tr], P[tr])
    Ppred = xi[te] @ B
    epsP = nrmse(Ppred, P[te])

    half = len(tr) // 2
    B1 = _fit_K(xi[tr[:half]], P[tr[:half]])
    B2 = _fit_K(xi[tr[half:]], P[tr[half:]])
    stab = rms(B1 - B2) / max(0.5 * (rms(B1) + rms(B2)), EPS)

    Jexp = -1j * omega[:, None] * P
    rhoexp = -1j * np.sum(kvec * P, axis=1)
    cont = -1j * omega * rho + 1j * np.sum(kvec * J, axis=1)
    epsJ = nrmse(Jexp, J)
    epsR = nrmse(rhoexp, rho)
    cont_scale = max(rms(omega * rho), rms(np.sum(kvec * J, axis=1)), EPS)
    epsC = rms(cont) / cont_scale

    t = cfg["thresholds"]["displacement"]
    conditions = {
        "heldout_constitutive_closure": epsP <= t["holdout_nrmse_max"],
        "polarization_current_closure": epsJ <= t["current_nrmse_max"],
        "bound_charge_closure": epsR <= t["bound_charge_nrmse_max"],
        "continuity_closure": epsC <= t["continuity_nrmse_max"],
        "coefficient_stability": stab <= t["coefficient_stability_max"],
    }
    metrics = {
        "n_samples": n,
        "n_train": int(len(tr)),
        "n_holdout": int(len(te)),
        "holdout_P_nrmse": epsP,
        "J_nrmse": epsJ,
        "rho_bound_nrmse": epsR,
        "continuity_nrmse": epsC,
        "coefficient_stability": stab,
        "K_fit_matrix_xi_to_P": B,
        "K_fit_imaginary_fraction": rms(B.imag) / max(rms(B), EPS),
        "unit_system": meta.get("unit_system", "unspecified")
    }
    return _finish("DFC-D", conditions, metrics, ["K_P is fitted only on the preregistered training subset."])


def gravity_gate(arr, meta, cfg):
    required = ["d", "E_total", "F_independent", "E_infinity", "rho_E_min", "rho_E_scale"]
    missing = [k for k in required if k not in arr]
    if missing:
        return _invalid("DFC-G", [f"missing array {k}" for k in missing])
    bad = []
    for k in ["same_hamiltonian", "fully_relaxed", "force_independent"]:
        if meta.get(k, None) is not True:
            bad.append(f"metadata must declare {k}=true")
    if bad:
        return _invalid("DFC-G", bad)

    d = np.asarray(arr["d"], float).reshape(-1)
    E = np.asarray(arr["E_total"], float).reshape(-1)
    F = np.asarray(arr["F_independent"], float).reshape(-1)
    rmin = np.asarray(arr["rho_E_min"], float).reshape(-1)
    rscale = np.asarray(arr["rho_E_scale"], float).reshape(-1)
    Einf_arr = np.asarray(arr["E_infinity"], float).reshape(-1)
    if len(Einf_arr) != 1:
        return _invalid("DFC-G", ["E_infinity must be a scalar stored as a one-element array"])
    n = len(d)
    if any(len(x) != n for x in [E, F, rmin, rscale]) or n < 8:
        return _invalid("DFC-G", ["d, E_total, F_independent, rho_E_min, rho_E_scale must have equal length >= 8"])
    order = np.argsort(d)
    d, E, F, rmin, rscale = [x[order] for x in [d, E, F, rmin, rscale]]
    if np.any(np.diff(d) <= 0):
        return _invalid("DFC-G", ["separations d must be unique and strictly increasing"])
    U = E - float(Einf_arr[0])
    dU = np.gradient(U, d, edge_order=2)
    FH = -dU
    core = np.zeros(n, dtype=bool)
    core[1:-1] = True
    if np.count_nonzero(core) < 6:
        core[:] = True

    epsF = nrmse(FH[core], F[core])
    negU = float(np.mean(U[core] < 0))
    posSlope = float(np.mean(dU[core] > 0))
    attrF = float(np.mean(F[core] < 0))
    t = cfg["thresholds"]["gravity"]
    energy_ok_mask = rmin >= -t["absolute_energy_negative_tolerance_fraction"] * np.maximum(np.abs(rscale), EPS)
    energy_ok = bool(np.all(energy_ok_mask))
    nU, r2U = fit_powerlaw(d[core], U[core])
    nF, r2F = fit_powerlaw(d[core], F[core])

    conditions = {
        "negative_interaction_energy": negU >= t["negative_interaction_fraction_min"],
        "positive_energy_slope": posSlope >= t["positive_energy_slope_fraction_min"],
        "independent_force_is_attractive": attrF >= t["attractive_force_fraction_min"],
        "force_matches_energy_derivative": epsF <= t["force_energy_nrmse_max"],
        "absolute_energy_nonnegative": energy_ok,
    }
    metrics = {
        "n_separations": n,
        "negative_interaction_fraction": negU,
        "positive_dU_dd_fraction": posSlope,
        "attractive_force_fraction": attrF,
        "force_energy_nrmse": epsF,
        "min_absolute_energy_guard_margin": float(np.min(rmin + t["absolute_energy_negative_tolerance_fraction"] * np.maximum(np.abs(rscale), EPS))),
        "blind_potential_exponent_n_U": nU,
        "blind_potential_exponent_r2": r2U,
        "blind_force_exponent_n_F": nF,
        "blind_force_exponent_r2": r2F,
        "E_infinity": float(Einf_arr[0]),
        "unit_system": meta.get("unit_system", "unspecified")
    }
    return _finish("DFC-G", conditions, metrics, ["Newtonian exponents are reported but are not used in blind pass/fail."])
