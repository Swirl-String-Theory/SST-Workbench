from __future__ import annotations
import numpy as np
try:
    from . import _native
    HAVE_NATIVE=True
except Exception:
    _native=None;HAVE_NATIVE=False

FOUR_PI=4*np.pi

def backend_name():return 'cpp-pybind11' if HAVE_NATIVE else 'numpy-fallback'

def _vortexlab_velocity_py(points, offsets, gammas, core, delta, c0):
    p=np.asarray(points,float);o=np.asarray(offsets,np.int64);g=np.asarray(gammas,float)
    out=np.zeros_like(p)
    # Segment midpoints for nonlocal term.
    segs=[]
    for ci in range(len(o)-1):
        a,b=int(o[ci]),int(o[ci+1]);c=p[a:b];n=len(c)
        for j in range(n):
            k=(j+1)%n;dl=c[k]-c[j];m=0.5*(c[k]+c[j]);segs.append((ci,j,m,dl,g[ci]))
    for ci in range(len(o)-1):
        a,b=int(o[ci]),int(o[ci+1]);c=p[a:b];n=len(c)
        for ii in range(n):
            im=(ii-1)%n;ip=(ii+1)%n
            dm=c[ii]-c[im];dp=c[ip]-c[ii]
            lm=max(np.linalg.norm(dm),1e-14);lp=max(np.linalg.norm(dp),1e-14)
            t=(dp/lp+dm/lm);t/=max(np.linalg.norm(t),1e-14)
            ds=0.5*(lm+lp)
            kvec=(c[ip]-2*c[ii]+c[im])/max(ds*ds,1e-14)
            Lam=np.log(max(2*np.sqrt(lm*lp)/(np.exp(delta)*core),1.0000001))+c0
            u=g[ci]/FOUR_PI*Lam*np.cross(t,kvec)
            q=c[ii]
            for sj,(cj,j,m,dl,gj) in enumerate(segs):
                if cj==ci and (j==ii or j==im):continue
                r=q-m;r2=float(np.dot(r,r));soft=core*core if cj!=ci else 0.0
                den=(r2+soft)**1.5
                if den>1e-20:u += gj/FOUR_PI*np.cross(dl,r)/den
            out[a+ii]=u
    return out

def vortexlab_velocity(points, offsets, gammas, core, delta=0.615, c0=0.1395):
    p=np.asarray(points,float);o=np.asarray(offsets,np.int64);g=np.asarray(gammas,float)
    if HAVE_NATIVE:return _native.vortexlab_velocity(p,o,g,float(core),float(delta),float(c0))
    return _vortexlab_velocity_py(p,o,g,float(core),float(delta),float(c0))

def regularized_energy(points, offsets, gammas, core, rho=1.0):
    p=np.asarray(points,float);o=np.asarray(offsets,np.int64);g=np.asarray(gammas,float)
    if HAVE_NATIVE:return float(_native.regularized_energy(p,o,g,float(core),float(rho)))
    mids=[];dls=[];gs=[]
    for ci in range(len(o)-1):
        c=p[o[ci]:o[ci+1]];nxt=np.roll(c,-1,axis=0);mids.append(0.5*(c+nxt));dls.append(nxt-c);gs.append(np.full(len(c),g[ci]))
    mids=np.vstack(mids);dls=np.vstack(dls);gs=np.concatenate(gs);E=0.0
    for i0 in range(0,len(mids),128):
        m=mids[i0:i0+128];dl=dls[i0:i0+128];gg=gs[i0:i0+128]
        r=m[:,None,:]-mids[None,:,:];den=np.sqrt(np.sum(r*r,axis=2)+core*core)
        E+=np.sum((gg[:,None]*gs[None,:])*(dl@dls.T)/den)
    return float(rho*E/(8*np.pi))


def _segment_distance2(p1,q1,p2,q2):
    # Closest distance between two finite 3-D segments (Ericson-style clamp).
    u=q1-p1;v=q2-p2;w=p1-p2
    a=float(np.dot(u,u));b=float(np.dot(u,v));c=float(np.dot(v,v));d=float(np.dot(u,w));e=float(np.dot(v,w))
    eps=1e-30;D=a*c-b*b;sD=D;tD=D
    if D<eps:
        sN=0.0;sD=1.0;tN=e;tD=c
    else:
        sN=b*e-c*d;tN=a*e-b*d
        if sN<0.0:sN=0.0;tN=e;tD=c
        elif sN>sD:sN=sD;tN=e+b;tD=c
    if tN<0.0:
        tN=0.0
        if -d<0.0:sN=0.0
        elif -d>a:sN=sD
        else:sN=-d;sD=a
    elif tN>tD:
        tN=tD
        if (-d+b)<0.0:sN=0.0
        elif (-d+b)>a:sN=sD
        else:sN=(-d+b);sD=a
    sc=0.0 if abs(sN)<eps else sN/max(sD,eps)
    tc=0.0 if abs(tN)<eps else tN/max(tD,eps)
    dP=w+sc*u-tc*v
    return float(np.dot(dP,dP))

def min_nonlocal_segment_distance(points,offsets,adjacency=3):
    p=np.asarray(points,float);o=np.asarray(offsets,np.int64)
    if HAVE_NATIVE:return float(_native.min_nonlocal_segment_distance(p,o,int(adjacency)))
    comps=[p[o[i]:o[i+1]] for i in range(len(o)-1)];best=float('inf')
    for ci,a in enumerate(comps):
        na=len(a)
        for cj in range(ci,len(comps)):
            b=comps[cj];nb=len(b)
            for i in range(na):
                p1=a[i];q1=a[(i+1)%na]
                j0=i+1 if ci==cj else 0
                for j in range(j0,nb):
                    if ci==cj:
                        cyc=min(abs(i-j),na-abs(i-j))
                        if cyc<=adjacency:continue
                    d2=_segment_distance2(p1,q1,b[j],b[(j+1)%nb])
                    if d2<best:best=d2
    return float(np.sqrt(best))
