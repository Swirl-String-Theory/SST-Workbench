from __future__ import annotations
import numpy as np


def load_xyz(path):
    pts=[]
    with open(path,'r',encoding='utf-8',errors='replace') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('#'): continue
            a=s.replace(',',' ').split()
            if len(a)<3: continue
            try: pts.append([float(a[0]),float(a[1]),float(a[2])])
            except ValueError: continue
    x=np.asarray(pts,float)
    if x.ndim!=2 or x.shape[0]<8 or x.shape[1]!=3:
        raise ValueError(f"Need >=8 XYZ rows: {path}")
    if np.linalg.norm(x[0]-x[-1]) < 1e-12:
        x=x[:-1]
    return x


def save_xyz(path,x):
    np.savetxt(path,np.asarray(x,float),fmt='%.17g')


def arclength_resample_closed(x,n):
    x=np.asarray(x,float)
    y=np.vstack([x,x[0]])
    ds=np.linalg.norm(np.diff(y,axis=0),axis=1)
    s=np.concatenate([[0.0],np.cumsum(ds)])
    L=s[-1]
    if not np.isfinite(L) or L<=0: raise ValueError('degenerate curve')
    st=np.linspace(0,L,n+1)[:-1]
    out=np.empty((n,3),float)
    for k,t in enumerate(st):
        i=min(np.searchsorted(s,t,side='right')-1,len(x)-1)
        u=(t-s[i])/max(ds[i],1e-30)
        out[k]=(1-u)*y[i]+u*y[i+1]
    return out


def center_rg(x):
    x=np.asarray(x,float)
    c=x.mean(axis=0); y=x-c
    rg=float(np.sqrt(np.mean(np.sum(y*y,axis=1))))
    return y,c,rg


def unit_tangents(x):
    d=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0)
    n=np.linalg.norm(d,axis=1)
    return d/np.maximum(n[:,None],1e-30)


def normal_project(v,t):
    return v-np.sum(v*t,axis=1)[:,None]*t


def remove_rigid(v,x):
    """Remove translation and infinitesimal rigid rotation from displacement field."""
    v=np.asarray(v,float).copy(); x=np.asarray(x,float)
    v-=v.mean(axis=0)
    # least-squares omega for v ~= omega x x
    A=[]; b=[]
    for r,w in zip(x,v):
        rx=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]],float)
        # omega x r = - r x omega
        A.append(-rx); b.append(w)
    A=np.vstack(A); b=np.concatenate(b)
    omega,*_=np.linalg.lstsq(A,b,rcond=None)
    v-=np.cross(np.broadcast_to(omega,x.shape),x)
    return v


def normalize_basis(v,rg):
    rms=float(np.sqrt(np.mean(np.sum(v*v,axis=1))))
    if rms < 1e-12*max(rg,1.0):
        raise ValueError('degenerate QHP basis')
    return v*(rg/rms)


def principal_frame(x):
    C=(x.T@x)/len(x)
    vals,vecs=np.linalg.eigh(C)
    order=np.argsort(vals)[::-1]
    return vals[order],vecs[:,order]


def qhp_bases(seed):
    """Return seed-centered Q,H,P basis fields, each RMS-normalized to Rg.

    Q: outward normal-plane breathing relative to centroid.
    H: traceless axial flatten/elongation along the smallest-variance PCA axis.
    P: periodic phase/shear: local azimuthal displacement about the PCA axis,
       modulated by one arclength harmonic to prevent it being a rigid rotation.
    """
    x,c,rg=center_rg(seed)
    t=unit_tangents(x)
    vals,E=principal_frame(x)
    e1,e2,e3=E[:,0],E[:,1],E[:,2]

    # Q: centroid-radial, stripped of tangent and rigid components.
    q=normal_project(x,t)
    q=remove_rigid(q,x)
    q=normal_project(q,t)

    # H: traceless axial deformation along e3 vs transverse plane.
    z=x@e3
    rperp=x-z[:,None]*e3
    h=z[:,None]*e3-0.5*rperp
    h=normal_project(h,t); h=remove_rigid(h,x); h=normal_project(h,t)

    # P: azimuthal phase/shear around e3, modulated around arclength.
    n=len(x)
    phase=2*np.pi*np.arange(n)/n
    az=np.cross(np.broadcast_to(e3,x.shape),rperp)
    p=np.sin(phase)[:,None]*az
    p=normal_project(p,t); p=remove_rigid(p,x); p=normal_project(p,t)

    return {
        'center':c,'rg':rg,'pca_values':vals,'pca_axes':E,
        'Q':normalize_basis(q,rg),
        'H':normalize_basis(h,rg),
        'P':normalize_basis(p,rg),
        'seed_centered':x,
    }


def apply_qhp(seed,q=0.0,h=0.0,p=0.0):
    B=qhp_bases(seed)
    x=B['seed_centered'] + q*B['Q'] + h*B['H'] + p*B['P']
    # keep seed centroid exactly; do not rescale shape
    x+=B['center']
    return x,B


def min_nonlocal_vertex_distance(x,skip=3):
    x=np.asarray(x,float); n=len(x); best=np.inf
    for i in range(n):
        d=np.linalg.norm(x-x[i],axis=1)
        idx=np.arange(n)
        sep=np.minimum((idx-i)%n,(i-idx)%n)
        mask=sep>skip
        if np.any(mask): best=min(best,float(np.min(d[mask])))
    return best


def metrics(x):
    y,c,rg=center_rg(x)
    seg=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    return {
        'n':int(len(x)), 'rg':rg, 'length':float(seg.sum()),
        'ds_cv':float(seg.std()/max(seg.mean(),1e-30)),
        'min_nonlocal_vertex_distance':min_nonlocal_vertex_distance(x),
    }
