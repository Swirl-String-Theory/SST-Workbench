from __future__ import annotations
import numpy as np
from .blind_geometry import close_curve


def component_slices(components):
    out=[]; o=0
    for c in components:
        n=len(c); out.append(slice(o,o+n)); o+=n
    return out


def flatten_components(components):
    return np.vstack([np.asarray(c,float) for c in components])


def split_state(x,sizes):
    out=[]; o=0
    for n in sizes:
        out.append(np.asarray(x[o:o+n],float)); o+=n
    return out


def tangents(curve):
    x=close_curve(curve)
    t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0)
    n=np.linalg.norm(t,axis=1); return t/np.maximum(n[:,None],1e-15)


def discrete_frame(curve):
    x=close_curve(curve); t=tangents(x)
    dt=np.roll(t,-1,axis=0)-np.roll(t,1,axis=0)
    nrm=np.linalg.norm(dt,axis=1)
    n=np.zeros_like(x)
    good=nrm>1e-9
    n[good]=dt[good]/nrm[good,None]
    # deterministic fallback normal perpendicular to tangent
    for i in np.where(~good)[0]:
        q=np.array([1.,0.,0.]) if abs(t[i,0])<0.8 else np.array([0.,1.,0.])
        q-=t[i]*np.dot(t[i],q); n[i]=q/max(np.linalg.norm(q),1e-15)
    b=np.cross(t,n); bn=np.linalg.norm(b,axis=1); b/=np.maximum(bn[:,None],1e-15)
    n=np.cross(b,t); n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
    return t,n,b


def _inner(a,b): return float(np.sum(np.asarray(a)*np.asarray(b)))


def _normalize(v):
    z=np.asarray(v,float); n=np.sqrt(_inner(z,z))
    return None if n<1e-12 else z/n


def rigid_tangent_fields(components):
    x=flatten_components(components); ctr=x.mean(0); r=x-ctr
    fields=[]; names=[]
    for j in range(3):
        f=np.zeros_like(x); f[:,j]=1.; fields.append(f); names.append(f'rigid_translation_{j}')
    axes=np.eye(3)
    for j,a in enumerate(axes):
        fields.append(np.cross(np.broadcast_to(a,r.shape),r)); names.append(f'rigid_rotation_{j}')
    sl=component_slices(components)
    for ci,c in enumerate(components):
        f=np.zeros_like(x); f[sl[ci]]=tangents(c); fields.append(f); names.append(f'tangent_{ci}')
    out=[]
    for name,f in zip(names,fields):
        q=f.copy()
        for g in out: q-=g*_inner(g,q)
        q=_normalize(q)
        if q is not None: out.append(q)
    return out


def project_out(fields, remove):
    out=[]; names=[]; fam=[]
    for name,family,f in fields:
        q=np.asarray(f,float).copy()
        for g in remove: q-=g*_inner(g,q)
        for g in out: q-=g*_inner(g,q)
        q=_normalize(q)
        if q is not None:
            out.append(q); names.append(name); fam.append(family)
    return np.asarray(out),names,fam


def build_mode_basis(components, kelvin_harmonics=(1,2), include_breathing=True, include_torsion=True):
    if len(components)!=3: raise ValueError('certification basis is preregistered for 3 components')
    comps=[close_curve(c) for c in components]; x=flatten_components(comps); sl=component_slices(comps)
    ctrs=np.array([c.mean(0) for c in comps]); cm=ctrs.mean(0)
    raw=[]
    # Three centroid-separation directions, compensated to preserve COM.
    for slot in range(3):
        d=ctrs[slot]-cm
        if np.linalg.norm(d)<1e-10: d=np.eye(3)[slot]
        d=d/np.linalg.norm(d); f=np.zeros_like(x)
        for j,s in enumerate(sl): f[s]=d*(1.0 if j==slot else -0.5)
        raw.append((f'separation_{slot}','separation',f))
    if include_breathing:
        for ci,(c,s) in enumerate(zip(comps,sl)):
            r=c-c.mean(0); f=np.zeros_like(x); f[s]=r
            raw.append((f'breathing_{ci}','breathing',f))
    if include_torsion:
        for ci,(c,s) in enumerate(zip(comps,sl)):
            t,n,b=discrete_frame(c); m=len(c)
            curv=np.linalg.norm(np.roll(t,-1,axis=0)-np.roll(t,1,axis=0),axis=1)
            center=int(np.argmax(curv)); d=np.minimum((np.arange(m)-center)%m,(center-np.arange(m))%m).astype(float)
            sigma=max(2.0,m/12.0); win=np.exp(-0.5*(d/sigma)**2); win-=win.mean()
            f=np.zeros_like(x); f[s]=win[:,None]*b
            raw.append((f'torsion_{ci}','torsion',f))
    for ci,(c,s) in enumerate(zip(comps,sl)):
        _,n,b=discrete_frame(c); m=len(c); theta=2*np.pi*np.arange(m)/m
        for k in kelvin_harmonics:
            for trig,label in ((np.cos,'c'),(np.sin,'s')):
                amp=trig(k*theta)
                fn=np.zeros_like(x); fb=np.zeros_like(x)
                fn[s]=amp[:,None]*n; fb[s]=amp[:,None]*b
                raw.append((f'kelvin_N_{ci}_k{k}_{label}','kelvin',fn))
                raw.append((f'kelvin_B_{ci}_k{k}_{label}','kelvin',fb))
    remove=rigid_tangent_fields(comps)
    B,names,families=project_out(raw,remove)
    if len(B)<6: raise RuntimeError('mode basis rank too small')
    return {'basis':B,'names':names,'families':families,'sizes':[len(c) for c in comps]}


def family_indices(mode_info,family):
    return [i for i,f in enumerate(mode_info['families']) if f==family]
