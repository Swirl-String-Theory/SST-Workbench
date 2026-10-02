from __future__ import annotations
import math
import numpy as np
from .geometry import (
    pack_components, unpack_components, frames_component, frames_geometry,
    local_chirality_texture, ds_cv_geometry, total_length, min_segment_length,
)

try:
    from native_ext import velocity_at_points_multi, curve_velocity_multi, transverse_jacobian_multi, gauss_xi_multi
except Exception as e:  # pragma: no cover
    velocity_at_points_multi=curve_velocity_multi=transverse_jacobian_multi=gauss_xi_multi=None
    _IMPORT_ERROR=e
else:
    _IMPORT_ERROR=None


def require_native():
    if curve_velocity_multi is None:
        raise RuntimeError(f"native_ext unavailable: {_IMPORT_ERROR}. Run run_01_build_native.cmd")


def _slices(offsets:np.ndarray):
    return [slice(int(offsets[i]),int(offsets[i+1])) for i in range(len(offsets)-1)]


def _flow(packed:np.ndarray, offsets:np.ndarray, core:float)->np.ndarray:
    return np.asarray(curve_velocity_multi(np.ascontiguousarray(packed,float),np.ascontiguousarray(offsets,np.int64),core,1.0),dtype=np.float64)


def centerline_helicity_xi(comps:list[np.ndarray],core:float)->float:
    """Operator-consistent dimensionless line helicity proxy.

    For equal unit circulations, Xi = sum_alpha int_{C_alpha} v_BS · dl / Gamma.
    Total geometry is normalized to L=1 before calling this routine.
    """
    require_native(); packed,offs=pack_components(comps)
    mids=[]; dls=[]
    for c in comps:
        nxt=np.roll(c,-1,axis=0); mids.append(0.5*(c+nxt)); dls.append(nxt-c)
    mids=np.vstack(mids); dls=np.vstack(dls)
    vel=np.asarray(velocity_at_points_multi(packed,offs,np.ascontiguousarray(mids),core,1.0),float)
    return float(np.sum(np.einsum("ij,ij->i",vel,dls)))


def tube_helicity_xi(comps:list[np.ndarray],core:float,radial_nodes:int=3,angles:int=8)->float:
    """Gaussian finite-core volume cross-check for H/Gamma^2 with equal Gamma=1 tubes."""
    require_native(); packed,offs=pack_components(comps)
    nodes,weights=np.polynomial.legendre.leggauss(radial_nodes); rmax=3.0*core
    rs=0.5*(nodes+1.0)*rmax; rweights=0.5*rmax*weights
    thetas=2*np.pi*np.arange(angles)/angles; dtheta=2*np.pi/angles
    pts=[]; omega=[]; dvol=[]
    for c in comps:
        t,n,b,kappa=frames_component(c); seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); ds=0.5*(seg+np.roll(seg,1))
        for i in range(len(c)):
            for r,rw in zip(rs,rweights):
                amp=math.exp(-(r/core)**2)/(math.pi*core*core)
                for th in thetas:
                    co,si=math.cos(th),math.sin(th)
                    pts.append(c[i]+r*(co*n[i]+si*b[i])); omega.append(amp*t[i])
                    jac=max(0.05,1.0-kappa[i]*r*co); dvol.append(ds[i]*r*rw*dtheta*jac)
    pts=np.ascontiguousarray(np.array(pts,float)); omega=np.array(omega,float); dvol=np.array(dvol,float)
    vel=np.asarray(velocity_at_points_multi(packed,offs,pts,core,1.0),float)
    return float(np.sum(np.einsum("ij,ij->i",vel,omega)*dvol))


def gauss_helicity_xi(comps:list[np.ndarray])->float:
    require_native(); packed,offs=pack_components(comps)
    return float(gauss_xi_multi(packed,offs,1e-10))


def _weights_from_components(comps:list[np.ndarray])->np.ndarray:
    ws=[]
    for c in comps:
        seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); ws.append(0.5*(seg+np.roll(seg,1)))
    return np.concatenate(ws)


