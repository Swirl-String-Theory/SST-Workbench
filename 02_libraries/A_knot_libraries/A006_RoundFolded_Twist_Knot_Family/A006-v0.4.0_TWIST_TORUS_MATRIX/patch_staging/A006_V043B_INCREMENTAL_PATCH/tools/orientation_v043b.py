#!/usr/bin/env python3
"""A006 v0.4.3b: orientation of already-placed WHOLE Borromean components.

In-plane rigid rotations preserve each isolated knot's type and cyclic length.
They do NOT automatically preserve the mutual linking/isotopy of a 3-component link.
CENTER is a numerical design heuristic, not a Milnor classification.
"""
from __future__ import annotations
import hashlib
import itertools
import math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

SAFE_CENTRE_DISTANCE = 0.20

def orientation_key(policy,angles):
    policy=policy.upper()
    if policy not in ('LEGACY','CENTER','MANUAL'):
        raise ValueError('Unknown closure policy')
    if policy=='MANUAL':
        tokens=['m' if a<0 else 'p' for a in angles]
        enc='_'.join(t+str(int(round(abs(a)*1000))) for t,a in zip(tokens,angles))
        return 'CPMANUAL_'+enc
    return 'CP'+policy

def principal_frame(p):
    p=np.asarray(p,float)
    c=p.mean(axis=0)
    _,_,vt=np.linalg.svd(p-c,full_matrices=False)
    n=vt[-1]
    n=n/np.linalg.norm(n)
    return c,n

def rotate_about_normal(p,centre,normal,degrees):
    """Rotate all of a whole component around its fitted ring-plane normal."""
    t=math.radians(float(degrees));a=np.asarray(p)-centre
    return centre + a*math.cos(t) + np.cross(normal,a)*math.sin(t) + np.outer(a@normal,normal)*(1-math.cos(t))

def clasp_marker(p):
    """Deterministic geometric proxy: max locally smoothed polygonal curvature.

    Cannot independently identify a topological clasp: that remains unverified.
    """
    a=np.roll(p,1,axis=0)-p;b=np.roll(p,-1,axis=0)-p
    la=np.linalg.norm(a,axis=1);lb=np.linalg.norm(b,axis=1)
    theta=np.arccos(np.clip(np.einsum('ij,ij->i',a,b)/(la*lb),-1,1))
    k=(np.pi-theta)/(0.5*(la+lb))
    width=max(3,round(len(p)*0.007))
    if width%2==0:width+=1
    sm=sum(np.roll(k,j,axis=0) for j in range(-(width//2),width//2+1))/width
    at=int(np.argmax(sm))
    return at,np.asarray(p[at]),float(sm[at])

def coarse_pair_distance(a,b):
    stridea=max(1,len(a)//512);strideb=max(1,len(b)//512)
    return float(np.min(cKDTree(b[::strideb]).query(a[::stridea],k=1)[0]))

def validate_link(parts,root):
    """Return static clearance and coarse pairwise Gauss linking; NOT mu123."""
    import sys
    sys.path.insert(0,str(Path(root)/'extensions'/'borromean'/'whole'))
    from build_whole import clearance,gauss
    selfdist=[float(clearance(p,skip=max(8,int(len(p)/128)))) for p in parts]
    inter=[float(clearance(parts[i],parts[j])) for i,j in ((0,1),(0,2),(1,2))]
    gauss_values=[float(gauss(parts[i][::max(1,len(parts[i])//256)],
                              parts[j][::max(1,len(parts[j])//256)])) for i,j in ((0,1),(0,2),(1,2))]
    ok=(np.isfinite(selfdist+inter+gauss_values).all() and
        min(selfdist)>SAFE_CENTRE_DISTANCE and min(inter)>SAFE_CENTRE_DISTANCE and
        max(map(abs,gauss_values))<0.02)
    return bool(ok),{'min_self_clearance':min(selfdist),'min_intercomponent_clearance':min(inter),
                       'pairwise_gauss_approx':gauss_values}

def orient_components(parts,policy='CENTER',manual_angles=(0.,0.,180.),root=None,knots=None):
    if len(parts)!=3:raise ValueError('Exactly three separate components required')
    if root is None:raise ValueError('Root is required to validate link geometry')
    parts=[np.asarray(p,float) for p in parts]
    frames=[principal_frame(p) for p in parts]
    global_centre=np.mean([c for c,n in frames],axis=0)
    marks=[clasp_marker(p) for p in parts]
    angles=tuple(map(float,manual_angles))
    if len(angles)!=3 or not all(map(math.isfinite,angles)):
        raise ValueError('Manual angles must be three finite degrees')
    policy=policy.upper()
    if policy=='LEGACY':candidates=[(0.,0.,0.)]
    elif policy=='MANUAL':candidates=[angles]
    elif policy=='CENTER':
        if knots is None or len(knots)!=3:raise ValueError('CENTER requires three component knot labels')
        # Preserve the already satisfactory 5_2 phases. Only the 6_1 orientation
        # is searched in 0/180 steps; the user observed its clasp facing outwards.
        candidates=list(itertools.product(*[((0.,180.) if k=='6_1' else (0.,)) for k in knots]))
    else:raise ValueError('Unsupported policy: '+policy)
    def score(angs):
        pts=[rotate_about_normal(mark[1][None,:],c,n,a)[0]
             for (c,n),mark,a in zip(frames,marks,angs)]
        radii=[max(1e-12,np.median(np.linalg.norm(p-c,axis=1)))
               for (c,n),p in zip(frames,parts)]
        return float(sum((np.linalg.norm(t-global_centre)/r)**2 for t,r in zip(pts,radii)))
    scores=sorted([(score(v),v) for v in candidates],key=lambda x:(x[0],x[1]))
    tested=[]
    for value,trial in scores:
        trial_parts=[rotate_about_normal(p,c,n,a) for p,(c,n),a in zip(parts,frames,trial)]
        # Isolated component edge length is invariant under rigid rotation.
        for before,after in zip(parts,trial_parts):
            b=np.linalg.norm(np.roll(before,-1,axis=0)-before,axis=1)
            a=np.linalg.norm(np.roll(after,-1,axis=0)-after,axis=1)
            if not np.allclose(a,b,atol=1e-9,rtol=1e-9):raise RuntimeError('Rotation altered component geometry')
        valid,met=validate_link(trial_parts,root)
        tested.append({'angles_deg':list(trial),'centre_proxy_score':value,'accepted':valid,'gates':met})
        if valid:
            return trial_parts,{'policy':policy,'angles_deg':list(trial),'manual_angles_requested':list(angles),
                                'selected_score':value,'tested_candidates':tested,
                                'landmark_method':'maximum smoothed discrete curvature (geometric proxy only)',
                                'landmark_indices':[m[0] for m in marks],
                                'rotation':'rigid in-plane about fitted whole-component plane normal',
                                'component_knot_labels':list(knots) if knots is not None else None,
                                'individual_component_topology':'UNCHANGED_BY_RIGID_ROTATION',
                                'full_link_isotopy':'UNRESOLVED','Milnor_mu123':'UNRESOLVED'}
    raise RuntimeError('No orientation candidate passes intercomponent clearance and pairwise linking; '
                       'refusing to create misleading Borromean geometry. '+repr(tested))
