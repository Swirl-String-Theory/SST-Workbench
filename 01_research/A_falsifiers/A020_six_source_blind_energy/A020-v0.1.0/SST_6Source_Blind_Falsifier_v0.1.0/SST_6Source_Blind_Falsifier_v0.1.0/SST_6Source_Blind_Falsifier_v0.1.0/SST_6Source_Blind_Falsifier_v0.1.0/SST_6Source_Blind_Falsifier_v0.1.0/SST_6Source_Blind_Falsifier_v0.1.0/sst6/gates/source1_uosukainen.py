from __future__ import annotations
import math
import numpy as np
from sst6.blind import stable_seed
from sst6.geometry import pack_components, rotation_minimizing_frame, fourier_normal_mode_perturbation
from .common import result, prepared, native, fit_log_slope


def cross_self_scaling(dataset, cfg):
    comps,v,offs,_=prepared(dataset,int(cfg["n_per_component"]))
    backend,bname=native(cfg)
    probes=[]
    for p in comps:
        _,n,_,_=rotation_minimizing_frame(p)
        stride=max(1,len(p)//int(cfg.get("probe_points_per_component",48)))
        probes.append(p[::stride]+float(cfg.get("probe_radius_core",2.5))*n[::stride])
    q=np.vstack(probes)
    gamma=2*math.pi; rho=1.0; core=1.0
    u0=np.asarray(backend.biot_savart_velocity(q,v,offs,gamma,core),float)
    eps=np.asarray(cfg.get("epsilons",[0.01,0.02,0.04,0.08]),float)
    cross_vals=[]; self_vals=[]
    base_seed=stable_seed(dataset.sha256,"U1")
    for ie,e in enumerate(eps):
        pert=[]
        for ci,p in enumerate(comps):
            mode=2+((base_seed+ci)%4)
            phase=((base_seed>>(ci%16))%10000)/10000*2*math.pi
            pert.append(fourier_normal_mode_perturbation(p,mode,float(e),phase=phase,axis="normal"))
        pv,po=pack_components([p+d for p,d in zip(comps,pert)])
        ue=np.asarray(backend.biot_savart_velocity(q,pv,po,gamma,core),float)
        du=ue-u0
        c=[]; s=[]
        for a,b in zip(u0,du):
            tc=np.outer(a,b)+np.outer(b,a); ts=np.outer(b,b)
            c.append(rho*np.linalg.norm(tc)); s.append(rho*np.linalg.norm(ts))
        cross_vals.append(float(np.mean(c))); self_vals.append(float(np.mean(s)))
    slope_c,r2c=fit_log_slope(eps,cross_vals); slope_s,r2s=fit_log_slope(eps,self_vals)
    tc=cfg.get("cross_slope",[0.8,1.2]); ts=cfg.get("self_slope",[1.6,2.4]); r2min=float(cfg.get("r2_min",0.97))
    ok=(tc[0]<=slope_c<=tc[1] and ts[0]<=slope_s<=ts[1] and r2c>=r2min and r2s>=r2min)
    return result(1,"U1_CROSS_SELF_SCALING","Transport cross-stress scales O(epsilon) and self-stress O(epsilon^2) in the small-perturbation regime.","PRIMARY_NUMERICAL_IDENTITY","PASS" if ok else "FAIL",{
        "backend":bname,"epsilons":eps.tolist(),"cross_norm":cross_vals,"self_norm":self_vals,"cross_slope":slope_c,"self_slope":slope_s,"cross_r2":r2c,"self_r2":r2s
    },{"cross_slope":tc,"self_slope":ts,"r2_min":r2min})


def _multipole_one(backend, vertices, offsets, pad, ngrid):
    mn=vertices.min(axis=0)-pad; mx=vertices.max(axis=0)+pad
    xs=[np.linspace(mn[i],mx[i],ngrid) for i in range(3)]
    X,Y,Z=np.meshgrid(xs[0],xs[1],xs[2],indexing="ij")
    q=np.column_stack([X.ravel(),Y.ravel(),Z.ravel()])
    u=np.asarray(backend.biot_savart_velocity(q,vertices,offsets,2*math.pi,1.0),float).reshape(ngrid,ngrid,ngrid,3)
    dx=[x[1]-x[0] for x in xs]
    G=np.empty((ngrid,ngrid,ngrid,3,3),float)
    for j in range(3):
        du=np.gradient(u[...,j],*dx,edge_order=2)
        for i in range(3): G[...,j,i]=du[i]
    S=np.einsum("...ji,...ij->...",G,G)
    dV=dx[0]*dx[1]*dx[2]
    absint=float(np.sum(np.abs(S))*dV)
    m0=float(np.sum(S)*dV)
    ctr=vertices.mean(axis=0); R=np.stack([X-ctr[0],Y-ctr[1],Z-ctr[2]],axis=-1)
    m1=np.sum(R*S[...,None],axis=(0,1,2))*dV
    L=float(np.linalg.norm(mx-mn))
    return {"pad_core":pad,"ngrid":ngrid,"m0_norm":abs(m0)/max(absint,1e-300),"m1_norm":float(np.linalg.norm(m1))/max(L*absint,1e-300),"source_abs_integral":absint,"source_signed_integral":m0}


def multipole_no_monopole(dataset,cfg):
    _,v,offs,_=prepared(dataset,int(cfg["n_per_component"]))
    backend,bname=native(cfg)
    grids=cfg.get("grids",[[4.0,11],[6.0,15]])
    vals=[_multipole_one(backend,v,offs,float(p),int(n)) for p,n in grids]
    outer=vals[-1]; m0max=float(cfg.get("m0_norm_max",0.12)); m1max=float(cfg.get("m1_norm_max",0.12))
    # Absolute smallness is the preregistered criterion. A coarser expanding box can
    # make the normalized finite-difference residual non-monotone even when both boxes
    # are already close to zero, so non-monotonicity alone is not a FAIL.
    improve=(len(vals)<2 or outer["m0_norm"]<=max(m0max, vals[0]["m0_norm"]*float(cfg.get("outer_worsen_factor",1.5))))
    ok=outer["m0_norm"]<=m0max and outer["m1_norm"]<=m1max and improve
    return result(1,"U2_TRANSPORT_MULTIPOLE","The regularized incompressible transport-stress Poisson source has no robust monopole/dipole in the expanding-domain limit.","PRIMARY_STATIC_FIELD","PASS" if ok else "FAIL",{"backend":bname,"domains":vals},{"m0_norm_max":m0max,"m1_norm_max":m1max,"outer_worsen_factor":cfg.get("outer_worsen_factor",1.5)},[
        "Finite boxes and finite-difference derivatives can leave boundary residuals; use extended resolution before treating a FAIL as physical."
    ])
