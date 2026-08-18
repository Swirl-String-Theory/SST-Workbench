from __future__ import annotations
import math, time
from pathlib import Path
import numpy as np
from kk_native.core import induced_velocity, velocity_at_points
from .geometry import rigid_fit, deformation_basis, mode_k2, frames_for_components, curve_length


def _shape_velocity(X, offsets, core_radius, circulation, threads, require_native, force_python=False):
    V,backend=induced_velocity(X,offsets,core_radius,circulation,threads=threads,require_native=require_native,force_python=force_python)
    fit=rigid_fit(X,V)
    return fit['residual'],fit,V,backend


def linearized_operator(comps, X, offsets, core_radius, circulation, threads, cfg, require_native=True, force_python=False):
    t0=time.time()
    F0,fit,V0,backend=_shape_velocity(X,offsets,core_radius,circulation,threads,require_native,force_python)
    Q,bmeta=deformation_basis(comps,int(cfg['modes_per_component']),int(cfg['max_basis_dim']))
    d=Q.shape[1]; N=len(X)
    h=float(cfg['jacobian_eps_fraction'])*core_radius*math.sqrt(N)
    A=np.empty((d,d),float)
    for j in range(d):
        Xp=X+(h*Q[:,j]).reshape(N,3)
        Fp,_,_,_=_shape_velocity(Xp,offsets,core_radius,circulation,threads,require_native,force_python)
        col=((Fp-F0)/h).reshape(-1)
        A[:,j]=Q.T@col
    ev,evec=np.linalg.eig(A)
    rows=[]; modes=[]
    # retain one side of each conjugate pair; real eigenvalues are kept separately with zero oscillation frequency
    idx=np.argsort(np.abs(np.imag(ev)))
    for ii in idx:
        lam=ev[ii]
        if np.imag(lam) < -1e-12: continue
        coeff=evec[:,ii]
        mode=(Q@coeff).reshape(N,3)
        k2=mode_k2(mode,comps)
        freq=abs(float(np.imag(lam))); growth=float(np.real(lam))
        rows.append({'eigen_index':int(ii),'lambda_real':growth,'lambda_imag':float(np.imag(lam)),'frequency':freq,'growth_abs':abs(growth),'growth_ratio':abs(growth)/max(freq,1e-15),'k2':float(k2),'k':float(math.sqrt(max(k2,0.0)))})
        modes.append(mode)
    return {
        'backend':backend,'runtime_s':time.time()-t0,'velocity':V0,'shape_velocity':F0,'rigid_fit':fit,
        'basis_meta':bmeta,'basis_Q':Q,'operator_A':A,'eigenvalues':ev,'mode_rows':rows,'modes':modes,
    }


def _linfit(x,y,through_zero=False):
    x=np.asarray(x,float); y=np.asarray(y,float); n=len(x)
    if n<2: return None
    if through_zero:
        b=float(np.dot(x,y)/max(np.dot(x,x),1e-300)); a=0.0; pred=b*x; p=1
    else:
        M=np.c_[np.ones(n),x]; a,b=np.linalg.lstsq(M,y,rcond=None)[0]; pred=a+b*x; p=2
    rss=float(np.sum((y-pred)**2)); tss=float(np.sum((y-y.mean())**2)); r2=1-rss/max(tss,1e-300)
    aic=n*math.log(max(rss/n,1e-300))+2*p
    return {'intercept':float(a),'slope':float(b),'rss':rss,'r2':float(r2),'aic':float(aic),'pred':pred}