def fit_rigid_field(packed:np.ndarray, vectors:np.ndarray, weights:np.ndarray|None=None)->dict:
    """Least-squares fit vectors_i ~= U + Omega x x_i."""
    x=np.asarray(packed,float); v=np.asarray(vectors,float); n=len(x)
    A=np.zeros((3*n,6),float); y=v.reshape(-1)
    for i,(xx,yy,zz) in enumerate(x):
        r=3*i; A[r:r+3,:3]=np.eye(3)
        A[r:r+3,3:]=np.array([[0,zz,-yy],[-zz,0,xx],[yy,-xx,0]],float)
    if weights is not None:
        sw=np.repeat(np.sqrt(np.asarray(weights,float)),3); Aw=A*sw[:,None]; yw=y*sw
    else: Aw=A; yw=y
    q,_,_,_=np.linalg.lstsq(Aw,yw,rcond=None); fit=(A@q).reshape(n,3); res=v-fit
    if weights is None:
        den=np.linalg.norm(v); num=np.linalg.norm(res)
    else:
        w=np.asarray(weights,float); den=math.sqrt(float(np.sum(w*np.sum(v*v,axis=1)))); num=math.sqrt(float(np.sum(w*np.sum(res*res,axis=1))))
    return {"translation":q[:3].tolist(),"rotation":q[3:].tolist(),"relative_residual":float(num/max(den,1e-30)),
            "rms_vector":float(math.sqrt(np.mean(np.sum(v*v,axis=1)))),"fit":fit,"residual":res}


def relative_equilibrium_metrics(comps:list[np.ndarray],core:float)->dict:
    packed,offs=pack_components(comps); v=_flow(packed,offs,core); w=_weights_from_components(comps)
    fit=fit_rigid_field(packed,v,w)
    return {k:fit[k] for k in ("translation","rotation","relative_residual","rms_vector")}


def _remove_rigid_perturbation(packed:np.ndarray,delta:np.ndarray,weights:np.ndarray)->tuple[np.ndarray,float]:
    fit=fit_rigid_field(packed,delta,weights); internal=fit["residual"]
    e0=float(np.sum(weights*np.sum(delta*delta,axis=1))); er=float(np.sum(weights*np.sum((delta-internal)**2,axis=1)))
    return internal,float(er/max(e0,1e-30))


def _rk4_base_step(x:np.ndarray,offs:np.ndarray,core:float,dt:float)->tuple[np.ndarray,float,tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]]:
    # Keep the physical translation.  Removing it after a step would change the
    # discrete base map unless the same projection were differentiated in the
    # tangent equation.  Biot--Savart is translation invariant, so there is no
    # numerical need to recenter the trajectory.
    x1=np.ascontiguousarray(x,dtype=np.float64)
    k1=_flow(x1,offs,core)
    x2=np.ascontiguousarray(x1+0.5*dt*k1)
    k2=_flow(x2,offs,core)
    x3=np.ascontiguousarray(x1+0.5*dt*k2)
    k3=_flow(x3,offs,core)
    x4=np.ascontiguousarray(x1+dt*k3)
    k4=_flow(x4,offs,core)
    vmax=max(float(np.max(np.linalg.norm(k,axis=1))) for k in (k1,k2,k3,k4))
    xnext=np.ascontiguousarray(x1+(dt/6.0)*(k1+2*k2+2*k3+k4))
    return xnext,vmax,(x1,x2,x3,x4)


def _packed_segment_stats(packed:np.ndarray,offs:np.ndarray)->tuple[float,float]:
    vals=[]
    for s in _slices(offs):
        c=packed[s]; vals.extend(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).tolist())
    a=np.array(vals,float); return float(np.min(a)),float(np.std(a)/max(np.mean(a),1e-30))


def integrate_base_trajectory(comps:list[np.ndarray],core:float,cfg:dict)->dict:
    packed,offs=pack_components(comps); T=float(cfg.get("trajectory_time",0.15)); cfl=float(cfg.get("trajectory_cfl",0.18))
    max_steps=int(cfg.get("max_trajectory_steps",180)); min_steps=int(cfg.get("min_trajectory_steps",24))
    f0=_flow(packed,offs,core); vmax=float(np.max(np.linalg.norm(f0,axis=1))); mind,_=_packed_segment_stats(packed,offs)
    dt_lim=cfl*min(core,mind)/max(vmax,1e-12); required=max(min_steps,int(math.ceil(T/max(dt_lim,1e-12))))
    steps=min(required,max_steps); dt=T/steps; underresolved=required>max_steps
    states=[packed.copy()]; rk_stages=[]; max_cv=0.0; max_cfl=0.0; max_stage_speed=vmax
    x=packed.copy()
    for _ in range(steps):
        x,vstage,stages=_rk4_base_step(x,offs,core,dt); rk_stages.append(stages)
        mind_now,cv=_packed_segment_stats(x,offs); max_cv=max(max_cv,cv); max_stage_speed=max(max_stage_speed,vstage)
        max_cfl=max(max_cfl,vstage*dt/max(min(core,mind_now),1e-30)); states.append(x.copy())
        if not np.isfinite(x).all(): raise FloatingPointError("non-finite baseline trajectory")
    L0=sum(np.linalg.norm(np.roll(packed[s],-1,axis=0)-packed[s],axis=1).sum() for s in _slices(offs))
    L1=sum(np.linalg.norm(np.roll(x[s],-1,axis=0)-x[s],axis=1).sum() for s in _slices(offs))
    shape=_rigid_shape_residual(packed,x)
    return {"states":states,"rk_stages":rk_stages,"offsets":offs,"dt":dt,"steps":steps,"required_steps":required,"underresolved":underresolved,
            "initial_max_speed":vmax,"max_stage_speed":max_stage_speed,"initial_min_ds":mind,"achieved_cfl":float(max_cfl),
            "max_ds_cv":max_cv,"relative_length_change":float((L1-L0)/max(L0,1e-30)),"rigid_shape_residual":shape}


