import numpy as np


def mean_autocorrelation(series, max_lag=None):
    x=np.asarray(series,float)
    if x.ndim==1:
        x=x[:,None]
    x=x-np.mean(x,axis=0,keepdims=True)
    nt=x.shape[0]
    if nt<2:
        return np.full(1,np.nan)
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
        ac=ac/np.maximum(1,np.arange(nt,nt-max_lag-1,-1))
        if ac[0]>0:
            ac=ac/ac[0]
            out.append(ac)
    if not out:
        return np.full(max_lag+1,np.nan)
    return np.nanmean(np.asarray(out),axis=0)


def integrated_memory_time(acf, dt):
    """Legacy v0.2.0 estimator: stop at first non-positive lag."""
    a=np.asarray(acf,float)
    if len(a)<2 or not np.isfinite(a[0]):
        return float('nan')
    stop=len(a)
    for i in range(1,len(a)):
        if not np.isfinite(a[i]) or a[i]<=0:
            stop=i
            break
    return float(dt)*(1.0+2.0*float(np.nansum(a[1:stop])))


def initial_positive_sequence_time(acf, dt):
    """Pairwise initial-positive-sequence estimator for integrated correlation time."""
    a=np.asarray(acf,float)
    if len(a)<2 or not np.isfinite(a[0]):
        return float('nan')
    s=0.0
    i=1
    while i < len(a):
        if i+1 < len(a):
            pair=a[i]+a[i+1]
            if not np.isfinite(pair) or pair<=0:
                break
            s += float(pair)
            i += 2
        else:
            if not np.isfinite(a[i]) or a[i]<=0:
                break
            s += float(a[i]); i += 1
    return float(dt)*(1.0+2.0*s)


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


def phase_randomized_surrogate(series, rng):
    """Preserve each probe power spectrum while randomizing Fourier phase.

    This is a diagnostic surrogate, not an ACF-null: by Wiener-Khinchin it can
    retain two-point temporal memory while removing detailed phase structure.
    """
    x=np.asarray(series,float)
    if x.ndim==1: x=x[:,None]
    n=x.shape[0]
    y=np.empty_like(x)
    for j in range(x.shape[1]):
        z=x[:,j]-np.mean(x[:,j])
        f=np.fft.rfft(z)
        ph=rng.uniform(0.0,2.0*np.pi,len(f))
        ph[0]=0.0
        if n%2==0 and len(ph)>1:
            ph[-1]=0.0
        fr=np.abs(f)*np.exp(1j*ph)
        y[:,j]=np.fft.irfft(fr,n=n)+np.mean(x[:,j])
    return y


def _circular_block_bootstrap(x, block, rng):
    x=np.asarray(x,float); n=len(x)
    starts=rng.integers(0,n,size=int(np.ceil(n/block)))
    idx=np.concatenate([(np.arange(block)+s)%n for s in starts])[:n]
    return x[idx]


def bootstrap_ips_memory(series, dt, repeats, rng, max_lag, ci=0.95):
    x=np.asarray(series,float)
    if x.ndim==1: x=x[:,None]
    n=len(x); block=max(4,int(round(np.sqrt(max(n,1)))))
    vals=[]
    for _ in range(int(repeats)):
        y=_circular_block_bootstrap(x,block,rng)
        ac=mean_autocorrelation(y,max_lag=max_lag)
        vals.append(initial_positive_sequence_time(ac,dt))
    a=np.asarray(vals,float); a=a[np.isfinite(a)]
    if len(a)==0:
        return {'low':float('nan'),'high':float('nan'),'median':float('nan'),'block_length':block,'repeats':int(repeats)}
    qtail=(1.0-float(ci))/2.0
    return {'low':float(np.quantile(a,qtail)),'high':float(np.quantile(a,1-qtail)),'median':float(np.median(a)),'block_length':block,'repeats':int(repeats)}


def memory_convergence(series, sample_steps, sample_dt, cfg, legacy_cfg, rng):
    x=np.asarray(series,float); steps=np.asarray(sample_steps,int)
    windows=[]
    for w in cfg['window_steps']:
        m=steps<=int(w); xx=x[m]
        n=len(xx)
        max_lag=min(int(cfg['max_lag_cap']),max(2,int(np.floor(n*float(cfg['max_lag_fraction']))))) if n>=4 else max(1,n-1)
        ac=mean_autocorrelation(xx,max_lag=max_lag)
        tau=initial_positive_sequence_time(ac,sample_dt)
        boot=bootstrap_ips_memory(xx,sample_dt,int(cfg['bootstrap_repeats']),rng,max_lag,float(cfg['bootstrap_ci'])) if n>=8 else {'low':float('nan'),'high':float('nan'),'median':float('nan'),'block_length':None,'repeats':0}
        legacy=memory_metrics(xx,sample_dt,max_lag=int(legacy_cfg['max_lag_samples']))
        null=shuffled_memory_null(xx,sample_dt,int(legacy_cfg['shuffle_repeats']),rng,max_lag=int(legacy_cfg['max_lag_samples']))
        ratio=float(legacy['memory_steps']/max(null['memory_steps_mean'],1e-12)) if np.isfinite(legacy['memory_steps']) else float('nan')
        lag_excess=float(legacy['lag1']-null['lag1_mean']) if np.isfinite(legacy['lag1']) else float('nan')
        legacy_pass=bool(np.isfinite(ratio) and np.isfinite(lag_excess) and ratio>=float(legacy_cfg['memory_ratio_min']) and lag_excess>=float(legacy_cfg['lag1_excess_min']))
        windows.append({'window_steps':int(w),'sample_count':int(n),'ips_memory_time':float(tau),'ips_memory_steps':float(tau/sample_dt) if np.isfinite(tau) else float('nan'),'bootstrap_ci':boot,'legacy_memory_steps':legacy['memory_steps'],'legacy_memory_ratio_to_null':ratio,'legacy_lag1_excess':lag_excess,'legacy_pass':legacy_pass,'acf':ac.tolist()})
    final=windows[-2:]
    present=bool(len(final)==2 and all(z['legacy_pass'] for z in final))
    rel=float('inf')
    overlap=False
    if len(final)==2 and all(np.isfinite(z['ips_memory_time']) for z in final):
        a,b=final[0]['ips_memory_time'],final[1]['ips_memory_time']
        rel=float(abs(b-a)/max(abs(a),abs(b),1e-12))
        ci0,ci1=final[0]['bootstrap_ci'],final[1]['bootstrap_ci']
        if all(np.isfinite([ci0['low'],ci0['high'],ci1['low'],ci1['high']])):
            overlap=max(ci0['low'],ci1['low'])<=min(ci0['high'],ci1['high'])
    conv=bool(present and rel<=float(cfg['relative_change_max']) and (overlap or not bool(cfg['require_bootstrap_ci_overlap'])))
    pr=phase_randomized_surrogate(x,rng)
    prac=mean_autocorrelation(pr,max_lag=min(int(cfg['max_lag_cap']),max(2,len(pr)//4)))
    prtau=initial_positive_sequence_time(prac,sample_dt)
    if not present: status='TEMPORAL_MEMORY_NOT_REPRODUCED'
    elif not conv: status='TEMPORAL_MEMORY_PRESENT_NOT_CONVERGED'
    else: status='TEMPORAL_MEMORY_CONVERGED'
    return {'status':status,'present_final_two':present,'converged':conv,'final_relative_change':rel,'final_bootstrap_ci_overlap':bool(overlap),'windows':windows,'phase_randomized_diagnostic':{'ips_memory_time':float(prtau),'acf':prac.tolist()}}
