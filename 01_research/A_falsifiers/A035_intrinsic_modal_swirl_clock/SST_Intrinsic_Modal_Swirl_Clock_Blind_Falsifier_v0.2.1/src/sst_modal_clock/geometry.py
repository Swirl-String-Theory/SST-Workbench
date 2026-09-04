from pathlib import Path
import re
import numpy as np
EXTS={'.txt','.xyz','.csv','.dat','.pts'}

def read_xyz(path):
    pts=[]
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip().replace(',',' ')
        if not s or s.startswith(('#','//',';')): continue
        vals=[]
        for tok in s.split():
            try: vals.append(float(tok))
            except ValueError: pass
        if len(vals)>=3 and np.isfinite(vals[:3]).all(): pts.append(vals[:3])
    a=np.asarray(pts,float)
    if len(a)>2 and np.linalg.norm(a[0]-a[-1])<1e-10*max(1.0,float(np.ptp(a,axis=0).max())): a=a[:-1]
    if len(a)<16: raise ValueError(f'{path}: fewer than 16 XYZ points')
    return a

def discover(root,source_regex=None):
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(root)
    rx=re.compile(source_regex,re.I) if source_regex else None; out=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in EXTS: continue
        if rx and not rx.search(p.name): continue
        try: out.append((p,read_xyz(p)))
        except Exception: pass
    if not out: raise RuntimeError(f'No parseable centerlines found under {root}' + (f' matching {source_regex}' if source_regex else ''))
    return out

def resample_closed(x,n):
    x=np.asarray(x,float); y=np.vstack([x,x[0]])
    ds=np.linalg.norm(np.diff(y,axis=0),axis=1); s=np.r_[0.,np.cumsum(ds)]; L=s[-1]
    if L<=1e-15: raise ValueError('degenerate closed curve')
    tgt=np.linspace(0,L,n,endpoint=False); out=np.empty((n,3))
    for d in range(3): out[:,d]=np.interp(tgt,s,y[:,d])
    return out

def centroid(x): return np.mean(np.asarray(x,float),axis=0)
def radius_gyration(x):
    y=np.asarray(x,float)-centroid(x); return float(np.sqrt(np.mean(np.sum(y*y,axis=1))))
def normalize(x):
    y=np.asarray(x,float)-centroid(x); rg=radius_gyration(y)
    if rg<=1e-15: raise ValueError('degenerate geometry')
    return y/rg,rg

def tangents(x):
    t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0); n=np.linalg.norm(t,axis=1); n[n<1e-15]=1.; return t/n[:,None]
def radial_normal(x):
    x=np.asarray(x,float); t=tangents(x); r=x-centroid(x); n=r-(r*t).sum(1)[:,None]*t; nn=np.linalg.norm(n,axis=1)
    bad=nn<1e-10
    if bad.any():
        c=np.roll(t,-1,axis=0)-np.roll(t,1,axis=0); n[bad]=c[bad]; nn=np.linalg.norm(n,axis=1)
    nn[nn<1e-15]=1.; return n/nn[:,None]
def remove_tangent(v,x):
    t=tangents(x); return v-(v*t).sum(1)[:,None]*t

def remove_rigid(v,x):
    x=np.asarray(x,float)-centroid(x); v=np.asarray(v,float); v=v-v.mean(0)
    A=[]; b=[]
    for r,u in zip(x,v):
        rx,ry,rz=r; A.extend([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]]); b.extend(u.tolist())
    A=np.asarray(A,float); b=np.asarray(b,float); om=np.linalg.lstsq(A,b,rcond=None)[0]
    rot=np.cross(np.broadcast_to(om,x.shape),x)
    return v-rot