def _rigid_shape_residual(x0:np.ndarray,x1:np.ndarray)->float:
    a=x0-x0.mean(axis=0); b=x1-x1.mean(axis=0); H=a.T@b; U,_,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1,:]*=-1; R=Vt.T@U.T
    ar=a@R.T; return float(np.linalg.norm(ar-b)/max(np.linalg.norm(a),1e-30))


def _jvp(x:np.ndarray,offs:np.ndarray,delta:np.ndarray,core:float,eps:float)->np.ndarray:
    rms=float(np.linalg.norm(delta)/math.sqrt(max(len(delta),1)))
    if rms<1e-30: return np.zeros_like(delta)
    d=delta/rms
    fp=_flow(np.ascontiguousarray(x+eps*d),offs,core); fm=_flow(np.ascontiguousarray(x-eps*d),offs,core)
    return (fp-fm)*(rms/(2.0*eps))


def initial_packet(comps:list[np.ndarray],component:int,center:float,width:float,mode:int)->np.ndarray:
    packed,offs=pack_components(comps); _,n,b,_=frames_geometry(comps); delta=np.zeros_like(packed); sl=_slices(offs)[component]; nc=sl.stop-sl.start
    s=np.arange(nc,dtype=float)/nc; d=np.minimum(np.abs(s-center),1.0-np.abs(s-center)); env=np.exp(-0.5*(d/width)**2)
    amp=env*np.cos(2*np.pi*mode*(s-center)); amp-=amp.mean(); delta[sl]=amp[:,None]*n[sl]
    weights=_weights_from_components(comps); delta,_=_remove_rigid_perturbation(packed,delta,weights)
    delta/=max(np.linalg.norm(delta),1e-30); return np.ascontiguousarray(delta)


def _fourier_pi(a:np.ndarray,b:np.ndarray)->float:
    z=a+1j*b; Z=np.fft.fft(z); f=np.fft.fftfreq(len(z)); p=float(np.sum(np.abs(Z[f>0])**2)); m=float(np.sum(np.abs(Z[f<0])**2))
    return float((p-m)/max(p+m,1e-30))


def _wrap_half(x:float)->float:
    return float((x+0.5)%1.0-0.5)


def packet_observables(packed:np.ndarray,offs:np.ndarray,delta:np.ndarray,component:int,center:float,dead_zone:float=0.02,window:float=0.40,locality_power:float=2.0)->dict:
    comps=[packed[s] for s in _slices(offs)]; weights=_weights_from_components(comps); internal,rigid_frac=_remove_rigid_perturbation(packed,delta,weights)
    t,n,b,_=frames_geometry(comps); aa=np.einsum("ij,ij->i",internal,n); bb=np.einsum("ij,ij->i",internal,b); tt=np.einsum("ij,ij->i",internal,t)
    e=aa*aa+bb*bb; total=float(np.sum(e)); sl=_slices(offs)[component]; ec=e[sl]; nc=len(ec); s=np.arange(nc,dtype=float)/nc
    phase=2*np.pi*(s-center)
    local=np.maximum(0.0,0.5*(1.0+np.cos(phase)))**float(locality_power)
    signed=np.sin(phase)*local
    direction=float(np.sum(ec*signed)/max(np.sum(ec*np.abs(signed)),1e-30))
    # Legacy hard split is retained as a secondary diagnostic only.
    rel=((s-center+0.5)%1.0)-0.5; plus=float(np.sum(ec[(rel>dead_zone)&(rel<window)])); minus=float(np.sum(ec[(rel<-dead_zone)&(rel>-window)])); split=float((plus-minus)/max(plus+minus,1e-30))
    z=np.sum(ec*np.exp(2j*np.pi*s)); centroid=float((np.angle(z)/(2*np.pi))%1.0) if abs(z)>1e-30 else center
    tangent=float(np.sum(tt*tt)/max(np.sum(aa*aa+bb*bb+tt*tt),1e-30)); leakage=float((total-float(np.sum(ec)))/max(total,1e-30))
    return {"fourier_pi":_fourier_pi(aa[sl],bb[sl]),"direction_pi":direction,"split_pi_legacy":split,"centroid_s":centroid,"transverse_energy":total,
            "leakage_fraction":leakage,"tangent_fraction":tangent,"rigid_fraction":rigid_frac}


