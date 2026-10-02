from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from . import __version__
from .backend import load_backend, backend_info
from . import fallback
from .coherence import (normalized_wave_coherence, combination_phase, phase_lock_metrics,
                        cumulative_transfer_flux_proxy, instantaneous_frequency_stats,
                        modal_energy_proxy)
from .constants import V_SWIRL, R_C, GAMMA_SST, OMEGA0_SST, F0_SST
from .dynamics import projected_kelvin_analysis
from .ideal_ab import parse_ideal_ab, sample_ideal_ab
from .kelvin import (rankine_bending_branch, make_ring, ring_linear_mode, simulate_ring_modes,
                     phase_slope, enumerate_resonances)
from .orbit import search_relative_periodic_orbit
from .monodromy import full_relative_monodromy_fd


ROOT = Path(__file__).resolve().parents[1]


def _jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        if np.iscomplexobj(x):
            return [{"re": float(z.real), "im": float(z.imag)} for z in x.reshape(-1)] if x.ndim == 1 else _jsonable(x.tolist())
        return x.tolist()
    if isinstance(x, np.generic):
        return _jsonable(x.item())
    if isinstance(x, complex):
        return {"re": float(x.real), "im": float(x.imag)}
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(obj), indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            rr = {}
            for k in keys:
                v = r.get(k, "")
                if isinstance(v, (list, tuple, dict)):
                    v = json.dumps(_jsonable(v), separators=(",", ":"))
                rr[k] = v
            w.writerow(rr)


def _preset(name: str) -> dict[str, Any]:
    if name == "quick":
        return {
            "rankine_scan": 5000,
            "phase1_ring_n": 96, "phase1_dt": 0.003, "phase1_time": 0.48,
            "phase2_ring_n_coarse": 192, "phase2_ring_n": 256, "phase2_mmax": 7,
            "trefoil_n": 32, "trefoil_mmax": 4,
            "rpo_dt": 0.01, "rpo_time": 0.35,
            "phase3_ring_n": 128, "phase3_dt": 0.003, "phase3_time": 0.72,
            "phase4_ring_n": 128, "phase4_dt": 0.003, "phase4_time": 0.9,
            "chirality_n": 32,
        }
    if name == "full":
        return {
            "rankine_scan": 5000,
            "phase1_ring_n": 192, "phase1_dt": 0.002, "phase1_time": 0.8,
            "phase2_ring_n_coarse": 256, "phase2_ring_n": 384, "phase2_mmax": 10,
            "trefoil_n": 64, "trefoil_mmax": 7,
            "rpo_dt": 0.005, "rpo_time": 1.0,
            "phase3_ring_n": 256, "phase3_dt": 0.0015, "phase3_time": 1.2,
            "phase4_ring_n": 256, "phase4_dt": 0.0015, "phase4_time": 1.5,
            "chirality_n": 64,
        }
    raise ValueError("preset must be quick or full")


