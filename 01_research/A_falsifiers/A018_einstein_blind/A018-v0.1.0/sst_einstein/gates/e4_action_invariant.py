from __future__ import annotations
import numpy as np
from ..geometry import ring, kelvin_ring
from ..simulation import evolve, PhysicalScale
from .. import native
from ..metrics import phase_frequency, loglog_slope

GATE="E4"

def _measure(ampl: float, cfg: dict, scale: PhysicalScale, mode: int, boost=(0,0,0)) -> dict:
    n=int(cfg["simulation"]["n_points"])
    base=ring(n,1.0)
    pert=kelvin_ring(n,1.0,ampl,mode,0.0,True)
    e0=native.filament_energy(base,scale.core_dimless,1.0,1.0)*scale.energy_J
    e1=native.filament_energy(pert,scale.core_dimless,1.0,1.0)*scale.energy_J
    dE=float(e1-e0)
    sim=evolve(pert,cfg,scale,uniform_dimless=boost,mode=mode,record_points=False)
    freq=phase_frequency(sim["time_s"],sim["kelvin_mode"],min_power=1e-30)
    J=float(dE/freq["nu_Hz"]) if freq.get("ok") and dE>0 else float("nan")
    return {"amplitude_over_R":float(ampl),"deltaE_J":dE,"frequency":{k:v for k,v in freq.items() if k!="phase"},
            "J_blind_J_s":J,"boost_dimless":list(boost)}

def run(cfg: dict, scale: PhysicalScale, outdir, rng=None, external_curves=None) -> dict:
    gc=cfg["gates"]["E4"]; mode=int(gc.get("mode",2)); amps=[float(x) for x in gc["amplitudes"]]
    cases=[_measure(a,cfg,scale,mode) for a in amps]
    valid=[c for c in cases if np.isfinite(c["J_blind_J_s"]) and c["frequency"]["phase_fit_r2"]>=gc["thresholds"]["phase_fit_r2_min"] and c["frequency"]["phase_span_rad"]>=gc["thresholds"]["phase_span_rad_min"]]
    if len(valid)<int(gc["thresholds"]["min_valid_amplitudes"]):
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Insufficient resolved mode-frequency measurements.","cases":cases,"thresholds":gc["thresholds"]}
    A=np.array([c["amplitude_over_R"] for c in valid]); J=np.array([c["J_blind_J_s"] for c in valid])
    slope=loglog_slope(A,J); cv=float(np.std(J,ddof=1)/abs(np.mean(J))) if len(J)>1 and np.mean(J)!=0 else float("inf")
    rep=float(gc.get("boost_probe_amplitude",amps[len(amps)//2])); boost=np.asarray(gc.get("boost_probe_dimless",[0.15,-0.07,0.11]),float)
    c0=_measure(rep,cfg,scale,mode,(0,0,0)); cb=_measure(rep,cfg,scale,mode,boost)
    boost_spread=abs(cb["J_blind_J_s"]-c0["J_blind_J_s"])/max(abs(cb["J_blind_J_s"]),abs(c0["J_blind_J_s"]),1e-300) if np.isfinite(cb["J_blind_J_s"]) and np.isfinite(c0["J_blind_J_s"]) else float("inf")
    th=gc["thresholds"]
    passed=(abs(slope["slope"])<=th["amplitude_log_slope_abs_max"] and cv<=th["J_cv_max"] and boost_spread<=th["boost_J_rel_max"])
    return {"gate":GATE,"hypothesis":"A model-native excitation action J=DeltaE/nu is amplitude-independent and boost-objective without comparison to any external action constant.",
            "verdict":"PASS" if passed else "FAIL","cases":cases,"amplitude_fit":{"log_slope":slope["slope"],"r2":slope["r2"],"J_cv":cv},
            "boost_probe":{"unboosted":c0,"boosted":cb,"J_relative_spread":float(boost_spread)},"thresholds":th,
            "blind_note":"No Planck-scale constant is present in the evaluator or config.",
            "falsification_meaning":"FAIL rejects a universal amplitude-independent E/nu action for the tested classical vortex excitation family."}
