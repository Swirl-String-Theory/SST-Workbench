from __future__ import annotations
import numpy as np

TWOPI=2*np.pi


def phase_from_shift(shift:int,n:int)->float:
    # align_cyclic rolls moving by +shift to match reference. Geometric phase
    # of moving relative to reference therefore has the opposite sign.
    return float(-TWOPI*int(shift)/max(int(n),1))


def best_cyclic_shift_no_rigid(reference,moving):
    a=np.asarray(reference,float);b=np.asarray(moving,float)
    if len(a)!=len(b): raise ValueError('phase curves must have equal sample counts')
    errs=[]
    for s in range(len(a)):
        d=a-np.roll(b,s,axis=0);errs.append(float(np.mean(np.sum(d*d,axis=1))))
    return int(np.argmin(errs)),float(np.min(errs))


def unwrap_fit_rate(t,phi):
    t=np.asarray(t,float);phi=np.unwrap(np.asarray(phi,float))
    m=np.isfinite(t)&np.isfinite(phi)
    t=t[m];phi=phi[m]
    if len(t)<3 or np.ptp(t)<=1e-14:return float('nan'),float('nan')
    X=np.c_[np.ones_like(t),t];q=np.linalg.lstsq(X,phi,rcond=None)[0];pred=X@q
    rms=float(np.sqrt(np.mean((phi-pred)**2)))
    return float(q[1]),rms


def best_small_rational_lock(omega_carrier,omega_thread,max_order=8):
    wc=float(omega_carrier);wt=float(omega_thread)
    if not np.isfinite(wc) or not np.isfinite(wt) or (abs(wc)+abs(wt))<1e-12:
        return {'p':0,'q':0,'residual':float('nan'),'ratio_thread_over_carrier':float('nan')}
    best=None
    for p in range(1,int(max_order)+1):
        for q in range(1,int(max_order)+1):
            # p*wc ~= q*wt  => wt/wc ~= p/q
            num=abs(p*wc-q*wt);den=.5*(abs(p*wc)+abs(q*wt))+1e-14;r=num/den
            key=(r,p+q,p,q)
            if best is None or key<best[0]:best=(key,p,q,r)
    return {'p':best[1],'q':best[2],'residual':float(best[3]),'ratio_thread_over_carrier':float(wt/wc) if abs(wc)>1e-14 else float('nan')}


def phase_lock_metrics(history,max_order=8):
    """Geometric phase proxy for multi-component carriers + central threads.

    This is deliberately *not* a material-marker gear ratio.  It uses cyclic
    phase of the evolving embedded curves after global carrier alignment.
    """
    rows=[r for r in history if r.get('carrier_component_phase') and r.get('thread_component_phase')]
    if len(rows)<4:
        return {'available':False,'reason':'insufficient phase history'}
    t=np.asarray([r['tau'] for r in rows],float)
    ncar=len(rows[0]['carrier_component_phase']);nth=len(rows[0]['thread_component_phase'])
    carrier_rates=[];carrier_fit=[]
    for j in range(ncar):
        w,e=unwrap_fit_rate(t,[r['carrier_component_phase'][j] for r in rows]);carrier_rates.append(w);carrier_fit.append(e)
    thread_rates=[];thread_fit=[]
    for j in range(nth):
        w,e=unwrap_fit_rate(t,[r['thread_component_phase'][j] for r in rows]);thread_rates.append(w);thread_fit.append(e)
    wc=float(np.nanmean(carrier_rates));wt=float(np.nanmean(thread_rates))
    rat=best_small_rational_lock(wc,wt,max_order)
    cspread=float(np.nanstd(carrier_rates)/(max(abs(wc),1e-12))) if np.isfinite(wc) else float('nan')
    tspread=float(np.nanstd(thread_rates)/(max(abs(wt),1e-12))) if np.isfinite(wt) else float('nan')
    score=float(rat['residual']+min(cspread,10.)+0.25*min(tspread,10.)) if np.isfinite(rat['residual']) else float('nan')
    return {
        'available':True,
        'carrier_phase_rates':carrier_rates,
        'thread_phase_rates':thread_rates,
        'carrier_mean_phase_rate':wc,
        'thread_mean_phase_rate':wt,
        'carrier_rate_cv':cspread,
        'thread_rate_cv':tspread,
        'carrier_fit_rms':carrier_fit,
        'thread_fit_rms':thread_fit,
        'best_rational_p':rat['p'],'best_rational_q':rat['q'],
        'rational_lock_residual':rat['residual'],
        'thread_over_carrier_rate':rat['ratio_thread_over_carrier'],
        'gear_phase_lock_score':score,
        'interpretation':'geometric cyclic-phase proxy; no mechanical gear ratio is supplied to the blind analysis',
    }