def fit_dispersion(mode_rows,cfg):
    stable=[r for r in mode_rows if r['frequency']>float(cfg['min_frequency']) and r['growth_ratio']<=float(cfg['max_growth_ratio_for_spectrum']) and np.isfinite(r['k2'])]
    stable=sorted(stable,key=lambda r:r['k2'])
    if len(stable)<int(cfg['min_spectral_modes']): return {'status':'INSUFFICIENT_STABLE_MODES','n_modes':len(stable)}
    x=np.array([r['k2'] for r in stable]); y=np.array([r['frequency']**2 for r in stable])
    split=max(3,int(math.ceil(float(cfg['train_fraction'])*len(stable)))); split=min(split,len(stable)-2)
    train=_linfit(x[:split],y[:split],False); zero=_linfit(x[:split],y[:split],True)
    if train is None or zero is None: return {'status':'FIT_FAILED','n_modes':len(stable)}
    pred=train['intercept']+train['slope']*x[split:]
    rmse=float(np.sqrt(np.mean((y[split:]-pred)**2)))
    scale=float(np.sqrt(np.mean(y[split:]**2))) if len(y[split:]) else float('nan')
    nrmse=rmse/max(scale,1e-300)
    allfit=_linfit(x,y,False)
    return {
        'status':'OK','n_modes':len(stable),'train_n':split,'holdout_n':len(stable)-split,
        'intercept':train['intercept'],'slope':train['slope'],'gap_sigma0':math.sqrt(max(train['intercept'],0.0)),
        'c_eff':math.sqrt(max(train['slope'],0.0)),'train_r2':train['r2'],'holdout_nrmse':nrmse,
        'delta_aic_zero_minus_gap':zero['aic']-train['aic'],'all_r2':None if allfit is None else allfit['r2'],
        'stable_mode_rows':stable,
    }


def radial_response(comps,X,offsets,core_radius,circulation,threads,lin,disp,cfg,require_native=True,force_python=False):
    if disp.get('status')!='OK': return {'status':'NO_VALID_DISPERSION'}
    fit=lin['rigid_fit']; omega=float(np.linalg.norm(fit['omega']))
    if omega<=1e-15 or disp.get('c_eff',0)<=0: return {'status':'NO_POSITIVE_PREDICTED_LENGTH'}
    predicted=float(disp['c_eff']/(2.0*omega))
    # choose the lowest-frequency sufficiently stable oscillatory mode
    candidates=[]
    for row,mode in zip(lin['mode_rows'],lin['modes']):
        if row['frequency']>float(cfg['min_frequency']) and row['growth_ratio']<=float(cfg['max_growth_ratio_for_spectrum']): candidates.append((row,mode))
    if not candidates: return {'status':'NO_STABLE_MODE'}
    row,cmode=min(candidates,key=lambda z:z[0]['frequency'])
    real=np.real(cmode); imag=np.imag(cmode); mode=real if np.linalg.norm(real)>=np.linalg.norm(imag) else imag
    rms=math.sqrt(float(np.mean(np.sum(mode*mode,axis=1)))); mode=mode/max(rms,1e-300)
    _,NN,_=frames_for_components(comps)
    nstations=min(int(cfg['radial_stations']),len(X)); ids=np.linspace(0,len(X)-1,nstations,endpoint=False,dtype=int)
    dmult=np.asarray(cfg['radial_distance_core_multipliers'],float); distances=dmult*core_radius
    h=float(cfg['radial_eps_fraction'])*core_radius
    Xp=X+h*mode
    rows=[]
    for d in distances:
        probes=X[ids]+d*NN[ids]
        v0,_=velocity_at_points(probes,X,offsets,core_radius,circulation,threads=threads,require_native=require_native,force_python=force_python)
        vp,_=velocity_at_points(probes,Xp,offsets,core_radius,circulation,threads=threads,require_native=require_native,force_python=force_python)
        dv=(vp-v0)/h
        amp=math.sqrt(float(np.mean(np.sum(dv*dv,axis=1))))
        rows.append({'distance':float(d),'distance_over_core':float(d/core_radius),'response_rms':amp})
    d=np.array([r['distance'] for r in rows]); a=np.array([r['response_rms'] for r in rows]); mask=(a>0)&np.isfinite(a)
    if mask.sum()<4: return {'status':'FIT_FAILED','rows':rows,'predicted_length':predicted}
    d=d[mask]; a=a[mask]; loga=np.log(a)
    M=np.c_[np.ones(len(d)),d]; ce=np.linalg.lstsq(M,loga,rcond=None)[0]; pred_e=M@ce; rss_e=float(np.sum((loga-pred_e)**2)); kappa=float(-ce[1]); L=float(1/kappa) if kappa>0 else float('inf')
    Mp=np.c_[np.ones(len(d)),np.log(d)]; cp=np.linalg.lstsq(Mp,loga,rcond=None)[0]; pred_p=Mp@cp; rss_p=float(np.sum((loga-pred_p)**2))
    n=len(d); aic_e=n*math.log(max(rss_e/n,1e-300))+4; aic_p=n*math.log(max(rss_p/n,1e-300))+4
    tss=float(np.sum((loga-loga.mean())**2)); r2e=1-rss_e/max(tss,1e-300)
    return {'status':'OK','mode':row,'rows':rows,'observed_exp_length':L,'predicted_kelvin_length':predicted,'length_ratio':L/predicted if np.isfinite(L) else float('inf'),'exp_log_r2':r2e,'delta_aic_power_minus_exp':aic_p-aic_e,'exp_kappa':kappa,'power_exponent':float(-cp[1])}


