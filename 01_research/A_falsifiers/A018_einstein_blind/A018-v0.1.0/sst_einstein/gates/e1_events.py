from __future__ import annotations
import numpy as np
from ..geometry import kelvin_ring
from ..simulation import evolve, PhysicalScale
from ..statistics import detect_positive_events, quantization_cross_validation, fit_quantum

GATE="E1"

def run(cfg: dict, scale: PhysicalScale, outdir, rng=None, external_curves=None) -> dict:
    if rng is None: rng=np.random.default_rng(int(cfg["blind_protocol"]["seed"]))
    gc=cfg["gates"]["E1"]; mode=int(gc.get("mode",2)); n=int(cfg["simulation"]["n_points"])
    series_results=[]; all_events=[]; q_by_series=[]; fidelity_failures=[]
    for a in [float(x) for x in gc["amplitudes"]]:
        p=kelvin_ring(n,1.0,a,mode,0.13,True)
        sim=evolve(p,cfg,scale,mode=mode,record_points=False)
        energy=np.asarray(sim["energy_J"],float)
        energy_drift=float((np.max(energy)-np.min(energy))/max(abs(energy[0]),1e-300))
        if energy_drift > float(gc["thresholds"]["energy_drift_rel_max"]):
            fidelity_failures.append({"amplitude_over_R":a,"energy_drift_rel":energy_drift})
        power=np.abs(sim["kelvin_mode"])**2
        # Preregistered dimensional proxy: total localized energy times a bounded mode fraction.
        p0=max(float(np.median(power)),1e-300)
        frac=power/(power+p0)
        proxy=sim["energy_J"]*frac
        ev=detect_positive_events(proxy,float(gc["event_z_mad"]))
        q,s=fit_quantum(ev) if len(ev)>=3 else (float("nan"),float("nan"))
        if np.isfinite(q): q_by_series.append(q)
        all_events.extend(ev.tolist())
        series_results.append({"amplitude_over_R":a,"energy_drift_rel":energy_drift,"n_events":int(len(ev)),"events_J_proxy":ev.tolist(),"best_q_J_proxy":q,"fit_score":s})
    events=np.asarray(all_events,float); th=gc["thresholds"]
    if fidelity_failures:
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Numerical localized-energy drift exceeds the preregistered fidelity ceiling in one or more event series.",
                "series":series_results,"fidelity_failures":fidelity_failures,"thresholds":th}
    if len(events)<th["min_events_total"] or len(q_by_series)<th["min_series_with_events"]:
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Too few preregistered positive-transfer events for a discreteness test.","series":series_results,"n_events_total":int(len(events)),"thresholds":th}
    cv= float(np.std(q_by_series,ddof=1)/abs(np.mean(q_by_series))) if len(q_by_series)>1 else float("inf")
    cvres=quantization_cross_validation(events,rng,int(gc.get("surrogates",200)))
    passed=(cvres.get("ok",False) and cvres["test_score"]<=th["test_quant_score_max"] and cvres["surrogate_p"]<=th["surrogate_p_max"] and cv<=th["q_between_series_cv_max"])
    return {"gate":GATE,"hypothesis":"Continuous vortex evolution produces internally discrete event-energy units stable across excitation amplitudes, without supplying an external quantum target.",
            "verdict":"PASS" if passed else "FAIL","series":series_results,"n_events_total":int(len(events)),"q_between_series_cv":cv,"cross_validation":cvres,"thresholds":th,
            "blind_note":"The fitted q is data-derived and is never compared with h*nu or any external quantum scale.",
            "falsification_meaning":"FAIL rejects the tested event-quantization closure for this preregistered mode-energy proxy."}
