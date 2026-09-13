from __future__ import annotations
import numpy as np
from scipy.optimize import minimize_scalar
TWOPI=2*np.pi

def wrap(x): return float(np.angle(np.exp(1j*float(x))))
def wrap_positive(x): return float(np.mod(float(x),TWOPI))

def loop_wavenumber(length_over_a,m,n,holonomy,closure_offset=0.0):
    """Bishop-frame loop closure: k L + m*holonomy = 2pi(n+offset)."""
    L=float(length_over_a); return float((TWOPI*(float(n)+float(closure_offset))-float(m)*float(holonomy))/max(L,1e-14))

def _packet_complex(t,q,amp,co):
    domega=np.polyval(co,q)-np.polyval(co,0.0)
    return np.sum(amp*np.exp(-1j*domega*float(t)))

def wavepacket_return(length_over_a,k0,omega0,poly_coeff,group_velocity,n_modes=31,n_times=401,
                      phase_step_max_rad=.05,phase_uncertainty_max_rad=.35,
                      dispersion_omega_rmse=0.0,return_coherence_min=.5):
    """Measure the first coherent loop return and its carrier phase.

    v0.1.2 deliberately separates envelope timing from carrier-phase resolution:
      1) a coarse grid locates the return envelope;
      2) bounded continuous optimization refines the envelope maximum;
      3) the optimizer tolerance is tied to |omega| dt <= phase_step_max_rad;
      4) phase uncertainty includes both return-time uncertainty and measured
         local dispersion-fit frequency uncertainty.

    No delay or target phase is supplied to the dynamics.
    """
    L=float(length_over_a); vg=float(group_velocity); om=float(omega0)
    if not np.isfinite(vg) or abs(vg)<1e-8:return {'available':False,'reason':'near-zero group velocity'}
    if not np.isfinite(om):return {'available':False,'reason':'non-finite modal frequency'}
    tau_pred=L/abs(vg)
    j=np.arange(-(int(n_modes)//2),int(n_modes)//2+1)
    q=TWOPI*j/L
    sig=max(2*TWOPI/L,0.22*abs(k0)+1e-3)
    amp=np.exp(-0.5*(q/sig)**2); amp/=np.sum(amp)
    co=np.asarray(poly_coeff,float)
    ncoarse=max(101,int(n_times))
    t=np.linspace(0,1.55*tau_pred,ncoarse)
    A=np.array([_packet_complex(tt,q,amp,co) for tt in t])
    mag=np.abs(A)
    mask=(t>=.55*tau_pred)&(t<=1.45*tau_pred)
    if not np.any(mask):return {'available':False,'reason':'empty return window'}
    inds=np.where(mask)[0]; ip=int(inds[np.argmax(mag[inds])])
    il=max(int(inds[0]),ip-1); ir=min(int(inds[-1]),ip+1)
    left=float(t[il]); right=float(t[ir])
    if not right>left:return {'available':False,'reason':'degenerate refinement bracket'}

    # The phase-resolution target controls the *refinement tolerance*, avoiding
    # the millions of global samples that slow group-velocity branches would
    # otherwise require while still resolving the carrier phase locally.
    dt_phase_target=float(phase_step_max_rad)/max(abs(om),1e-12)
    coarse_dt=float(t[1]-t[0]) if len(t)>1 else right-left
    xatol=max(min(dt_phase_target/20.0,coarse_dt/1000.0),1e-12*max(1.0,tau_pred))
    opt=minimize_scalar(lambda z:-abs(_packet_complex(z,q,amp,co)),bounds=(left,right),method='bounded',options={'xatol':xatol,'maxiter':300})
    tau=float(opt.x if opt.success else t[ip])
    astar=_packet_complex(tau,q,amp,co)
    coherence=float(abs(astar)/max(abs(_packet_complex(0.0,q,amp,co)),1e-30))

    # Repeat at tighter tolerance; their displacement is an empirical numerical
    # return-time uncertainty rather than an assumed delay uncertainty.
    xatol2=max(xatol/8.0,1e-13*max(1.0,tau_pred))
    opt2=minimize_scalar(lambda z:-abs(_packet_complex(z,q,amp,co)),bounds=(left,right),method='bounded',options={'xatol':xatol2,'maxiter':400})
    tau2=float(opt2.x if opt2.success else tau)
    tau_refined=.5*(tau+tau2)
    tau_unc=max(abs(tau2-tau),xatol2)
    aref=_packet_complex(tau_refined,q,amp,co)

    # Local envelope phase derivative. Together with -omega0 this gives the
    # total carrier-phase sensitivity to return-time uncertainty.
    dtloc=max(min(dt_phase_target/4.0,(right-left)/1000.0),1e-12*max(1.0,tau_pred))
    ap=_packet_complex(tau_refined+dtloc,q,amp,co); am=_packet_complex(tau_refined-dtloc,q,amp,co)
    env_phase_rate=wrap(np.angle(ap)-np.angle(am))/(2.0*dtloc)
    total_phase_rate=-om+env_phase_rate
    rmse=max(float(dispersion_omega_rmse),0.0) if np.isfinite(dispersion_omega_rmse) else np.inf
    phase_unc_time=abs(total_phase_rate)*tau_unc
    phase_unc_disp=rmse*abs(tau_refined)
    phase_unc=float(np.hypot(phase_unc_time,phase_unc_disp))
    phase=float(wrap(-om*tau_refined+float(np.angle(aref))))
    phase_step=float(abs(om)*dt_phase_target)
    phase_valid=bool(np.isfinite(phase_unc) and phase_unc<=float(phase_uncertainty_max_rad) and phase_step<=float(phase_step_max_rad)*(1+1e-12) and coherence>=float(return_coherence_min))
    return {
        'available':True,
        'tau_group':tau_pred,
        'tau_return':tau_refined,
        'tau_relative_error':float(abs(tau_refined/tau_pred-1)),
        'return_coherence':coherence,
        'loop_phase':phase,
        'phase_valid':phase_valid,
        'phase_sampling_step_rad':phase_step,
        'phase_step_max_rad':float(phase_step_max_rad),
        'phase_time_step_target':dt_phase_target,
        'phase_uncertainty_rad':phase_unc,
        'phase_uncertainty_from_time_rad':float(phase_unc_time),
        'phase_uncertainty_from_dispersion_rad':float(phase_unc_disp),
        'tau_return_numerical_uncertainty':float(tau_unc),
        'dispersion_omega_rmse':float(rmse),
        'carrier_phase_cycles_at_return':float(abs(om)*tau_refined/TWOPI),
        'coarse_peak_index':ip,
        'continuous_peak_refined':True,
        'optimizer_xatol':float(xatol2),
    }

def circular_features(phi): return np.c_[np.ones(len(phi)),np.cos(phi),np.sin(phi)]

def circular_regression_cv(phi,y,groups):
    phi=np.asarray(phi,float);y=np.asarray(y,float);groups=np.asarray(groups); pred=np.full(len(y),np.nan)
    ug=list(dict.fromkeys(groups.tolist()))
    for g in ug:
        tr=groups!=g;te=groups==g
        if np.sum(tr)<4:continue
        X=circular_features(phi[tr]); q=np.linalg.lstsq(X,y[tr],rcond=None)[0];pred[te]=circular_features(phi[te])@q
    m=np.isfinite(pred)&np.isfinite(y)
    if np.sum(m)<4:return {'cv_r2':float('nan'),'rmse':float('nan'),'n':int(np.sum(m))}
    ss=float(np.sum((y[m]-pred[m])**2));den=float(np.sum((y[m]-np.mean(y[m]))**2));r2=1-ss/max(den,1e-30);return {'cv_r2':float(r2),'rmse':float(np.sqrt(np.mean((y[m]-pred[m])**2))),'n':int(np.sum(m))}
