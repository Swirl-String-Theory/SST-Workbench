from pathlib import Path
import numpy as np

EXTS={'.txt','.xyz','.csv','.dat','.pts'}

def _numeric_xyz_lines(path):
    pts=[]
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip().replace(',',' ')
        if not s or s.startswith(('#','//',';')): continue
        vals=[]
        for tok in s.split():
            try: vals.append(float(tok))
            except ValueError: pass
        if len(vals)>=3 and np.isfinite(vals[:3]).all(): pts.append(vals[:3])
    a=np.asarray(pts,dtype=float)
    if len(a)>2 and np.linalg.norm(a[0]-a[-1]) < 1e-10*max(1.0,np.ptp(a,axis=0).max()): a=a[:-1]
    if len(a)<16: raise ValueError(f"{path}: fewer than 16 XYZ points")
    return a

def discover(root):
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(root)
    out=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.suffix.lower() in EXTS:
            try:
                x=_numeric_xyz_lines(p)
                if len(x)>=16: out.append((p,x))
            except Exception: pass
    if not out: raise RuntimeError(f"No parseable closed XYZ centerlines found under {root}")
    return out

def cumulative_arclength(x):
    y=np.vstack([x,x[0]])
    ds=np.linalg.norm(np.diff(y,axis=0),axis=1)
    s=np.r_[0.0,np.cumsum(ds)]
    return s,ds

def resample_closed(x,n):
    x=np.asarray(x,float)
    s,ds=cumulative_arclength(x); L=s[-1]
    y=np.vstack([x,x[0]])
    tgt=np.linspace(0,L,n,endpoint=False)
    out=np.empty((n,3))
    for d in range(3): out[:,d]=np.interp(tgt,s,y[:,d])
    return out

def centroid_arclength(x):
    xp=np.roll(x,-1,axis=0); ds=np.linalg.norm(xp-x,axis=1); mid=.5*(x+xp)
    return (mid*ds[:,None]).sum(0)/max(ds.sum(),1e-30)

def radius_gyration(x):
    c=centroid_arclength(x); xp=np.roll(x,-1,axis=0); ds=np.linalg.norm(xp-x,axis=1); mid=.5*(x+xp)
    return float(np.sqrt((((mid-c)**2).sum(1)*ds).sum()/max(ds.sum(),1e-30)))

def normalize(x):
    x=np.asarray(x,float); c=centroid_arclength(x); x=x-c; rg=radius_gyration(x)
    if rg<=0: raise ValueError('degenerate radius of gyration')
    return x/rg,rg

def tangents(x):
    t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0)
    n=np.linalg.norm(t,axis=1); n[n==0]=1
    return t/n[:,None]

def radial_normals(x):
    c=x.mean(0); r=x-c; t=tangents(x); n=r-(r*t).sum(1)[:,None]*t
    nn=np.linalg.norm(n,axis=1)
    bad=nn<1e-12
    if bad.any():
        tt=np.roll(t,-1,axis=0)-np.roll(t,1,axis=0); n[bad]=tt[bad]; nn=np.linalg.norm(n,axis=1)
    nn[nn<1e-12]=1
    return n/nn[:,None]

def circular_distance(theta,theta0):
    return np.angle(np.exp(1j*(theta-theta0)))

def perturb(x,breathing_eps,breathing_sign,packet_eps,packet_polarity,packet_center_frac,packet_width_frac):
    x=np.asarray(x,float); c=x.mean(0)
    y=c+(1.0+breathing_eps*breathing_sign)*(x-c)
    n=radial_normals(y)
    th=2*np.pi*np.arange(len(y))/len(y); th0=2*np.pi*packet_center_frac
    d=circular_distance(th,th0); width=max(2*np.pi*packet_width_frac,1e-6)
    w=np.exp(-0.5*(d/width)**2)
    y=y+packet_eps*packet_polarity*w[:,None]*n
    return y

def synthetic_ring(n=96):
    t=np.linspace(0,2*np.pi,n,endpoint=False); return np.c_[np.cos(t),np.sin(t),np.zeros(n)]

def synthetic_trefoil(n=192):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    x=(2+np.cos(3*t))*np.cos(2*t); y=(2+np.cos(3*t))*np.sin(2*t); z=np.sin(3*t)
    return np.c_[x,y,z]
