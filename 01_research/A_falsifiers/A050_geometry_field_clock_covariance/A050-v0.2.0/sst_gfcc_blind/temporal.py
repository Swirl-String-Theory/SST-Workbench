import numpy as np


def mean_autocorrelation(series, max_lag=None):
    x=np.asarray(series,float)
    if x.ndim==1:
        x=x[:,None]
    x=x-np.mean(x,axis=0,keepdims=True)
    nt=x.shape[0]
    if max_lag is None:
        max_lag=max(1,nt//2)
    max_lag=min(int(max_lag),nt-1)
    out=[]
    for j in range(x.shape[1]):
        y=x[:,j]
        den=float(np.dot(y,y))
        if not np.isfinite(den) or den<=1e-30:
            continue
        nfft=1
        while nfft<2*nt:
            nfft*=2
        f=np.fft.rfft(y,n=nfft)
        ac=np.fft.irfft(f*np.conj(f),n=nfft)[:max_lag+1]
        # unbiased lag normalization, then normalize to unit zero-lag
        ac=ac/np.maximum(1,np.arange(nt,nt-max_lag-1,-1))
        if ac[0]>0:
            ac=ac/ac[0]
            out.append(ac)
    if not out:
        return np.full(max_lag+1,np.nan)
    return np.nanmean(np.asarray(out),axis=0)


def integrated_memory_time(acf, dt):
    a=np.asarray(acf,float)
    if len(a)<2 or not np.isfinite(a[0]):
        return float('nan')
    stop=len(a)
    for i in range(1,len(a)):
        if not np.isfinite(a[i]) or a[i]<=0:
            stop=i
            break
    return float(dt)*(1.0+2.0*float(np.nansum(a[1:stop])))


def memory_metrics(series, dt, max_lag=None):
    ac=mean_autocorrelation(series,max_lag=max_lag)
    tau=integrated_memory_time(ac,dt)
    return {
        'lag1': float(ac[1]) if len(ac)>1 and np.isfinite(ac[1]) else float('nan'),
        'memory_time': tau,
        'memory_steps': float(tau/float(dt)) if np.isfinite(tau) and dt>0 else float('nan'),
        'acf': ac.tolist(),
    }


def shuffled_memory_null(series, dt, repeats, rng, max_lag=None):
    x=np.asarray(series,float)
    vals=[]
    for _ in range(int(repeats)):
        y=x.copy()
        for j in range(y.shape[1]):
            y[:,j]=y[rng.permutation(y.shape[0]),j]
        vals.append(memory_metrics(y,dt,max_lag=max_lag))
    ms=np.asarray([v['memory_steps'] for v in vals],float)
    l1=np.asarray([v['lag1'] for v in vals],float)
    return {
        'memory_steps_mean': float(np.nanmean(ms)),
        'memory_steps_std': float(np.nanstd(ms)),
        'lag1_mean': float(np.nanmean(l1)),
        'lag1_std': float(np.nanstd(l1)),
    }
