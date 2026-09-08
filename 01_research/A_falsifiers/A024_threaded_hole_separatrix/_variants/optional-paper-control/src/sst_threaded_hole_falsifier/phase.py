from __future__ import annotations
import numpy as np
TWOPI=2*np.pi

def unwrap_fit_rate(t,phi):
    t=np.asarray(t,float);phi=np.unwrap(np.asarray(phi,float));m=np.isfinite(t)&np.isfinite(phi);t=t[m];phi=phi[m]
    if len(t)<3 or np.ptp(t)<=1e-14:return float('nan'),float('nan')
    X=np.c_[np.ones_like(t),t];q=np.linalg.lstsq(X,phi,rcond=None)[0];pred=X@q
    return float(q[1]),float(np.sqrt(np.mean((phi-pred)**2)))

def best_small_rational_lock(omega_carrier,omega_thread,max_order=8):
    wc=float(omega_carrier);wt=float(omega_thread)
    if not np.isfinite(wc) or not np.isfinite(wt) or (abs(wc)+abs(wt))<1e-12:return {'p':0,'q':0,'residual':float('nan'),'ratio_thread_over_carrier':float('nan')}
    best=None
    for p in range(1,int(max_order)+1):
        for q in range(1,int(max_order)+1):
            num=abs(p*wc-q*wt);den=.5*(abs(p*wc)+abs(q*wt))+1e-14;r=num/den;key=(r,p+q,p,q)
            if best is None or key<best[0]:best=(key,p,q,r)
    return {'p':best[1],'q':best[2],'residual':float(best[3]),'ratio_thread_over_carrier':float(wt/wc) if abs(wc)>1e-14 else float('nan')}

def torus_poloidal_phase(curve):
    """Geometric phase of a T(1,1)-like ring on a common torus.

    Uses the phase of (rho-<rho> + i z) relative to toroidal azimuth theta,
    therefore it survives uniform arclength redistribution.
    """
    c=np.asarray(curve,float);theta=np.arctan2(c[:,1],c[:,0]);rho=np.sqrt(c[:,0]**2+c[:,1]**2);u=(rho-rho.mean())+1j*(c[:,2]-c[:,2].mean());z=np.mean(u*np.exp(-1j*theta))
    return float(np.angle(z)) if abs(z)>1e-14 else float('nan')

def helix_phase(reference,moving):
    """Geometric phase of the central helical pass, independent of marker index."""
    ref=np.asarray(reference,float);mov=np.asarray(moving,float)
    # Far return legs have much larger cylindrical radius; use the central 45%.
    rr=np.sqrt(ref[:,0]**2+ref[:,1]**2);rm=np.sqrt(mov[:,0]**2+mov[:,1]**2);tr=np.quantile(rr,.45);tm=np.quantile(rm,.45);a=ref[rr<=tr];b=mov[rm<=tm]
    if len(a)<6 or len(b)<6:return float('nan')
    za=a[:,2];tha=np.unwrap(np.arctan2(a[:,1],a[:,0]));A=np.c_[np.ones_like(za),za];q=np.linalg.lstsq(A,tha,rcond=None)[0];k=float(q[1])
    def phase(c):
        z=c[:,2];th=np.arctan2(c[:,1],c[:,0]);w=np.mean(np.exp(1j*(th-k*z)));return float(np.angle(w)) if abs(w)>1e-14 else float('nan')
    return float(np.angle(np.exp(1j*(phase(b)-phase(a)))))

def phase_lock_metrics(history,max_order=8):
    rows=[r for r in history if r.get('carrier_component_phase') and r.get('thread_component_phase')]
    if len(rows)<4:return {'available':False,'reason':'insufficient geometric phase history'}
    t=np.asarray([r['tau'] for r in rows],float);ncar=len(rows[0]['carrier_component_phase']);nth=len(rows[0]['thread_component_phase']);cr=[];cf=[];tr=[];tf=[]
    for j in range(ncar):w,e=unwrap_fit_rate(t,[r['carrier_component_phase'][j] for r in rows]);cr.append(w);cf.append(e)
    for j in range(nth):w,e=unwrap_fit_rate(t,[r['thread_component_phase'][j] for r in rows]);tr.append(w);tf.append(e)
    wc=float(np.nanmean(cr));wt=float(np.nanmean(tr));rat=best_small_rational_lock(wc,wt,max_order);cspread=float(np.nanstd(cr)/max(abs(wc),1e-12)) if np.isfinite(wc) else float('nan');tspread=float(np.nanstd(tr)/max(abs(wt),1e-12)) if np.isfinite(wt) else float('nan');score=float(rat['residual']+min(cspread,10.)+.25*min(tspread,10.)) if np.isfinite(rat['residual']) else float('nan')
    return {'available':True,'carrier_phase_rates':cr,'thread_phase_rates':tr,'carrier_mean_phase_rate':wc,'thread_mean_phase_rate':wt,'carrier_rate_cv':cspread,'thread_rate_cv':tspread,'carrier_fit_rms':cf,'thread_fit_rms':tf,'best_rational_p':rat['p'],'best_rational_q':rat['q'],'rational_lock_residual':rat['residual'],'thread_over_carrier_rate':rat['ratio_thread_over_carrier'],'gear_phase_lock_score':score,'interpretation':'v0.2.1 geometric toroidal/poloidal + helix phase; invariant to marker redistribution; no mechanical gear ratio supplied'}
