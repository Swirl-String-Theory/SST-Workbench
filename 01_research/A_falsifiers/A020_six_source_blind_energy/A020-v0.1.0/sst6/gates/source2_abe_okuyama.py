from __future__ import annotations
import math
import numpy as np
from sst6.blind import stable_seed
from sst6.geometry import pack_components, fourier_normal_mode_perturbation, curvature_torsion, component_length
from .common import result, prepared, native


def _energy(backend, comps):
    v,o=pack_components(comps)
    return float(backend.regularized_energy(v,o,1.0,2*math.pi,1.0))


def modal_additivity(dataset,cfg):
    comps,_,_,_=prepared(dataset,int(cfg["n_per_component"]))
    backend,bname=native(cfg)
    amp=float(cfg.get("amplitude_core",0.03)); modes=cfg.get("modes",[2,3]); seed=stable_seed(dataset.sha256,"AO1")
    d1=[]; d2=[]
    for ci,p in enumerate(comps):
        ph1=((seed+17*ci)%10000)/10000*2*math.pi; ph2=((seed+313+29*ci)%10000)/10000*2*math.pi
        d1.append(fourier_normal_mode_perturbation(p,int(modes[0]),amp,ph1,"normal"))
        d2.append(fourier_normal_mode_perturbation(p,int(modes[1]),amp,ph2,"binormal"))
    e0=_energy(backend,comps); e1=_energy(backend,[p+d for p,d in zip(comps,d1)]); e2=_energy(backend,[p+d for p,d in zip(comps,d2)]); e12=_energy(backend,[p+a+b for p,a,b in zip(comps,d1,d2)])
    de1=e1-e0; de2=e2-e0; de12=e12-e0; resid=abs(de12-de1-de2)/max(abs(de1)+abs(de2),1e-15)
    lim=float(cfg.get("nonlinear_residual_max",0.15)); ok=resid<=lim
    return result(2,"AO1_MODAL_ADDITIVITY","At the preregistered small amplitude, the declared regularized energy is approximately additive across two independent deformation modes.","MODEL_CONDITIONAL","PASS" if ok else "FAIL",{"backend":bname,"E0":e0,"dE_mode1":de1,"dE_mode2":de2,"dE_both":de12,"nonlinear_residual":resid,"amplitude_core":amp,"modes":modes},{"nonlinear_residual_max":lim},[
        "This tests the declared finite-core energy proxy, not thermodynamic entropy itself."
    ])


def phase_erasure(dataset,cfg):
    comps,_,_,_=prepared(dataset,int(cfg["n_per_component"]))
    backend,bname=native(cfg)
    amp=float(cfg.get("amplitude_core",0.04)); modes=cfg.get("modes",[2,3]); nphase=int(cfg.get("phase_samples",12)); seed=stable_seed(dataset.sha256,"AO6"); rng=np.random.default_rng(seed)
    e0=_energy(backend,comps); vals=[]
    for _ in range(nphase):
        ph=rng.uniform(0,2*math.pi,size=(len(comps),2)); out=[]
        for ci,p in enumerate(comps):
            d=fourier_normal_mode_perturbation(p,int(modes[0]),amp,float(ph[ci,0]),"normal")+fourier_normal_mode_perturbation(p,int(modes[1]),amp,float(ph[ci,1]),"binormal")
            out.append(p+d)
        vals.append(_energy(backend,out)-e0)
    a=np.asarray(vals); sensitivity=float(np.std(a)/max(np.mean(np.abs(a)),1e-15)); lim=float(cfg.get("phase_cv_max",0.05)); ok=sensitivity<=lim
    return result(2,"AO6_PHASE_ERASURE","Observables used in a Shannon-only modal coarse graining are insensitive to relative phase at fixed modal amplitudes.","MODEL_CONDITIONAL","PASS" if ok else "FAIL",{"backend":bname,"energy_increments":a.tolist(),"phase_sensitivity_cv":sensitivity,"amplitude_core":amp,"modes":modes},{"phase_cv_max":lim},[
        "FAIL means relative phase remains dynamically visible in this energy proxy; it does not falsify SST, only a Shannon-only reduction."
    ])


def boltzmann_geometry_proxy(dataset,cfg):
    comps,_,_,_=prepared(dataset,int(cfg["n_per_component"]))
    # Geometry-only diagnostic: curvature Fourier powers as p_n; E_n ~ k_n^2. Not a physical temperature claim.
    rows=[]
    for ci,p in enumerate(comps):
        k,_,_=curvature_torsion(p); x=k-k.mean(); pow=np.abs(np.fft.rfft(x))**2
        nmax=min(int(cfg.get("max_mode",16)),len(pow)-1); idx=np.arange(1,nmax+1); pp=pow[1:nmax+1]
        mask=pp>max(float(pp.max())*1e-8,1e-30) if len(pp) else np.zeros(0,bool)
        idx=idx[mask]; pp=pp[mask]
        if len(idx)<4: continue
        pp=pp/pp.sum(); L=component_length(p); E=(2*math.pi*idx/L)**2
        y=np.log(pp); A=np.column_stack([np.ones_like(E),E]); coef=np.linalg.lstsq(A,y,rcond=None)[0]; pred=A@coef
        sst=float(np.sum((y-y.mean())**2)); r2=1-float(np.sum((y-pred)**2))/sst if sst>0 else 1.0
        beta=-float(coef[1]); rows.append({"component":ci,"beta_proxy":beta,"r2":r2,"n_modes":len(idx)})
    mean_r2=float(np.mean([r["r2"] for r in rows])) if rows else float("nan")
    return result(2,"AO3_BOLTZMANN_GEOMETRY_PROXY","Curvature-mode occupation powers happen to follow a Boltzmann-like straight line in a geometry-only proxy.","PROXY_DIAGNOSTIC","PASS" if rows and mean_r2>=float(cfg.get("r2_min",0.95)) else "FAIL",{"components":rows,"mean_r2":mean_r2},{"r2_min":cfg.get("r2_min",0.95)},[
        "Excluded from the primary verdict. E_n~k_n^2 and curvature power are diagnostic proxies, not a derived SST thermodynamic sector."
    ])
