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
    x=np.asarray(x,float); y=np.vstack([x,x[0]]); ds=np.linalg.norm(np.diff(y,axis=0),axis=1); s=np.r_[0.,np.cumsum(ds)]; L=s[-1]; tgt=np.linspace(0,L,n,endpoint=False); out=np.empty((n,3))
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
    # least-squares infinitesimal translation + rotation removal
    x=np.asarray(x,float)-centroid(x); v=np.asarray(v,float); v=v-v.mean(0)
    A=[]; b=[]
    for r,u in zip(x,v):
        rx,ry,rz=r; A.extend([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]]); b.extend(u.tolist())
    A=np.asarray(A,float); b=np.asarray(b,float); om=np.linalg.lstsq(A,b,rcond=None)[0]; rot=np.cross(np.broadcast_to(om,x.shape),x)
    return v-rot

def broadband_probe(x,harmonics=(1,2,3,4)):
    x=np.asarray(x,float); n=len(x); th=2*np.pi*np.arange(n)/n; n1=radial_normal(x); t=tangents(x); n2=np.cross(t,n1); nn=np.linalg.norm(n2,axis=1); nn[nn<1e-15]=1; n2=n2/nn[:,None]
    a=np.zeros(n); b=np.zeros(n)
    for m in harmonics:
        a += np.cos(m*th+0.37*m)/(m**1.25); b += np.sin(m*th+0.61*m)/(m**1.25)
    v=a[:,None]*n1+b[:,None]*n2; v=remove_tangent(remove_rigid(v,x),x); rms=np.sqrt(np.mean(np.sum(v*v,axis=1)))
    if rms<1e-15: raise ValueError('degenerate broadband probe')
    return v/rms

def kabsch_align(y,ref):
    y=np.asarray(y,float); ref=np.asarray(ref,float); yc=y-y.mean(0); rc=ref-ref.mean(0); H=yc.T@rc; U,S,Vt=np.linalg.svd(H); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    return yc@R

def aligned_normal_displacement(y,ref): return remove_tangent(kabsch_align(y,ref)-np.asarray(ref,float),ref)

def synthetic_trefoil(n=192):
    t=np.linspace(0,2*np.pi,n,endpoint=False); return np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]