def analyze_case(comps, core_radius, cfg, threads, require_native=True, force_python=False):
    from .geometry import resample_components, edge_cv
    rcomps,X,offsets=resample_components(comps,int(cfg['resample_total_points']),int(cfg['min_points_per_component']))
    circulation=float(cfg.get('circulation',1.0))
    lin=linearized_operator(rcomps,X,offsets,core_radius,circulation,threads,cfg,require_native,force_python)
    disp=fit_dispersion(lin['mode_rows'],cfg)
    radial=radial_response(rcomps,X,offsets,core_radius,circulation,threads,lin,disp,cfg,require_native,force_python) if bool(cfg.get('radial_response_enabled',True)) else {'status':'DISABLED'}
    fit=lin['rigid_fit']; omega=float(np.linalg.norm(fit['omega']))
    sensitivity=[]
    for mult in cfg.get('equilibrium_core_sensitivity_multipliers',[1.0]):
        mult=float(mult)
        if abs(mult-1.0)<1e-15:
            sf=fit
        else:
            vv,_=induced_velocity(X,offsets,core_radius*mult,circulation,threads=threads,require_native=require_native,force_python=force_python)
            sf=rigid_fit(X,vv)
        sensitivity.append({'core_multiplier':mult,'relative_residual':float(sf['relative_residual']),'omega_eff':float(np.linalg.norm(sf['omega'])),'rms_velocity':float(sf['rms_velocity'])})
    if disp.get('status')=='OK' and omega>0:
        disp['gap_to_2omega_ratio']=float(disp['gap_sigma0']/(2*omega)); disp['omega_eff']=omega
    else:
        disp['gap_to_2omega_ratio']=None; disp['omega_eff']=omega
    return {
        'resampled_points':len(X),'resampled_component_points':[len(c) for c in rcomps],'resampled_edge_cv':edge_cv(rcomps),
        'core_radius_model':float(core_radius),'circulation_model':float(cfg.get('circulation',1.0)),'backend':lin['backend'],'runtime_s':lin['runtime_s'],
        'relative_equilibrium':{'relative_residual':float(fit['relative_residual']),'rms_velocity':float(fit['rms_velocity']),'translation':fit['translation'].tolist(),'omega_vector':fit['omega'].tolist(),'omega_eff':omega,'core_sensitivity':sensitivity},
        'basis':lin['basis_meta'],'dispersion':{k:v for k,v in disp.items() if k!='stable_mode_rows'},'radial_response':radial,
        '_artifacts':{'operator_A':lin['operator_A'],'mode_rows':lin['mode_rows']},
    }