def broadband_probe(x,harmonics=(1,2,3,4)):
    x=np.asarray(x,float); n=len(x); th=2*np.pi*np.arange(n)/n; n1=radial_normal(x); t=tangents(x)
    n2=np.cross(t,n1); nn=np.linalg.norm(n2,axis=1); nn[nn<1e-15]=1; n2=n2/nn[:,None]
    a=np.zeros(n); b=np.zeros(n)
    for m in harmonics:
        a += np.cos(m*th+0.37*m)/(m**1.25); b += np.sin(m*th+0.61*m)/(m**1.25)
    v=a[:,None]*n1+b[:,None]*n2; v=remove_tangent(remove_rigid(v,x),x)
    rms=np.sqrt(np.mean(np.sum(v*v,axis=1)))
    if rms<1e-15: raise ValueError('degenerate broadband probe')
    return v/rms

def kabsch_align(y,ref):
    y=np.asarray(y,float); ref=np.asarray(ref,float); yc=y-y.mean(0); rc=ref-ref.mean(0)
    H=yc.T@rc; U,S,Vt=np.linalg.svd(H); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    return yc@R

def _best_cyclic_shift(aligned,ref):
    """Best cyclic index shift after rough rigid alignment, using FFT correlation."""
    a=np.asarray(aligned,float)-np.mean(aligned,axis=0); b=np.asarray(ref,float)-np.mean(ref,axis=0)
    score=np.zeros(len(a),float)
    for d in range(3):
        # score[s] = sum_i roll(a,-s)[i] * b[i]
        score += np.fft.ifft(np.conj(np.fft.fft(a[:,d]))*np.fft.fft(b[:,d])).real
    return int(np.argmax(score))

def canonical_arclength_align(y,ref,iterations=2):
    """Geometry-only canonicalization used before POD/projection.

    1) uniformly resample the CURRENT closed curve on normalized arclength,
    2) remove arbitrary cyclic parameter-origin drift using the rotation-invariant
       radius-from-centroid signature,
    3) remove rigid translation/rotation, then refine the cyclic phase.

    This is analysis-only. It does not alter the simulated trajectory.
    """
    ref=np.asarray(ref,float); cur=resample_closed(np.asarray(y,float),len(ref)); rr=resample_closed(ref,len(ref))
    rc=rr-rr.mean(0); yc=cur-cur.mean(0)
    sr=np.linalg.norm(rc,axis=1); sy=np.linalg.norm(yc,axis=1)
    radial_score=np.fft.ifft(np.fft.fft(sy)*np.conj(np.fft.fft(sr))).real
    cur=np.roll(cur,-int(np.argmax(radial_score)),axis=0)
    for _ in range(max(1,int(iterations))):
        a=kabsch_align(cur,rr); s=_best_cyclic_shift(a,rr)
        if s==0: break
        cur=np.roll(cur,-s,axis=0)
    return kabsch_align(cur,rr)

def aligned_normal_displacement(y,ref,parameterization_invariant=True):
    rr=resample_closed(np.asarray(ref,float),len(ref))
    aligned=canonical_arclength_align(y,rr) if parameterization_invariant else kabsch_align(y,rr)
    return remove_tangent(aligned-rr,rr)

def tangential_redistribution_velocity(x,rate=2.0,method='segment_feedback'):
    """Purely tangential geometry-only mesh gauge velocity.

    segment_feedback solves a first-order discrete arclength-density controller:
        alpha[i+1]-alpha[i] = -rate * (ell[i]-mean(ell))
    and applies u_mesh[i]=alpha[i] t_hat[i].  The periodic compatibility
    condition holds because the segment-length errors sum to zero.

    target_projection is retained only as an audit/legacy gauge.
    """
    x=np.asarray(x,float); t=tangents(x); method=str(method)
    if method=='target_projection':
        target=resample_closed(x,len(x)); d=target-x
        return float(rate)*(np.sum(d*t,axis=1)[:,None]*t)
    if method!='segment_feedback': raise ValueError(f'unknown mesh_redistribution_method={method}')
    ds=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1); err=ds-float(np.mean(ds)); n=len(x)
    alpha=np.zeros(n,float)
    if n>1: alpha[1:]=-float(rate)*np.cumsum(err[:-1])
    alpha-=float(np.mean(alpha))
    return alpha[:,None]*t

def synthetic_trefoil(n=192):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]
