"""SST A068 v0.4.3: synchronous surface-mesh refinement / Cauchy deformation.

Numerical diagnostics only: non-exhaustive intersections never pass qualification.
The Euler field is evolved ONCE; meshes at 32x10,64x20,128x40 see identical RK4 stages.
"""
from __future__ import annotations
import numpy as np
from .euler3d import Euler3D, load_geometry, normalized_components
from .material import create_torus, geometry, diagnostics, sample_vector

MESHES=((32,10),(64,20),(128,40))

def _advect_bundle(G,U,meshes,probes,dt):
    """RK4 for Euler + a family of material surfaces + deformation satellites."""
    empty=np.empty((0,3,G.n,G.n,G.n))
    vectors=[m.reshape(-1,3) for m in meshes]
    shapes=[m.shape for m in meshes]
    sizes=[len(v) for v in vectors]
    all_pts=np.concatenate(vectors+[probes.reshape(-1,3)])
    def speed(state,pts): return sample_vector(G,state,pts)
    k1,_=G.rhs(U,empty); h1=speed(U,all_pts)
    k2,_=G.rhs(U+dt*k1/2,empty);h2=speed(U+dt*k1/2,all_pts+dt*h1/2)
    k3,_=G.rhs(U+dt*k2/2,empty);h3=speed(U+dt*k2/2,all_pts+dt*h2/2)
    k4,_=G.rhs(U+dt*k3,empty);h4=speed(U+dt*k3,all_pts+dt*h3)
    next_U=G.project(U+dt*(k1+2*k2+2*k3+k4)/6)
    next_pts=all_pts+dt*(h1+2*h2+2*h3+h4)/6
    splits=np.split(next_pts,np.cumsum(sizes))
    return next_U,[a.reshape(shape) for a,shape in zip(splits[:-1],shapes)],splits[-1].reshape(probes.shape)

def _shape_flags(S):
    g=geometry(S)
    area=g['triangle_areas']
    # Necessary but not sufficient for embeddedness; no false self-intersection PASS.
    finite=bool(np.all(np.isfinite(S)))
    zero=int(np.sum(area<=1e-12))
    signed=g['volume_signed']
    return {'finite_coordinates':finite,'collapsed_triangles':zero,'signed_volume':signed,
            'self_intersection_certification':'NOT_EXECUTED_REQUIRES_EXACT_TRIANGLE_TRIANGLE_OR_BVH',
            'orientation_certification':'UNRESOLVED_FOR_SELF_INTERSECTING_OR_FOLDED_MESH'}

def material_mesh_sweep(source,n=12,core=.4,dt=.04,T=.24,meshes=MESHES,probe_count=8,epsilon=1e-3):
    if T<=0 or dt<=0 or abs(round(T/dt)*dt-T)>1e-10:raise ValueError('T/dt must be integer')
    components,_=load_geometry(source)
    G=Euler3D(n,core)
    U=G.velocity_from_curve(normalized_components(components)[0])
    surfaces=[create_torus(components,sections=a,sides=b)[0] for a,b in meshes]
    volumes=[geometry(s)['volume_abs'] for s in surfaces]
    pts=surfaces[-1].reshape(-1,3)[np.linspace(0,surfaces[-1].size//3-1,probe_count,dtype=int)]
    # Satellite mapping X +/- eps e_i; det of centered finite-difference deformation gradient.
    probes=np.concatenate([pts[:,None,:], *[pts[:,None,:]+epsilon*np.eye(3)[j][None,None,:] for j in range(3)],
                           *[pts[:,None,:]-epsilon*np.eye(3)[j][None,None,:] for j in range(3)]],axis=1)
    rows=[]
    for step in range(round(T/dt)+1):
        shape=[diagnostics(G,U,S,v) for S,v in zip(surfaces,volumes)]
        F=np.stack([(probes[:,1+j]-probes[:,4+j])/(2*epsilon) for j in range(3)],axis=2)
        det=np.linalg.det(F)
        rows.append({'t':step*dt,'meshes':[{'sections':meshes[k][0],'sides':meshes[k][1],
                        'volume_drift':r['material_volume_relative_drift'],
                        'tangency_mean':r['vorticity_tangency_mean_abs_cos'],
                        'tangency_max':r['vorticity_tangency_max_abs_cos'],
                        'triangles':_shape_flags(surfaces[k])} for k,r in enumerate(shape)],
                     'det_F_max_abs_error':float(np.max(abs(det-1))),
                     'det_F_min':float(det.min()),'det_F_max':float(det.max())})
        if step<round(T/dt):U,surfaces,probes=_advect_bundle(G,U,surfaces,probes,dt)
    maxdet=max(x['det_F_max_abs_error'] for x in rows)
    maxvolume=[max(r['meshes'][j]['volume_drift'] for r in rows) for j in range(len(meshes))]
    maxmean=[max(r['meshes'][j]['tangency_mean'] for r in rows) for j in range(len(meshes))]
    delta=abs(maxvolume[-1]-maxvolume[-2])
    return {'schema':'A068-MATERIAL-REFINEMENT-v0.4.3','authority':'MODEL_DIAGNOSTIC_ONLY',
            'settings':{'grid':n,'core':core,'dt':dt,'T':T,'mesh_levels':[list(x) for x in meshes],
                        'deformation_probes':probe_count,'satellite_epsilon':epsilon},
            'max_volume_drifts':maxvolume,'max_vorticity_tangency_mean':maxmean,
            'max_det_F_error':maxdet,'finest_two_volume_drift_difference':delta,
            'volume_screen_pass':bool(maxvolume[-1]<.05),
            'detF_screen_pass':bool(maxdet<.05),
            'mesh_stability_screen_pass':bool(delta<.01),
            'embedded_surface_certified':False,
            'material_tube_qualified':False,
            'reason':'No certified embedded surface/initial vorticity-flux boundary; detF and mesh convergence are independent numerical screens',
            'history':rows}
