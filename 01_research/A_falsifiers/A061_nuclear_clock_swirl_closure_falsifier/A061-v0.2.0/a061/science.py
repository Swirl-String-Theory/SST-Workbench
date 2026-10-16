"""A061 scientific computation. Public blind side: NO private config reads."""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np


def sst28_ratio(x):
    """SST-28 reference ansatz S=sqrt(1-x^2 exp(-2x)); x=r/r_core."""
    x=np.asarray(x,dtype=np.float64)
    z=x*np.exp(-x)
    return np.sqrt(np.maximum(0.0,1.0-z*z))


def sst28_omega_scaled(x):
    """omega_z/(vchar/r_core) for v_phi/vchar=x exp(-x)."""
    x=np.asarray(x,dtype=np.float64)
    return np.exp(-x)*(2.0-x)


def plateau_s(x, winding=1):
    """SST-28 circulatory pole approximation with kappa=2pi*rc*vchar.
    Return NAN if v_phi > vchar; the model then has no real clock rate.
    """
    x=np.asarray(x,dtype=np.float64)
    val=1.0-np.square(winding/np.maximum(x,1e-300))
    return np.where(val>=0,np.sqrt(np.maximum(val,0)),np.nan)


def freq_ratio_perturb(s1,s2):
    return (s1/s2)-1


def crystal_reconstruction(p):
    h=p['Huang_2026']
    shift=h['nu_TS1_Hz']-h['nu_S1_Hz']
    relative=shift/(0.5*(h['nu_TS1_Hz']+h['nu_S1_Hz']))
    return dict(offset_Hz=float(shift),fractional_offset=float(relative),reported_fractional=h['fractional_intercrystal_shift'],
        uncertainty_Hz=h['crystal_relative_uncertainty_of_difference_Hz'],z_zero=float(shift/h['crystal_relative_uncertainty_of_difference_Hz']))


def oscillator_feedback(n=4096, gain=0.38, delay=2, sigma=1., seed=1234):
    """Purely instrumental delayed proportional servo (no physics input).
    e[k+1]=e[k]-gain*e[k-delay]+noise[k]; noise e.g. optical discriminator.
    """
    rng=np.random.default_rng(seed)
    noise=rng.normal(0,sigma,n)
    err=np.zeros(n,dtype=np.float64)
    for k in range(delay,n-1):
        err[k+1]=err[k]-gain*err[k-delay]+noise[k]
    return err


def max_sinusoid_periodogram(t,y,freq_hz):
    """Generalized LS power, normalized by total centered sum of squares.
    De-mean t,y; regress sin & cos including near-orthogonal cross term.
    Values in [0,1]. No timing assumptions; no interpolation.
    """
    t=np.asarray(t,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    w=np.asarray(freq_hz,dtype=np.float64)
    if len(y)!=len(t) or len(y)<12 or (np.diff(t)<=0).any():raise ValueError('invalid time series')
    t=t-t[0]; y=y-y.mean()
    ang=2*np.pi*np.outer(w,t)
    c=np.cos(ang);s=np.sin(ang)
    c-=c.mean(axis=1)[:,None];s-=s.mean(axis=1)[:,None]
    a=np.sum(c*c,axis=1); b=np.sum(s*s,axis=1); d=np.sum(s*c,axis=1)
    cy=c@y;sy=s@y
    det=a*b-d*d
    good=det>1e-20
    out=np.full(len(w),np.nan)
    out[good]=(b[good]*cy[good]**2+a[good]*sy[good]**2-2*d[good]*cy[good]*sy[good])/det[good]/max(float(y@y),1e-300)
    return np.clip(out,0,1)


def monte_carlo_search(t,y,seed=61061,n_mc=160,n_freq=240,alpha=0.05,block=7):
    """Generalized sinusoid scan with an exploratory *global* block-bootstrap null.

    Precomputes the design matrix and scores all bootstrap replicates in batches.
    This tests for coherent variation against a stationary resampling null, not
    against a fully calibrated clock-control noise model or an SST-specific theory.
    """
    t=np.asarray(t,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    if len(t)!=len(y) or len(t)<60 or not np.isfinite(t).all() or not np.isfinite(y).all():
        raise ValueError('>=60 finite observations required')
    if np.any(np.diff(t)<=0):raise ValueError('nonmonotonic or duplicate timing')
    span=t[-1]-t[0];dt=float(np.median(np.diff(t)))
    freqs=np.geomspace(1/span,0.5/dt,n_freq)
    ang=2*np.pi*freqs[:,None]*(t[None,:]-t[0])
    c=np.cos(ang);s=np.sin(ang)
    c-=c.mean(axis=1,keepdims=True);s-=s.mean(axis=1,keepdims=True)
    a=np.einsum('ij,ij->i',c,c);b=np.einsum('ij,ij->i',s,s)
    d=np.einsum('ij,ij->i',c,s)
    det=a*b-d*d;good=det>1e-20
    def scores(Y):
        Y=Y-np.mean(Y,axis=0,keepdims=True)
        cy=c@Y;sy=s@Y
        denom=np.maximum(np.sum(Y*Y,axis=0),1e-300)
        P=(b[:,None]*cy*cy+a[:,None]*sy*sy-2*d[:,None]*cy*sy)/np.maximum(det[:,None],1e-300)/denom[None,:]
        P[~good,:]=np.nan
        return np.clip(P,0,1)
    observed=scores(y[:,None])[:,0]
    rng=np.random.default_rng(seed);n=len(y)
    yy=y-y.mean();nullmax=[]
    # Bound scratch memory and avoid recomputing the FFT-like regressors.
    for first in range(0,n_mc,16):
        count=min(16,n_mc-first)
        xs=[]
        for _ in range(count):
            starts=rng.integers(0,n,size=(n+block-1)//block)
            ix=(starts[:,None]+np.arange(block)[None,:])%n
            xs.append(yy[ix.reshape(-1)[:n]])
        sim=np.stack(xs,axis=1)
        nullmax.extend(np.nanmax(scores(sim),axis=0).tolist())
    cutoff=float(np.quantile(nullmax,1-alpha))
    j=int(np.nanargmax(observed))
    return {'best_frequency_Hz':float(freqs[j]),'best_period_s':float(1/freqs[j]),
        'max_power':float(observed[j]),'global_95pct_threshold':cutoff,
        'global_peak_above_threshold':bool(observed[j]>cutoff),
        'assumed_null':f'circular block bootstrap, block={block} samples, weak stationarity required',
        'n_data':len(t),'span_s':float(span),'median_cadence_s':dt,'n_mc':n_mc,'n_freq':n_freq,
        'frequency_min_Hz':float(freqs[0]),'frequency_max_Hz':float(freqs[-1])}


def load_two_col_csv(path):
    a=np.genfromtxt(path,delimiter=',',dtype=np.float64,comments='#',invalid_raise=False)
    if a.ndim==1:a=a.reshape(1,-1)
    if a.shape[1]<2:raise ValueError('At least 2 columns required')
    a=a[:,:2];a=a[np.isfinite(a).all(axis=1)]
    a=a[np.argsort(a[:,0])]
    if len(a)<12 or np.any(np.diff(a[:,0])<=0):raise ValueError('invalid/duplicate time stamps')
    return a[:,0],a[:,1]