def run_phase1(out_dir: Path, *, preset: str = "quick", force_python: bool = False,
               skip_build: bool = False) -> dict[str, Any]:
    cfg = _preset(preset); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    xvals = [0.04, 0.06, 0.08, 0.10, 0.20, 0.50, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    rows = rankine_bending_branch(xvals, scan_points=cfg["rankine_scan"])
    write_csv(out_dir / "K0_rankine_paper_benchmark.csv", rows)
    small = [r for r in rows if r.get("root_found") and r["x"] <= 0.10]
    high = [r for r in rows if r.get("root_found") and r["x"] >= 6.0]
    small_err = max(abs(r["abs_omega_over_Omega0"] - r["long_wave_abs_over_Omega0"]) /
                    max(r["long_wave_abs_over_Omega0"], 1e-30) for r in small)
    high_err = max(abs(r["abs_omega_over_Omega0"] - r["high_k_abs_over_Omega0"]) /
                   max(r["high_k_abs_over_Omega0"], 1e-30) for r in high)
    residual_max = max(r.get("residual_abs", 0.0) for r in rows if r.get("root_found"))
    K0 = {"status": "PASS" if small_err < 0.12 and high_err < 0.12 and residual_max < 1e-4 else "FAIL",
          "small_x_max_relative_error": small_err, "high_x_relative_error": high_err,
          "max_root_residual": residual_max,
          "classification": "PAPER_EQUATION_NUMERICAL_REPRODUCTION"}

    backend, bname = load_backend(force_python=force_python, skip_build=skip_build)
    xs = np.array([0.01, 0.03, 0.05, 0.10, 0.20, 0.50, 1.0], dtype=float)
    hat = np.asarray(backend.kelvin_long_wave_hat_array(xs), dtype=float)
    core_rows = []
    for x, wh in zip(xs, hat):
        k = x / R_C
        f = abs(wh) * V_SWIRL / R_C / (2.0 * math.pi)
        # Hollow-core is a sensitivity comparator, not the SST core law.
        whc = float(backend.hollow_core_dispersion_si(k, R_C, GAMMA_SST, 1))
        core_rows.append({"kr_c": x, "omega_hat_longwave": wh,
                          "frequency_longwave_Hz": f, "omega_hollow_rad_s": whc,
                          "frequency_hollow_Hz": abs(whc)/(2.0*math.pi)})
    write_csv(out_dir / "K1_SST_core_model_scales.csv", core_rows)
    K1 = {"status": "PASS", "classification": "SST_SCALE_DIAGNOSTIC_WITH_CORE_MODEL_SENSITIVITY",
          "Gamma_SST_m2_s": GAMMA_SST, "v_swirl_over_rc_s_inv": OMEGA0_SST,
          "f0_Hz": F0_SST, "backend": bname}

    # Native/Python parity for both the Kelvin kernel and regularised Biot-Savart.
    pyhat = fallback.kelvin_long_wave_hat_array(xs)
    kelvin_parity = float(np.max(np.abs(hat - pyhat)))
    ring = make_ring(24, 1.0)
    vfast = np.asarray(backend.induced_velocity(ring, ring, 1.0, 0.05), dtype=float)
    vpy = np.asarray(fallback.induced_velocity(ring, ring, 1.0, 0.05), dtype=float)
    bs_parity = float(np.max(np.abs(vfast - vpy)))
    if force_python:
        K2 = {"status": "SKIP", "reason": "FORCE_PYTHON__NATIVE_PARITY_NOT_TESTED",
              "kelvin_max_abs_same_backend": kelvin_parity, "biot_savart_max_abs_same_backend": bs_parity,
              "classification": "NATIVE_FALLBACK_PARITY"}
    else:
        K2 = {"status": "PASS" if kelvin_parity < 1e-12 and bs_parity < 5e-11 else "FAIL",
              "kelvin_max_abs_cpp_python": kelvin_parity, "biot_savart_max_abs_cpp_python": bs_parity,
              "classification": "NATIVE_FALLBACK_PARITY"}

    amplitudes = [0.005, 0.02, 0.05] if preset == "quick" else [0.005, 0.01, 0.03, 0.05, 0.10]
    amp_rows = []
    for A in amplitudes:
        sim = simulate_ring_modes(n=cfg["phase1_ring_n"], modes=[3], initial_amplitudes={3: A+0j},
                                  eps_over_R=0.05, dt_hat=cfg["phase1_dt"], time_hat=cfg["phase1_time"],
                                  sample_stride=2, force_python=force_python, skip_build=True)
        fit = phase_slope(sim["times"], sim["amplitudes"][3])
        amp_rows.append({"amplitude_over_R": A, "steepness_proxy_mA_over_R": 3*A,
                         "omega_hat": fit["omega_hat"], "phase_rms": fit["phase_rms"],
                         "amp_mean": fit["amp_mean"]})
    write_csv(out_dir / "K3_ring_amplitude_sweep.csv", amp_rows)
    good = [r for r in amp_rows if r["omega_hat"] is not None and np.isfinite(r["omega_hat"])]
    if len(good) >= 3:
        aa = np.array([r["amplitude_over_R"]**2 for r in good]); ww = np.array([r["omega_hat"] for r in good])
        coef = np.polyfit(aa, ww, 1)
        K3 = {"status": "PASS", "omega0_hat_extrapolated": float(coef[1]),
              "nonlinear_shift_coefficient_hat_per_A2": float(coef[0]),
              "classification": "NONLINEAR_BIOT_SAVART_AMPLITUDE_SWEEP"}
    else:
        K3 = {"status": "FAIL", "classification": "NONLINEAR_BIOT_SAVART_AMPLITUDE_SWEEP"}

    summary = {"phase": "I", "version": __version__, "preset": preset,
               "description": "Paper benchmark + straight/core scales + native parity + weak-amplitude ring diagnostic",
               "gates": {"K0": K0, "K1": K1, "K2": K2, "K3": K3}}
    write_json(out_dir / "phase1_summary.json", summary)
    return summary


def run_phase2(out_dir: Path, *, preset: str = "quick", force_python: bool = False,
               skip_build: bool = False) -> dict[str, Any]:
    cfg = _preset(preset); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    coarse_n = cfg["phase2_ring_n_coarse"]; fine_n = cfg["phase2_ring_n"]
    modes = list(range(2, cfg["phase2_mmax"] + 1))
    ring_rows = []
    for m in modes:
        a = ring_linear_mode(m, n=coarse_n, eps_over_R=0.05, force_python=force_python, skip_build=skip_build)
        b = ring_linear_mode(m, n=fine_n, eps_over_R=0.05, force_python=force_python, skip_build=True)
        x = m * 0.05
        bracket = math.log(2.0/x) - 0.5772156649015329 + 0.25
        lw = abs(m*m*bracket)
        conv = abs(b["omega_hat"] - a["omega_hat"]) / max(abs(b["omega_hat"]), 1e-30)
        ring_rows.append({"mode": m, "N_coarse": coarse_n, "N_fine": fine_n,
                          "omega_hat_coarse": a["omega_hat"], "omega_hat_fine": b["omega_hat"],
                          "growth_hat_fine": b["growth_hat"], "quality_re_over_im": b["quality_re_over_im"],
                          "resolution_relative_change": conv, "straight_longwave_omega_hat": lw,
                          "curvature_fractional_shift": (b["omega_hat"]-lw)/max(lw,1e-30)})
    write_csv(out_dir / "K4_ring_linear_spectrum.csv", ring_rows)
    med_conv = float(np.median([r["resolution_relative_change"] for r in ring_rows]))
    ds_over_eps_coarse = (2.0 * math.pi / coarse_n) / 0.05
    ds_over_eps_fine = (2.0 * math.pi / fine_n) / 0.05
    K4 = {"status": "PASS" if med_conv < (0.08 if preset == "quick" else 0.05) else "WARN",
          "median_resolution_relative_change": med_conv,
          "ds_over_eps_coarse": ds_over_eps_coarse, "ds_over_eps_fine": ds_over_eps_fine,
          "classification": "REGULARIZED_BIOT_SAVART_RING_LINEARIZATION"}

    ideal_path = ROOT / "data" / "ideal_3_1_1.txt"
    model = parse_ideal_ab(ideal_path, "3:1:1")
    center = sample_ideal_ab(model, cfg["trefoil_n"])
    trefoil_rows = []
    for m in range(1, cfg["trefoil_mmax"] + 1):
        try:
            a = projected_kelvin_analysis(center, D=model.D, offset_over_D=0.25, eps_over_D=0.10,
                                          fd_step_over_D=2e-5, gamma_plus=1.0, gamma_minus=-1.0,
                                          channel_phase=math.pi/2, mode_m=m, force_python=force_python,
                                          skip_build=True)
            trefoil_rows.append({"mode_m": m, "omega_positive_hat": a["omega_positive_hat"],
                                 "omega_negative_abs_hat": a["omega_negative_abs_hat"],
                                 "positive_quality_re_over_im": a["positive_quality_re_over_im"],
                                 "negative_quality_re_over_im": a["negative_quality_re_over_im"],
                                 "relative_equilibrium_residual": a["rigid"]["relative_equilibrium_residual"],
                                 "classification": "FROZEN_LOCAL_KELVIN_SPECTRUM"})
        except Exception as exc:
            trefoil_rows.append({"mode_m": m, "error": str(exc), "classification": "FROZEN_LOCAL_KELVIN_SPECTRUM"})
    write_csv(out_dir / "K5_trefoil_frozen_kelvin_spectrum.csv", trefoil_rows)
    ok_t = [r for r in trefoil_rows if "omega_positive_hat" in r]
    K5 = {"status": "PASS" if ok_t else "FAIL", "modes_resolved": len(ok_t),
          "classification": "FROZEN_LOCAL_ONLY_NOT_FLOQUET_UNLESS_RPO_PASSES"}

    rpo = search_relative_periodic_orbit(center, D=model.D, offset_over_D=0.25, eps_over_D=0.10,
                                         channel_phase=math.pi/2, dt_hat=cfg["rpo_dt"],
                                         max_time_hat=cfg["rpo_time"], min_time_hat=0.06,
                                         snapshot_stride=2, recurrence_tol_over_D=0.05,
                                         force_python=force_python, skip_build=True)
    cand = rpo["candidate"]
    write_json(out_dir / "K6_rpo_candidate.json", {k:v for k,v in rpo.items() if k not in {"initial_state","terminal_state","trajectory"}})
    if cand["accepted"]:
        try:
            x0 = np.asarray(rpo["initial_state"], dtype=float)
            mono = full_relative_monodromy_fd(x0, D=model.D, period_hat=cand["period_hat"],
                                              dt_hat=cfg["rpo_dt"],
                                              shift=cand["shift"], rotation=np.asarray(cand["rotation"]),
                                              translation=np.asarray(cand["translation_over_D"])*model.D,
                                              eps_over_D=0.10, gamma_plus=1.0, gamma_minus=-1.0,
                                              fd_step_over_D=2e-5, max_n=max(24, len(center)),
                                              force_python=force_python, skip_build=True)
            write_json(out_dir / "K6_true_monodromy.json", mono)
            K6 = {"status": "PASS", "rpo_accepted": True, "monodromy_constructed": True,
                  "classification": "TRUE_RELATIVE_FLOQUET"}
        except Exception as exc:
            K6 = {"status": "FAIL", "rpo_accepted": True, "monodromy_constructed": False,
                  "error": str(exc), "classification": "TRUE_RELATIVE_FLOQUET"}
    else:
        K6 = {"status": "SKIP", "rpo_accepted": False, "monodromy_constructed": False,
              "recurrence_rms_over_D": cand["recurrence_rms_over_D"],
              "endpoint_vectorfield_error": cand["endpoint_vectorfield_error"],
              "reason": "NO_RPO__TRUE_FLOQUET_SCIENTIFICALLY_LOCKED",
              "classification": "STRICT_RPO_GATE"}

    summary = {"phase": "II", "version": __version__, "preset": preset,
               "description": "Ring curvature -> trefoil frozen spectrum -> strict RPO/true-Floquet gate",
               "ring_spectrum": ring_rows, "trefoil_spectrum": trefoil_rows,
               "gates": {"K4": K4, "K5": K5, "K6": K6}}
    write_json(out_dir / "phase2_summary.json", summary)
    return summary


def run_phase3(out_dir: Path, phase2: dict[str, Any], *, preset: str = "quick",
               force_python: bool = False) -> dict[str, Any]:
    cfg = _preset(preset); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    freqs = {int(r["mode"]): float(r["omega_hat_fine"]) for r in phase2["ring_spectrum"]}
    r4 = enumerate_resonances(freqs, 4, top_n=80)
    r6 = enumerate_resonances(freqs, 6, top_n=120)
    write_csv(out_dir / "K7_four_wave_resonances.csv", r4)
    write_csv(out_dir / "K7_six_wave_resonances.csv", r6)
    K7 = {"status": "PASS" if r6 else "FAIL", "four_wave_candidates": len(r4),
          "six_wave_candidates": len(r6),
          "best_four_relative_detuning": r4[0]["relative_detuning"] if r4 else None,
          "best_six_relative_detuning": r6[0]["relative_detuning"] if r6 else None,
          "classification": "BLIND_RESONANCE_ENUMERATION_FROM_NUMERICAL_RING_SPECTRUM"}

    if not r6:
        summary = {"phase":"III","version":__version__,"preset":preset,"gates":{"K7":K7,"K8":{"status":"SKIP"},"K9":{"status":"SKIP"}}}
        write_json(out_dir / "phase3_summary.json", summary); return summary
    best6 = r6[0]
    unique = sorted(set(best6["incoming"] + best6["outgoing"]))
    init = {m: 0.006 * np.exp(1j * (0.37*m + 0.11*m*m)) for m in unique}
    all_modes = sorted(freqs)
    sim = simulate_ring_modes(n=cfg["phase3_ring_n"], modes=all_modes, initial_amplitudes=init,
                              eps_over_R=0.05, dt_hat=cfg["phase3_dt"], time_hat=cfg["phase3_time"],
                              sample_stride=2, force_python=force_python, skip_build=True)
    theta = combination_phase(sim["amplitudes"], best6["incoming"], best6["outgoing"])
    lock = phase_lock_metrics(sim["times"], theta)
    energies = modal_energy_proxy(sim["amplitudes"])
    exchange = {}
    for m in unique:
        e = energies[m]
        exchange[m] = float((np.max(e)-np.min(e))/max(np.mean(e),1e-30))
    K8 = {"status": "DIAGNOSTIC", "selected_sextet": best6, "phase_lock_metrics": lock,
          "relative_energy_exchange_by_mode": exchange,
          "classification": "FULL_NONLINEAR_REGULARIZED_BIOT_SAVART_SEXTET_SEED"}

    p6 = normalized_wave_coherence(sim["amplitudes"], best6["incoming"], best6["outgoing"])
    best4 = r4[0] if r4 else None
    p4 = normalized_wave_coherence(sim["amplitudes"], best4["incoming"], best4["outgoing"]) if best4 else None
    control = r6[min(len(r6)-1, 40)] if len(r6)>1 else best6
    p6_control = normalized_wave_coherence(sim["amplitudes"], control["incoming"], control["outgoing"])
    K9 = {"status": "DIAGNOSTIC", "pentacoherence_best6": p6, "tricoherence_best4": p4,
          "control_sextet": control, "pentacoherence_control": p6_control,
          "classification": "HIGHER_ORDER_PHASE_COHERENCE_DIAGNOSTIC"}
    write_json(out_dir / "K8_K9_sextet_diagnostics.json", {"K8":K8,"K9":K9})
    # compact modal time series CSV
    rows=[]
    for i,t in enumerate(sim["times"]):
        row={"time_hat":float(t)}
        for m in all_modes:
            z=sim["amplitudes"][m][i]; row[f"a{m}_re"]=float(z.real); row[f"a{m}_im"]=float(z.imag)
        rows.append(row)
    write_csv(out_dir / "sextet_modal_timeseries.csv", rows)
    summary = {"phase":"III","version":__version__,"preset":preset,
               "description":"Blind resonance search -> isolated sextet seed -> 4/6-wave coherence",
               "gates":{"K7":K7,"K8":K8,"K9":K9}}
    write_json(out_dir / "phase3_summary.json", summary)
    return summary


def run_phase4(out_dir: Path, phase2: dict[str, Any], *, preset: str = "quick",
               force_python: bool = False) -> dict[str, Any]:
    cfg = _preset(preset); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    freqs={int(r["mode"]):float(r["omega_hat_fine"]) for r in phase2["ring_spectrum"]}
    modes=sorted(freqs)
    rng=np.random.default_rng(20260810)
    pump=[m for m in modes if m<=4]
    init={m:0.012*np.exp(1j*float(rng.uniform(0,2*math.pi))) for m in pump}
    sim=simulate_ring_modes(n=cfg["phase4_ring_n"],modes=modes,initial_amplitudes=init,
                            eps_over_R=0.05,dt_hat=cfg["phase4_dt"],time_hat=cfg["phase4_time"],
                            sample_stride=2,force_python=force_python,skip_build=True)
    e=modal_energy_proxy(sim["amplitudes"])
    e0=sum(float(v[0]) for v in e.values()); ef=sum(float(v[-1]) for v in e.values())
    high=[m for m in modes if m>max(pump)]
    high0=sum(float(e[m][0]) for m in high); highf=sum(float(e[m][-1]) for m in high)
    K10={"status":"DIAGNOSTIC","initial_band":pump,
         "high_mode_fraction_initial":high0/max(e0,1e-30),"high_mode_fraction_final":highf/max(ef,1e-30),
         "classification":"UNFORCED_BROADBAND_TRANSFER_DIAGNOSTIC_NOT_STATIONARY_TURBULENCE"}
    flux=cumulative_transfer_flux_proxy(sim["times"],sim["amplitudes"])
    vals=np.array([flux[m] for m in modes[1:-1]],dtype=float) if len(modes)>2 else np.array([])
    plateau_cv=float(np.std(vals)/max(abs(np.mean(vals)),1e-30)) if len(vals) else None
    K11={"status":"DIAGNOSTIC","flux_proxy_by_cutoff":flux,"plateau_coefficient_of_variation":plateau_cv,
         "classification":"UNFORCED_CUMULATIVE_ENERGY_TRANSFER_PROXY"}
    ts=[]
    sep_pass=0
    for m in modes:
        stat=instantaneous_frequency_stats(sim["times"],sim["amplitudes"][m])
        tau_lin=1.0/max(abs(freqs[m]),1e-30); tau_nl=stat["tau_nl_hat"]
        good=bool(np.isfinite(tau_nl) and tau_lin<tau_nl<cfg["phase4_time"])
        sep_pass += int(good)
        ts.append({"mode":m,"tau_linear_hat":tau_lin,"tau_nonlinear_hat":tau_nl,
                   "omega_mean_hat":stat["omega_mean_hat"],"delta_omega_hat":stat["delta_omega_hat"],
                   "separation_within_run":good})
    write_csv(out_dir / "K12_timescale_separation.csv", ts)
    K12={"status":"PASS" if sep_pass>=max(1,len(modes)//3) else "WARN","modes_passing":sep_pass,
         "modes_total":len(modes),"classification":"FINITE_RUN_WEAK_NONLINEAR_TIMESCALE_DIAGNOSTIC"}

    model=parse_ideal_ab(ROOT/"data"/"ideal_3_1_1.txt","3:1:1")
    base=sample_ideal_ab(model,cfg["chirality_n"])
    chir=[]
    for mirror in [False,True]:
        c=base.copy()
        if mirror: c[:,0]*=-1.0
        for sign in [1.0,-1.0]:
            try:
                a=projected_kelvin_analysis(c,D=model.D,offset_over_D=0.25,eps_over_D=0.10,
                                            fd_step_over_D=2e-5,gamma_plus=sign,gamma_minus=-sign,
                                            channel_phase=math.pi/2,mode_m=1,force_python=force_python,skip_build=True)
                chir.append({"mirror":mirror,"circulation_sign":int(sign),
                             "omega_plus_hat":a["omega_positive_hat"],"omega_minus_hat":a["omega_negative_abs_hat"],
                             "relative_equilibrium_residual":a["rigid"]["relative_equilibrium_residual"]})
            except Exception as exc:
                chir.append({"mirror":mirror,"circulation_sign":int(sign),"error":str(exc)})
    write_csv(out_dir / "K13_chirality_four_configurations.csv",chir)
    def get(mi,sg):
        return next((r for r in chir if r.get("mirror")==mi and r.get("circulation_sign")==sg and "omega_plus_hat" in r),None)
    pairs=[]
    for akey,bkey in [((False,1),(True,-1)),((False,-1),(True,1))]:
        a=get(*akey); b=get(*bkey)
        if a and b:
            pairs.append(abs(a["omega_plus_hat"]-b["omega_plus_hat"])/max(0.5*(abs(a["omega_plus_hat"])+abs(b["omega_plus_hat"])),1e-30))
    K13={"status":"DIAGNOSTIC" if len(chir)==4 and all("omega_plus_hat" in r for r in chir) else "WARN",
         "parity_circulation_partner_relative_differences":pairs,
         "classification":"FOUR_CONFIGURATION_CHIRALITY_SYMMETRY_AUDIT"}

    forbidden=["7.297" + "352", "137." + "035", "137." + "036"]
    hits=[]
    for path in list((ROOT/"sst_kelvin_workbench").glob("*.py"))+[ROOT/"cpp"/"native.cpp"]:
        text=path.read_text(encoding="utf-8",errors="ignore")
        for pat in forbidden:
            if pat in text: hits.append({"file":str(path.relative_to(ROOT)),"pattern":pat})
    K14={"status":"PASS" if not hits else "FAIL","forbidden_target_hits":hits,
         "classification":"TARGET_BLIND_SOURCE_SCAN"}

    rows=[]
    for i,t in enumerate(sim["times"]):
        row={"time_hat":float(t),"energy_proxy":float(sim["energy_proxy"][i])}
        for m in modes:
            z=sim["amplitudes"][m][i]; row[f"a{m}_re"]=float(z.real); row[f"a{m}_im"]=float(z.imag)
        rows.append(row)
    write_csv(out_dir/"broadband_modal_timeseries.csv",rows)
    summary={"phase":"IV","version":__version__,"preset":preset,
             "description":"Broadband transfer + flux proxy + timescales + chirality + target-blind lock",
             "gates":{"K10":K10,"K11":K11,"K12":K12,"K13":K13,"K14":K14}}
    write_json(out_dir/"phase4_summary.json",summary)
    return summary


def run_all(out_dir: Path, *, preset: str = "quick", force_python: bool = False,
            force_build: bool = False) -> dict[str, Any]:
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    if force_build and not force_python:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=True,verbose=True)
    p1=run_phase1(out_dir/"phase1",preset=preset,force_python=force_python,skip_build=False)
    p2=run_phase2(out_dir/"phase2",preset=preset,force_python=force_python,skip_build=True)
    p3=run_phase3(out_dir/"phase3",p2,preset=preset,force_python=force_python)
    p4=run_phase4(out_dir/"phase4",p2,preset=preset,force_python=force_python)
    statuses={}
    for p in [p1,p2,p3,p4]:
        for k,v in p.get("gates",{}).items(): statuses[k]=v.get("status")
    hard_fail=[k for k,s in statuses.items() if s=="FAIL"]
    summary={"package":"SST Kelvin/Floquet Workbench","version":__version__,"preset":preset,
             "backend":backend_info(force_python=force_python,skip_build=True),
             "gate_statuses":statuses,"hard_failures":hard_fail,
             "scientific_note":"SKIP at K6 is intentional when no accepted RPO exists; no true Floquet claim is then made.",
             "phases":{"I":p1,"II":p2,"III":p3,"IV":p4}}
    write_json(out_dir/"audit_summary.json",summary)
    return summary
