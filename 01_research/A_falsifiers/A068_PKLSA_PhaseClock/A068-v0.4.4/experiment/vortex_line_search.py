"""Registered multi-anchor return-map diagnostic for the *Euler vorticity field*.

Candidate ranking by closure is exploratory and must never count as independent
physical inference (selection on the same source).
"""
from __future__ import annotations
import numpy as np
from .euler3d import L,Euler3D,load_geometry,normalized_components
from .vortex_seed import integrate_line,vortex_line_seed

def closure_search(source,*,n=12,core=.4,anchor_indices=(0,12,24),
                   lengths=(4.,8.,12.),steps=64,radius=.08,sides=8):
    original,_=load_geometry(source);G=Euler3D(n,core)
    c=normalized_components(original)[0][0]
    U=G.velocity_from_curve(normalized_components(original)[0]);W=G.curl(U)
    trials=[]
    for ix in anchor_indices:
        anchor=c[int(ix)%len(c)]
        for length in lengths:
            try:
                curve=integrate_line(G,W,anchor,float(length),int(steps))
                delta=((curve[-1]-curve[0]+L/2)%L)-L/2
                residual=float(np.linalg.norm(delta))
                trials.append({'seed_index':int(ix),'length':float(length),'closure_distance':residual,
                               'finite':bool(np.all(np.isfinite(curve)))})
            except (ValueError,FloatingPointError) as exc:
                trials.append({'seed_index':int(ix),'length':float(length),'error':str(exc),'finite':False})
    finite=[t for t in trials if t['finite']]
    best=min(finite,key=lambda x:x['closure_distance']) if finite else None
    # No arbitrary closure stitching, no attempt to upgrade topology from one closed line.
    return {'schema':'A068-VORTEX-RETURN-MAP-v0.4.4', 'authority':'EXPLORATORY_ONLY',
            'trials':trials,'best':best,'vortex_tube_qualified':False,
            'independent_source_count':0,
            'selection_bias_warning':'Candidate selected using same Euler realization, requires withheld validation'}
