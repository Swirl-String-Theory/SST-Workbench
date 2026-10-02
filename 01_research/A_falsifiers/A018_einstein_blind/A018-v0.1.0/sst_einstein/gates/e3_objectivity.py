from __future__ import annotations
import numpy as np
from ..geometry import kelvin_ring, resample_closed, rms_radius
from ..simulation import evolve, PhysicalScale
from ..metrics import relative_rms, relative_scalar, relative_vector
from .. import native

GATE="E3"

def run(cfg: dict, scale: PhysicalScale, outdir, rng=None, external_curves=None) -> dict:
    gc=cfg["gates"]["E3"]
    n=int(cfg["simulation"]["n_points"]); mode=int(gc.get("mode",2))
    init=kelvin_ring(n,1.0,float(gc.get("amplitude",0.04)),mode,0.0,True)
    ref=evolve(init,cfg,scale,uniform_dimless=(0,0,0),mode=mode,record_points=True)
    boosts=gc["boosts_dimless"]
    cases=[]
    for u in boosts:
        u=np.asarray(u,float)
        b=evolve(init,cfg,scale,uniform_dimless=u,mode=mode,record_points=True)
        shape=[]; energy=[]; impulse=[]; mode_res=[]
        for k,t in enumerate(ref["time_dimless"]):
            corrected=b["frames"][k]-u[None,:]*t
            shape.append(relative_rms(corrected,ref["frames"][k]))
            energy.append(relative_scalar(b["energy_J"][k],ref["energy_J"][k]))
            impulse.append(relative_vector(b["impulse_kg_m_s"][k],ref["impulse_kg_m_s"][k]))
            qa=b["curvature_mode"][k]; qb=ref["curvature_mode"][k]
            mode_res.append(abs(qa-qb)/max(abs(qa),abs(qb),1e-30))
        cases.append({"boost_dimless":u.tolist(),"shape_rel_max":float(np.max(shape)),
                      "energy_rel_max":float(np.max(energy)),"impulse_rel_max":float(np.max(impulse)),
                      "intrinsic_mode_rel_max":float(np.max(mode_res))})
    external_static=[]
    if external_curves:
        probe=np.asarray(boosts[0],float)
        for name,curve in external_curves:
            try:
                p=resample_closed(np.asarray(curve,float),n)
                rr=rms_radius(p)
                if not np.isfinite(rr) or rr<=0: continue
                p=(p-p.mean(axis=0))/rr
                v0=native.biot_savart_velocity(p,scale.core_dimless,1.0,(0,0,0))
                vb=native.biot_savart_velocity(p,scale.core_dimless,1.0,probe)
                velocity_obj=relative_rms(vb-probe[None,:],v0)
                e0=native.filament_energy(p,scale.core_dimless,1.0,1.0)
                I0=native.impulse(p,1.0,1.0); k0=native.curvature(p)
                # translation of the entire curve is an explicit objectivity check for intrinsic functionals
                shift=np.array([0.37,-0.21,0.13]); ps=p+shift
                et=native.filament_energy(ps,scale.core_dimless,1.0,1.0)
                It=native.impulse(ps,1.0,1.0); kt=native.curvature(ps)
                external_static.append({"source":name,"velocity_objectivity_rel":velocity_obj,
                                        "translation_energy_rel":relative_scalar(e0,et),
                                        "translation_impulse_rel":relative_vector(I0,It),
                                        "translation_curvature_rel":float(np.linalg.norm(k0-kt)/max(np.linalg.norm(k0),1e-300))})
            except Exception as exc:
                external_static.append({"source":name,"error":repr(exc)})
    th=gc["thresholds"]
    worst={k:max(c[k] for c in cases) for k in ["shape_rel_max","energy_rel_max","impulse_rel_max","intrinsic_mode_rel_max"]}
    ext_bad=[]
    for c in external_static:
        if "error" in c: ext_bad.append(c); continue
        if max(c["velocity_objectivity_rel"],c["translation_energy_rel"],c["translation_impulse_rel"],c["translation_curvature_rel"])>th.get("external_static_rel_max",th["mode_rel_max"]):
            ext_bad.append(c)
    passed=(worst["shape_rel_max"]<=th["shape_rel_max"] and worst["energy_rel_max"]<=th["energy_rel_max"]
            and worst["impulse_rel_max"]<=th["impulse_rel_max"] and worst["intrinsic_mode_rel_max"]<=th["mode_rel_max"] and not ext_bad)
    return {"gate":GATE,"hypothesis":"Intrinsic vortex observables are objective under a uniform Galilean fluid boost after removal of the trivial translation.",
            "verdict":"PASS" if passed else "FAIL","cases":cases,"external_static_cases":external_static,"worst":worst,"thresholds":th,
            "falsification_meaning":"FAIL rejects the tested objectivity/boost-invariance closure for these model-native observables."}
