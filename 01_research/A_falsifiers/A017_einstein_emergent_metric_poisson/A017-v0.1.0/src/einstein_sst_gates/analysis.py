from __future__ import annotations
import numpy as np
from .geometry import resample_closed,estimate_thickness,field_velocity_gradient
from .constants import R_C,GAMMA,C_LIGHT,G_NEWTON

def fibonacci_sphere(n):
    i=np.arange(int(n),dtype=float); z=1.0-2.0*(i+0.5)/n; phi=(np.pi*(3.0-np.sqrt(5.0)))*i; r=np.sqrt(np.maximum(0.0,1-z*z))
    return np.column_stack([r*np.cos(phi),r*np.sin(phi),z])

def _fit_slope(x,y,n_tail=None):
    x=np.asarray(x,float);y=np.asarray(y,float);m=np.isfinite(x)&np.isfinite(y)&(x>0)&(y>0);x=x[m];y=y[m]
    if n_tail and len(x)>n_tail: x=x[-n_tail:];y=y[-n_tail:]
    if len(x)<3:return float('nan'),float('nan')
    slope,intercept=np.polyfit(np.log(x),np.log(y),1); pred=intercept+slope*np.log(x); ssr=float(np.sum((np.log(y)-pred)**2));sst=float(np.sum((np.log(y)-np.mean(np.log(y)))**2));r2=1-ssr/sst if sst>0 else 1.0
    return float(slope),float(r2)

def gradient_invariants(v,g):
    # g[...,i,j] = partial_j v_i
    S=0.5*(g+np.swapaxes(g,-1,-2));
    omega=np.stack([g[:,2,1]-g[:,1,2],g[:,0,2]-g[:,2,0],g[:,1,0]-g[:,0,1]],axis=1)
    q=0.5*np.sum(omega*omega,axis=1)-np.sum(S*S,axis=(1,2))
    direct=-np.einsum('mij,mji->m',g,g)
    div=np.trace(g,axis1=1,axis2=2)
    return q,direct,omega,S,div

