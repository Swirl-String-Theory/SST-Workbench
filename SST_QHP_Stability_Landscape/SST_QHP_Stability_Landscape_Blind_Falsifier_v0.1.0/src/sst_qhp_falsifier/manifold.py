import numpy as np
from .geometry import normal_component
AXES=('q','h','p')

def group_key(r,axis,tol_digits=12):
    return tuple(round(float(r[a]),tol_digits) for a in AXES if a!=axis)

def build_neighbors(rows):
    neighbors={i:{} for i in range(len(rows))}
    for axis in AXES:
        groups={}
        for i,r in enumerate(rows): groups.setdefault((r['family_blind'],r.get('replicate','0'),group_key(r,axis)),[]).append((float(r[axis]),i))
        for _,vals in groups.items():
            vals=sorted(vals)
            for k,(v,i) in enumerate(vals):
                if k>0: neighbors[i].setdefault(axis,{})['minus']=vals[k-1][1]
                if k+1<len(vals): neighbors[i].setdefault(axis,{})['plus']=vals[k+1][1]
    return neighbors

def tangent_for(i,axis,rows,X,neighbors):
    nb=neighbors[i].get(axis,{})
    if 'minus' in nb and 'plus' in nb:
        im,ip=nb['minus'],nb['plus']; d=float(rows[ip][axis])-float(rows[im][axis]); T=(X[ip]-X[im])/d if abs(d)>1e-15 else None; scheme='central'
    elif 'plus' in nb:
        ip=nb['plus']; d=float(rows[ip][axis])-float(rows[i][axis]); T=(X[ip]-X[i])/d if abs(d)>1e-15 else None; scheme='forward'
    elif 'minus' in nb:
        im=nb['minus']; d=float(rows[i][axis])-float(rows[im][axis]); T=(X[i]-X[im])/d if abs(d)>1e-15 else None; scheme='backward'
    else: T=None; scheme='none'
    if T is None: return None,scheme
    # QHP tangent must represent geometry change, not bead reparameterization.
    T=normal_component(T,X[i]); den=float(np.sum(T*T));
    if den<1e-16: return None,'degenerate'
    return T,scheme

def project_field(U,T):
    if T is None: return np.nan
    return float(np.sum(U*T)/np.sum(T*T))

def gram_projection(U,tangents):
    active=[a for a,T in tangents.items() if T is not None]
    if not active: return {},np.nan
    A=np.array([[np.sum(tangents[a]*tangents[b]) for b in active] for a in active],float)
    b=np.array([np.sum(tangents[a]*U) for a in active],float)
    coef=np.linalg.lstsq(A,b,rcond=1e-10)[0]
    recon=sum(c*tangents[a] for c,a in zip(coef,active)); frac=float(np.sum(recon*recon)/max(np.sum(U*U),1e-30))
    return dict(zip(active,map(float,coef))),frac
