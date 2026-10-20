"""A068 v0.4.3 field-line-generated vortex-surface candidates, no topology assumption.
Integrate x'(s)=omega(x)/|omega(x)|; stitch only if closure and local tangency screens pass.
"""
from __future__ import annotations
import numpy as np
from .euler3d import L, Euler3D,load_geometry,normalized_components
from .material import sample_vector,geometry,diagnostics

def _direction(G,W,X):
    w=sample_vector(G,W,np.asarray(X))
    norm=np.linalg.norm(w,axis=-1,keepdims=True)
    if float(np.min(norm))<1e-10:raise ValueError('Vorticity singularity during field-line tracing')
    return w/norm

def integrate_line(G,W,initial,length,steps):
    h=length/steps;p=np.asarray(initial,float)
    path=[p.copy()]
    for _ in range(steps):
        k1=_direction(G,W,p);k2=_direction(G,W,p+.5*h*k1)
        k3=_direction(G,W,p+.5*h*k2);k4=_direction(G,W,p+h*k3)
        p=p+h*(k1+2*k2+2*k3+k4)/6
        path.append(p.copy())
    return np.asarray(path)

def vortex_line_seed(G,U,anchor,radius=.08,sections=64,sides=12,length=8.,closure_limit=.1):
    """Traces sides from transverse ring; no artificial endpoint closing in qualification.

    The surface array is a *diagnostic candidate* even for nonclosed lines. Report
    endpoint mismatch BEFORE artificially joining the last to first cross section.
    """
    W=G.curl(U)
    center=np.asarray(anchor,float)
    tangent=_direction(G,W,center)
    axis=np.eye(3)[np.argmin(abs(tangent))]
    normal=axis-np.dot(axis,tangent)*tangent;normal/=np.linalg.norm(normal)
    binormal=np.cross(tangent,normal)
    angles=np.arange(sides)*2*np.pi/sides
    ring=center+radius*(np.cos(angles)[:,None]*normal+np.sin(angles)[:,None]*binormal)
    lines=[];failures=[]
    for start in ring:
        try:lines.append(integrate_line(G,W,start,length,sections))
        except ValueError as exc: failures.append(str(exc));break
    if failures:return {'traced':False,'errors':failures,'vortex_tube_qualified':False}
    lines=np.stack(lines) # (sides,sections+1,3)
    delta=((lines[:,-1]-lines[:,0]+L/2)%L)-L/2
    closure=np.linalg.norm(delta,axis=1)
    candidate=lines[:,:-1].transpose(1,0,2)
    # Closing the surface for diagnostics is not an acceptable physical closure.
    detail=diagnostics(G,U,candidate,geometry(candidate)['volume_abs'])
    return {'schema':'A068-VORTEX-LINE-SEED-v0.4.3','traced':True,
            'params':{'sections':sections,'sides':sides,'length':length,'radius':radius},
            'closure_max':float(closure.max()),'closure_mean':float(closure.mean()),
            'closure_tolerance':closure_limit,'closed_line_screen_pass':bool(np.max(closure)<closure_limit),
            'candidate_tangency_mean':detail['vorticity_tangency_mean_abs_cos'],
            'candidate_tangency_max':detail['vorticity_tangency_max_abs_cos'],
            'candidate_volume':detail['volume_abs'],
            'vortex_tube_qualified':False,
            'qualification':'UNRESOLVED_NO_EMBEDDEDNESS_OR_MATERIAL_STABILITY_PROOF',
            'model_only':True}

def vortex_seed_from_curve(source,n=16,core=.4,**kwargs):
    c,_=load_geometry(source)
    G=Euler3D(n,core);normalized=normalized_components(c)[0]
    U=G.velocity_from_curve(normalized)
    return vortex_line_seed(G,U,normalized[0][0],**kwargs)
