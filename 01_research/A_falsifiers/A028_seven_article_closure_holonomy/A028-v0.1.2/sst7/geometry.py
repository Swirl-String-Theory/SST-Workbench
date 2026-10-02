from __future__ import annotations
import numpy as np

def close_curve(p):
    p=np.asarray(p,float)
    if np.linalg.norm(p[0]-p[-1]) < 1e-12*max(1.0,np.ptp(p,axis=0).max()):
        return p[:-1]
    return p

def curve_length(p):
    p=close_curve(p)
    d=np.roll(p,-1,axis=0)-p
    return float(np.linalg.norm(d,axis=1).sum())

def resample_closed(p,n):
    p=close_curve(p)
    q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1)
    s=np.r_[0,np.cumsum(ds)]
    L=s[-1]
    if not np.isfinite(L) or L<=0: raise ValueError('degenerate curve')
    t=np.linspace(0,L,n,endpoint=False)
    out=np.empty((n,3),float)
    for j in range(3): out[:,j]=np.interp(t,s,q[:,j])
    return out

def closure_gap_ratio(p):
    """Endpoint gap divided by total polyline length.

    A closed polygon often omits the duplicated endpoint, so the closing edge is
    normally O(1/N) of the total length rather than zero.  Normalizing by total
    length therefore detects grossly open input without falsely rejecting a valid
    closed polygon whose last sample is simply adjacent to the first.
    """
    p=np.asarray(p,float)
    if len(p)<2:
        return float('inf')
    seg=np.linalg.norm(np.diff(p,axis=0),axis=1)
    L=float(seg.sum())
    return float(np.linalg.norm(p[0]-p[-1])/max(L,1e-300))


def gauss_linking(a,b):
    """Midpoint quadrature of the Gauss linking integral for two closed polygons.

    This is a centerline-only diagnostic.  It does not identify phase-fiber or
    vorticity-tube topology.
    """
    a=close_curve(np.asarray(a,float)); b=close_curve(np.asarray(b,float))
    da=np.roll(a,-1,axis=0)-a; db=np.roll(b,-1,axis=0)-b
    ma=0.5*(a+np.roll(a,-1,axis=0)); mb=0.5*(b+np.roll(b,-1,axis=0))
    total=0.0
    # chunk over the second curve to bound memory on large links
    chunk=512
    for j0 in range(0,len(b),chunk):
        j1=min(len(b),j0+chunk)
        r=ma[:,None,:]-mb[None,j0:j1,:]
        cross=np.cross(da[:,None,:],db[None,j0:j1,:])
        r2=np.sum(r*r,axis=-1)
        mask=r2>1e-30
        dot=np.sum(r*cross,axis=-1)
        total+=float(np.sum(np.where(mask,dot/(np.maximum(r2,1e-300)**1.5),0.0)))
    return total/(4*np.pi)

def normalized_mode_power(p,mmax=16):
    p=resample_closed(p,max(64,len(close_curve(p))))
    p=p-p.mean(axis=0)
    z=np.fft.rfft(p,axis=0)
    power=(np.abs(z)**2).sum(axis=1)
    power=power[1:mmax+1]
    s=power.sum()
    return power/s if s>0 else power

def mode_corr(a,b):
    n=min(len(a),len(b)); a=np.asarray(a[:n]); b=np.asarray(b[:n])
    if np.std(a)==0 or np.std(b)==0: return 1.0 if np.allclose(a,b) else 0.0
    return float(np.corrcoef(a,b)[0,1])
