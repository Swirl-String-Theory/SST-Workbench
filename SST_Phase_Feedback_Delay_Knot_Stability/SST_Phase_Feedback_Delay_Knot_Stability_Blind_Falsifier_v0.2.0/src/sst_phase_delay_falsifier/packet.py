from __future__ import annotations
import numpy as np
from .geometry import bishop_frame_closed,kabsch_align,length
from .backend import evolve_pair

def _circular_delta(phi,center=0.0):
    return (phi-center+np.pi)%(2*np.pi)-np.pi

def fit_circular_transport(times,phases,loop_length,fit_skip_fraction=0.10):
    t=np.asarray(times,float); ph=np.unwrap(np.asarray(phases,float))
    i0=max(1,int(round(fit_skip_fraction*len(t))))
    if len(t)-i0<3:
        return {'valid':False,'v_group':np.nan,'slope_angle':np.nan,'r2':np.nan,'angular_span':np.nan}
    tt=t[i0:]; yy=ph[i0:]
    A=np.column_stack([tt,np.ones_like(tt)])
    slope,inter=np.linalg.lstsq(A,yy,rcond=None)[0]
    yh=A@np.array([slope,inter]); ssr=float(np.sum((yy-yh)**2)); sst=float(np.sum((yy-np.mean(yy))**2))
    r2=1.0-ssr/sst if sst>1e-30 else 0.0
    span=float(np.max(yy)-np.min(yy))
    vg=float(loop_length*slope/(2*np.pi))
    return {'valid':True,'v_group':vg,'slope_angle':float(slope),'r2':float(r2),'angular_span':span}

def packet_group_velocity(x,m,gamma,core,gap,tchar,cfg):
    x=np.asarray(x,float); N=len(x); q=2*np.pi*np.arange(N)/N
    _,n,b=bishop_frame_closed(x)
    sig=2*np.pi*float(cfg['envelope_sigma_fraction'])
    env=np.exp(-0.5*(_circular_delta(q)/max(sig,1e-12))**2)
    # Helical quadrature packet biases a traveling, rather than purely standing, carrier.
    p=env[:,None]*(np.cos(m*q)[:,None]*n + np.sin(m*q)[:,None]*b)
    p-=np.mean(p,axis=0,keepdims=True)
    rms=np.sqrt(np.mean(np.sum(p*p,axis=1))); p/=max(rms,1e-300)
    amp=float(cfg['perturb_to_gap'])*gap
    xp=x+amp*p
    steps=int(cfg['steps']); dt=float(cfg['total_time_to_tchar'])*tchar/steps
    sample_every=max(1,steps//int(cfg['samples']))
    evo=evolve_pair(x,xp,steps,dt,gamma,core,sample_every)
    phases=[]; coherences=[]
    unit=np.exp(1j*q)
    for a,bb in zip(evo['a'],evo['b']):
        bal=kabsch_align(a,bb); aa=a-np.mean(a,axis=0,keepdims=True)
        d=bal-aa; w=np.sum(d*d,axis=1); sw=float(np.sum(w))
        if not np.isfinite(sw) or sw<=1e-300:
            phases.append(np.nan); coherences.append(0.0); continue
        z=np.sum(w*unit)/sw
        phases.append(float(np.angle(z))); coherences.append(float(abs(z)))
    phases=np.asarray(phases,float); coh=np.asarray(coherences,float); times=np.asarray(evo['times'],float)
    good=np.isfinite(phases)&np.isfinite(times)
    if good.sum()<4:
        return {'m':int(m),'valid':False,'reason':'insufficient_centroid_samples','v_group':np.nan,'tau_loop':np.nan,'r2':np.nan,'angular_span':np.nan,'median_coherence':float(np.nanmedian(coh))}
    fit=fit_circular_transport(times[good],phases[good],length(x),float(cfg.get('fit_skip_fraction',0.10)))
    medcoh=float(np.nanmedian(coh[good])); vg=fit['v_group']
    valid=(fit['valid'] and np.isfinite(vg) and abs(vg)>float(cfg['v_group_floor']) and
           fit['r2']>=float(cfg['fit_r2_min']) and fit['angular_span']>=float(cfg['angular_span_min']) and
           medcoh>=float(cfg['coherence_min']))
    tau=length(x)/abs(vg) if valid else np.nan
    return {'m':int(m),'valid':bool(valid),'reason':'ok' if valid else 'packet_quality_gate',
            'v_group':float(vg) if np.isfinite(vg) else np.nan,'tau_loop':float(tau) if np.isfinite(tau) else np.nan,
            'r2':fit['r2'],'angular_span':fit['angular_span'],'median_coherence':medcoh,
            'dt':dt,'steps':steps,'samples':len(times)}