def evolve_tangent_on_trajectory(traj:dict,comps0:list[np.ndarray],core:float,component:int,center:float,mode:int,cfg:dict)->dict:
    states=traj["states"]; offs=traj["offsets"]; dt=float(traj["dt"]); eps=float(cfg.get("jvp_eps_fraction",2e-5)); width=float(cfg.get("packet_width",0.08))
    dead=float(cfg.get("transport_dead_zone",0.02)); window=float(cfg.get("transport_window",0.40)); locality=float(cfg.get("transport_locality_power",2.0))
    d=initial_packet(comps0,component,center,width,mode); d0=d.copy(); init=packet_observables(states[0],offs,d,component,center,dead,window,locality)
    sample_count=int(cfg.get("trajectory_samples",24)); sample_idx=set(np.linspace(0,len(states)-1,min(sample_count,len(states)),dtype=int).tolist())
    samples=[{"step":0,"time":0.0,**init,"direction_pi_delta":0.0,"split_pi_legacy_delta":0.0,"fourier_pi_delta":0.0,"centroid_shift":0.0}]
    log_scale=0.0; renorm_hi=float(cfg.get("tangent_renorm_hi",1e3)); renorm_lo=float(cfg.get("tangent_renorm_lo",1e-3))
    stages_all=traj.get("rk_stages")
    if stages_all is None or len(stages_all)!=len(states)-1:
        raise RuntimeError("trajectory is missing RK4 stage states required by the variational integrator")
    for k in range(len(states)-1):
        x1=states[k+1]; xs1,xs2,xs3,xs4=stages_all[k]
        k1=_jvp(xs1,offs,d,core,eps)
        k2=_jvp(xs2,offs,d+0.5*dt*k1,core,eps)
        k3=_jvp(xs3,offs,d+0.5*dt*k2,core,eps)
        k4=_jvp(xs4,offs,d+dt*k3,core,eps)
        d=d+(dt/6.0)*(k1+2*k2+2*k3+k4)
        if not np.isfinite(d).all(): raise FloatingPointError("non-finite tangent state")
        nd=float(np.linalg.norm(d))
        if nd>renorm_hi or (0<nd<renorm_lo): d/=nd; log_scale+=math.log(nd)
        step=k+1
        if step in sample_idx:
            o=packet_observables(x1,offs,d,component,center,dead,window,locality)
            o["step"]=step; o["time"]=step*dt; o["direction_pi_delta"]=o["direction_pi"]-init["direction_pi"]; o["split_pi_legacy_delta"]=o["split_pi_legacy"]-init["split_pi_legacy"]; o["fourier_pi_delta"]=o["fourier_pi"]-init["fourier_pi"]
            o["centroid_shift"]=_wrap_half(o["centroid_s"]-init["centroid_s"]); samples.append(o)
    nd=float(np.linalg.norm(d)); log_growth=log_scale+math.log(max(nd,1e-300)/max(np.linalg.norm(d0),1e-300)); late=samples[max(1,len(samples)//2):]
    T=max(float(samples[-1]["time"]),1e-30)
    return {"component":int(component),"center":float(center),"mode":int(mode),
            "transport_pi":float(np.mean([q["direction_pi_delta"] for q in late])),
            "fourier_pi":float(np.mean([q["fourier_pi_delta"] for q in late])),
            "centroid_velocity":float(samples[-1]["centroid_shift"]/T),
            "centroid_shift_final":float(samples[-1]["centroid_shift"]),
            "log_norm_growth":float(log_growth),"norm_growth":float(math.exp(min(700.0,log_growth))),
            "leakage_fraction_late":float(np.mean([q["leakage_fraction"] for q in late])),
            "tangent_fraction_late":float(np.mean([q["tangent_fraction"] for q in late])),
            "rigid_fraction_late":float(np.mean([q["rigid_fraction"] for q in late])),"samples":samples}


def frozen_spectrum(comps:list[np.ndarray],core:float,fd_eps:float)->dict:
    require_native(); packed,offs=pack_components(comps); _,n,b,_=frames_geometry(comps)
    J=np.asarray(transverse_jacobian_multi(packed,offs,n,b,core,1.0,fd_eps),float); dim=J.shape[0]; scale=max(float(np.linalg.norm(J,"fro")/math.sqrt(dim)),1e-12); eig=np.linalg.eigvals(J/scale)
    return {"enabled":True,"operator_rate_scale_Gamma_over_L2":scale,"max_real":float(np.max(eig.real)),"min_real":float(np.min(eig.real)),
            "spectral_radius":float(np.max(np.abs(eig))),"eigenvalues":[[float(z.real),float(z.imag)] for z in eig]}


def candidate_metrics(comps:list[np.ndarray],cfg:dict)->dict:
    require_native(); core=float(cfg["core_fraction"]); packed,offs=pack_components(comps)
    xi=centerline_helicity_xi(comps,core); gx=gauss_helicity_xi(comps)
    tube=None
    if bool(cfg.get("compute_tube_helicity",False)):
        tube=tube_helicity_xi(comps,core,int(cfg.get("helicity_radial_nodes",3)),int(cfg.get("helicity_angles",8)))
    re0=relative_equilibrium_metrics(comps,core); traj=integrate_base_trajectory(comps,core,cfg)
    final_comps=[traj["states"][-1][s] for s in _slices(traj["offsets"])]; ref=relative_equilibrium_metrics(final_comps,core)
    textures=[local_chirality_texture(c) for c in comps]
    loc={"mean":float(np.mean(np.concatenate(textures))),"rms":float(np.sqrt(np.mean(np.concatenate(textures)**2))),
         "abs_mean":float(np.mean(np.abs(np.concatenate(textures))))}
    max_comp=min(len(comps),int(cfg.get("max_excited_components",3))) if bool(cfg.get("excite_all_components",True)) else 1
    excitations=[]
    for ci in range(max_comp):
        chi=textures[ci]
        for center in cfg.get("excitation_centers",[0.25,0.75]):
            idx=int(round(float(center)*len(chi)))%len(chi)
            for mode in cfg.get("carrier_modes",[3]):
                e=evolve_tangent_on_trajectory(traj,comps,core,ci,float(center),int(mode),cfg); e["local_chirality_at_center"]=float(chi[idx])
                if not bool(cfg.get("store_excitation_samples",False)): e.pop("samples",None)
                excitations.append(e)
    pi=np.array([e["transport_pi"] for e in excitations],float); fpi=np.array([e["fourier_pi"] for e in excitations],float); cv=np.array([e["centroid_velocity"] for e in excitations],float)
    amp=np.array([e["log_norm_growth"] for e in excitations],float); tang=np.array([e["tangent_fraction_late"] for e in excitations],float); rigid=np.array([e["rigid_fraction_late"] for e in excitations],float)
    chis=np.array([e["local_chirality_at_center"] for e in excitations],float)
    corr=float(np.corrcoef(chis,pi)[0,1]) if len(pi)>=3 and np.std(chis)>1e-15 and np.std(pi)>1e-15 else float("nan")
    spec={"enabled":False}
    if bool(cfg.get("compute_frozen_spectrum",False)) and len(packed)<=int(cfg.get("max_spectrum_points",128)):
        spec=frozen_spectrum(comps,core,float(cfg.get("fd_eps_fraction",1.5e-5)))
    return {"n_components":len(comps),"n_points_total":len(packed),"component_points":[len(c) for c in comps],
            "xi_helicity_centerline":xi,"xi_gauss":gx,"xi_helicity_tube":tube,"local_chirality":loc,
            "relative_equilibrium_initial":re0,"relative_equilibrium_final":ref,
            "trajectory":{"steps":traj["steps"],"required_steps":traj["required_steps"],"underresolved":traj["underresolved"],"dt":traj["dt"],
                          "achieved_cfl":traj["achieved_cfl"],"max_ds_cv":traj["max_ds_cv"],"relative_length_change":traj["relative_length_change"],"rigid_shape_residual":traj["rigid_shape_residual"]},
            "transport_pi":float(np.mean(pi)),"transport_pi_std_over_excitations":float(np.std(pi)),"transport_pi_abs_mean":float(np.mean(np.abs(pi))),
            "fourier_pi":float(np.mean(fpi)),"centroid_velocity":float(np.mean(cv)),"centroid_velocity_abs_mean":float(np.mean(np.abs(cv))),
            "log_norm_growth_mean":float(np.mean(amp)),"log_norm_growth_max":float(np.max(amp)),"tangent_fraction_mean":float(np.mean(tang)),"rigid_fraction_mean":float(np.mean(rigid)),
            "local_chirality_transport_corr":corr,"spectrum":spec,"excitations":excitations}
