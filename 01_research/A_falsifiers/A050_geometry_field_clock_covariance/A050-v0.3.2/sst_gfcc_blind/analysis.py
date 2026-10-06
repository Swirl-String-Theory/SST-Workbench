import numpy as np

def spherical_kernel(n, radius_cells):
    a=np.arange(n)
    d=np.minimum(a, n-a)
    X,Y,Z=np.meshgrid(d,d,d,indexing="ij")
    mask=(X*X+Y*Y+Z*Z)<=float(radius_cells)**2
    k=mask.astype(float)
    k/=k.sum()
    return k

def smooth_periodic(q, radius_cells):
    k=spherical_kernel(q.shape[0], radius_cells)
    return np.fft.ifftn(np.fft.fftn(q)*np.fft.fftn(k)).real

def variance_scaling_scalar(q, radii):
    vals=[]
    for r in radii:
        z=smooth_periodic(q,r)
        vals.append(float(np.var(z)))
    return np.asarray(vals,float)

def variance_scaling_vector(u, radii):
    vals=[]
    for r in radii:
        acc=0.0
        for j in range(3):
            z=smooth_periodic(u[...,j],r)
            acc += float(np.var(z))
        vals.append(acc)
    return np.asarray(vals,float)

def fit_power(radii, values, min_radius):
    r=np.asarray(radii,float); y=np.asarray(values,float)
    mask=(r>=float(min_radius)) & np.isfinite(y) & (y>0)
    if mask.sum()<3:
        return {"exponent": float("nan"), "r2": float("nan"), "slope": float("nan"), "intercept": float("nan"), "n_fit": int(mask.sum())}
    x=np.log(r[mask]); z=np.log(y[mask])
    slope,intercept=np.polyfit(x,z,1)
    pred=slope*x+intercept
    ss_res=float(np.sum((z-pred)**2)); ss_tot=float(np.sum((z-z.mean())**2))
    r2=1.0-ss_res/ss_tot if ss_tot>0 else 1.0
    return {"exponent": float(-slope), "r2": float(r2), "slope": float(slope), "intercept": float(intercept), "n_fit": int(mask.sum())}

def shuffled_scaling(q, radii, repeats, rng):
    flat=np.asarray(q,float).ravel().copy()
    allv=[]
    for _ in range(int(repeats)):
        rng.shuffle(flat)
        qq=flat.reshape(q.shape)
        allv.append(variance_scaling_scalar(qq,radii))
    return np.mean(np.asarray(allv),axis=0)

def radial_autocorrelation(q):
    q=np.asarray(q,float); q=q-q.mean(); n=q.shape[0]
    h=np.fft.fftn(q); ac=np.fft.ifftn(h*np.conj(h)).real
    ac=np.fft.fftshift(ac); ac/=max(float(ac.max()),1e-30)
    c=np.arange(n)-n//2
    X,Y,Z=np.meshgrid(c,c,c,indexing="ij")
    rr=np.sqrt(X*X+Y*Y+Z*Z)
    bins=np.arange(0,n//2+1)
    out=[]
    for i in range(len(bins)-1):
        m=(rr>=bins[i])&(rr<bins[i+1])
        out.append(float(ac[m].mean()) if np.any(m) else float('nan'))
    out=np.asarray(out)
    corr_len=float('nan')
    for i,v in enumerate(out):
        if np.isfinite(v) and v<=np.exp(-1):
            corr_len=float(i); break
    return out, corr_len

def temporal_integrated_variance(series, dt):
    # series shape: time x probes. Global spatial mean is already zero for the scalar field.
    x=np.asarray(series,float)
    cum=np.cumsum(x,axis=0)*float(dt)
    v=np.var(cum,axis=1)
    t=np.arange(1,len(v)+1,dtype=float)*float(dt)
    return t,v

def fit_temporal(t,v):
    t=np.asarray(t,float); v=np.asarray(v,float)
    start=max(1,len(t)//3)
    m=(np.arange(len(t))>=start)&(v>0)&np.isfinite(v)
    if m.sum()<3:
        return {"exponent":float('nan'),"r2":float('nan')}
    x=np.log(t[m]); y=np.log(v[m])
    slope,intercept=np.polyfit(x,y,1)
    pred=slope*x+intercept
    ssr=float(np.sum((y-pred)**2)); sst=float(np.sum((y-y.mean())**2))
    return {"exponent":float(slope),"r2":float(1-ssr/sst if sst>0 else 1.0)}