def analyze_knot(points,cfg,require_cpp=True):
    nres=int(cfg['geometry']['resample_points']); exclude=int(cfg['geometry']['thickness_exclude_steps'])
    rp=resample_closed(points,nres,require_cpp=require_cpp)
    th=estimate_thickness(rp,exclude,require_cpp=require_cpp); delta=float(th['thickness'])
    if not np.isfinite(delta) or delta<=0: raise ValueError('invalid estimated thickness')
    # Normalize to unit core/thickness radius. This makes shape gates scale-free.
    ctr=np.mean(rp,axis=0); pn=(rp-ctr)/delta; length=float(np.linalg.norm(np.roll(pn,-1,axis=0)-pn,axis=1).sum())
    extent=float(np.max(np.linalg.norm(pn,axis=1)))
    dirs=fibonacci_sphere(int(cfg['sampling']['sphere_directions']))
    factors=np.geomspace(float(cfg['sampling']['r_factor_min']),float(cfg['sampling']['r_factor_max']),int(cfg['sampling']['n_shells']))
    radii=factors*max(extent,1.0)
    rows=[]
    for R in radii:
        qpts=dirs*R; v,g=field_velocity_gradient(pn,qpts,1.0,1.0,require_cpp=require_cpp)
        v2=np.sum(v*v,axis=1); vrms=float(np.sqrt(np.mean(v2))); phi=-0.5*v2
        # Einstein-SST shift metric identities at shell level.
        vphys=(GAMMA/R_C)*v
        beta=vphys/C_LIGHT; beta2_phys=np.sum(beta*beta,axis=1)
        clock=np.sqrt(np.maximum(0.0,1.0-beta2_phys))
        # Numerical realization of the effective shift metric.
        gm=np.zeros((len(v),4,4),float); gm[:,1:,1:]=np.eye(3)[None,:,:]
        gm[:,0,0]=-(1.0-beta2_phys); gm[:,0,1:]=beta; gm[:,1:,0]=beta
        det_err=float(np.max(np.abs(np.linalg.det(gm)+1.0)))
        clock_metric=np.sqrt(np.maximum(0.0,-gm[:,0,0]))
        clock_identity_err=float(np.max(np.abs(clock_metric-clock)))
        # Surface forms of the pressure-Poisson and Phi=-v^2/2 integrals.
        adv=np.einsum('mij,mj->mi',g,v)       # (v.grad)v = G v
        grad_half_v2=np.einsum('mji,mj->mi',g,v) # grad(v^2/2)=G^T v
        flux_p=-np.einsum('mi,mi->m',adv,dirs)
        flux_phi=-np.einsum('mi,mi->m',grad_half_v2,dirs)
        area=4*np.pi*R*R
        I_p=float(area*np.mean(flux_p)); I_phi=float(area*np.mean(flux_phi))
        A_p=float(area*np.mean(np.abs(flux_p))); A_phi=float(area*np.mean(np.abs(flux_phi)))
        mu_p=I_p/(4*np.pi); mu_phi=I_phi/(4*np.pi); mu_amp=0.5*R*float(np.mean(v2))
        qinv,direct,omega,S,div=gradient_invariants(v,g)
        cross=np.linalg.norm(np.cross(v,omega),axis=1); den=np.linalg.norm(v,axis=1)*np.linalg.norm(omega,axis=1)
        bel=float(np.median(cross/np.maximum(den,1e-300)))
        rows.append({
            'R_core':float(R),'v_rms_norm':vrms,'v2_mean_norm':float(np.mean(v2)),'v2_cv':float(np.std(v2)/max(np.mean(v2),1e-300)),
            'phi_mean_norm':float(np.mean(phi)),'mu_amp_norm':mu_amp,'I_poisson_norm':I_p,'I_phi_norm':I_phi,'mu_poisson_norm':mu_p,'mu_phi_norm':mu_phi,
            'poisson_cancellation':abs(I_p)/max(A_p,1e-300),'phi_cancellation':abs(I_phi)/max(A_phi,1e-300),
            'beltrami_misalignment_median':bel,'divergence_rms_norm':float(np.sqrt(np.mean(div*div))),
            'poisson_identity_rel_rms':float(np.sqrt(np.mean((qinv-direct)**2))/max(np.sqrt(np.mean(qinv*qinv)),1e-300)),
            'clock_min':float(np.min(clock)),'clock_mean':float(np.mean(clock)),
            'metric_det_error_max':det_err,'clock_identity_error_max':clock_identity_err,
        })
    # Tail fits: direct monopole requires v^2 ~ R^-1 and mu_amp=R v^2/2 plateau.
    r=np.array([z['R_core'] for z in rows]); v2=np.array([z['v2_mean_norm'] for z in rows]); ma=np.array([z['mu_amp_norm'] for z in rows]); mp=np.abs(np.array([z['mu_poisson_norm'] for z in rows])); mph=np.abs(np.array([z['mu_phi_norm'] for z in rows]))
    tail_n=int(cfg['sampling']['tail_fit_shells'])
    s_v2,r2_v2=_fit_slope(r,v2,tail_n); s_ma,r2_ma=_fit_slope(r,ma,tail_n); s_mp,r2_mp=_fit_slope(r,np.maximum(mp,1e-300),tail_n); s_mph,r2_mph=_fit_slope(r,np.maximum(mph,1e-300),tail_n)
    tail=rows[-tail_n:]
    mu_amp_med=float(np.median([z['mu_amp_norm'] for z in tail])); mu_p_med=float(np.median([z['mu_poisson_norm'] for z in tail])); mu_phi_med=float(np.median([z['mu_phi_norm'] for z in tail]))
    scale_mu=GAMMA*GAMMA/R_C
    return {
        'normalized_points':pn,'thickness_raw':delta,'length_raw':float(length*delta),'ropelength_estimate':length,'extent_core':extent,'thickness':th,
        'shells':rows,
        'tail_v2_exponent':float(-s_v2),'tail_v2_fit_r2':r2_v2,'tail_velocity_exponent':float(-0.5*s_v2),'tail_mu_amp_log_slope':s_ma,'tail_mu_amp_fit_r2':r2_ma,
        'tail_mu_poisson_log_slope':s_mp,'tail_mu_poisson_fit_r2':r2_mp,'tail_mu_phi_log_slope':s_mph,'tail_mu_phi_fit_r2':r2_mph,
        'tail_mu_amp_norm_median':mu_amp_med,'tail_mu_poisson_norm_median':mu_p_med,'tail_mu_phi_norm_median':mu_phi_med,
        'tail_poisson_to_amp_ratio':mu_p_med/max(mu_amp_med,1e-300),'tail_phi_to_amp_ratio':mu_phi_med/max(mu_amp_med,1e-300),'tail_poisson_to_phi_ratio':mu_p_med/(mu_phi_med if abs(mu_phi_med)>1e-300 else np.nan),
        'tail_poisson_positive_fraction':float(np.mean([z['mu_poisson_norm']>0 for z in tail])),
        'tail_anisotropy_median':float(np.median([z['v2_cv'] for z in tail])),'tail_beltrami_misalignment_median':float(np.median([z['beltrami_misalignment_median'] for z in tail])),
        'poisson_identity_rel_rms_max':float(np.max([z['poisson_identity_rel_rms'] for z in rows])),'divergence_rms_norm_max':float(np.max([z['divergence_rms_norm'] for z in rows])),
        'mu_amp_phys_m3_s2':mu_amp_med*scale_mu,'mu_poisson_phys_m3_s2':mu_p_med*scale_mu,'mu_phi_phys_m3_s2':mu_phi_med*scale_mu,
        'mass_amp_kg':mu_amp_med*scale_mu/G_NEWTON,'mass_poisson_kg':mu_p_med*scale_mu/G_NEWTON,'mass_phi_kg':mu_phi_med*scale_mu/G_NEWTON,
    }
