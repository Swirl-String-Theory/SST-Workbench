"""v0.4.4 long-horizon, multi-resolution Lagrangian material-volume audit.

This is a numerical diagnostic, not a topological proof of embeddedness or a
source-native vortex tube. All mesh levels share precisely the same Euler RK4
sub-stages and remain independent of the 'primary' Euler conservation branch.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree
from .euler3d import Euler3D,load_geometry,normalized_components
from .material import create_torus,geometry,diagnostics
from .mesh_refinement import _advect_bundle

LEVELS=((32,10),(64,20),(128,40))

def surface_quality_screen(s, probes=256, relative_tolerance=1e-9):
    """An independent mesh *screen*, NOT exact triangle-intersection certification.

    Uses sampled non-adjacent bounding spheres, so it can only flag candidate
    collisions. A negative screen cannot prove global embeddedness.
    """
    g=geometry(s); m,k,_=s.shape
    vertices=s.reshape(-1,3)
    ids=np.arange(m*k).reshape(m,k)
    # Same triangle connectivity/order as material.geometry(), including seam.
    a=ids; b=np.roll(ids,-1,axis=0); c=np.roll(ids,-1,axis=1)
    d=np.roll(b,-1,axis=1)
    tri=np.concatenate([np.stack([a,b,c],axis=-1).reshape(-1,3),
                        np.stack([b,d,c],axis=-1).reshape(-1,3)],axis=0)
    verts=vertices[tri]; cent=np.mean(verts,axis=1)
    rad=np.max(np.linalg.norm(verts-cent[:,None],axis=2),axis=1)
    area=g['triangle_areas']
    finite=bool(np.all(np.isfinite(s)) and np.all(np.isfinite(area)))
    scale=max(float(np.max(rad)),1e-15)
    degenerate=int(np.sum(area<=relative_tolerance*scale**2))
    # Sampled collision broadphase cannot rule out unsampled or interpenetrating
    # triangles; ignores direct vertex-sharing neighbors by topology.
    pick=np.unique(np.linspace(0,len(tri)-1,min(probes,len(tri)),dtype=int))
    tree=cKDTree(cent)
    potential=0
    for i in pick:
        neighbors=tree.query_ball_point(cent[i],r=float(rad[i]+np.max(rad)))
        vi=set(map(int,tri[i]))
        for j in neighbors:
            if j==i or vi.intersection(map(int,tri[j])):continue
            if np.linalg.norm(cent[i]-cent[j]) <= rad[i]+rad[j]:potential+=1
    return {'finite':finite,'degenerate_triangle_count':degenerate,
            'sampled_broadphase_potential_pairs':int(potential),
            'sampled_triangle_count':int(len(pick)), 'total_triangle_count':int(len(tri)),
            'signed_volume':float(g['volume_signed']),
            'surface_embeddedness':'UNRESOLVED_NOT_EXHAUSTIVE_OR_EXACT',
            'collision_candidate_detection':'NUMERICAL_BROADPHASE_ONLY'}

def long_material_campaign(source,*,n=16,core=.4,dt=.04,T=20.,
                           mesh_levels=LEVELS,output_every=25,
                           probe_count=12,epsilon=1e-3,quality_probes=96):
    if n<8 or dt<=0 or T<=0 or output_every<1 or epsilon<=0:raise ValueError('Invalid campaign parameters')
    steps=round(T/dt)
    if abs(steps*dt-T)>1e-10:raise ValueError('T must be integer multiple of dt')
    geom,_=load_geometry(source)
    G=Euler3D(n,core); U=G.velocity_from_curve(normalized_components(geom)[0])
    surfaces=[create_torus(geom,sections=a,sides=b)[0] for a,b in mesh_levels]
    volume0=[geometry(x)['volume_abs'] for x in surfaces]
    points=surfaces[-1].reshape(-1,3)[np.linspace(0,len(surfaces[-1].reshape(-1,3))-1,probe_count,dtype=int)]
    eye=np.eye(3)*epsilon
    probes=np.stack([points,*(points+v for v in eye),*(points-v for v in eye)],axis=1)
    measurements=[]; previous_orientation=None; defects=[]
    for step in range(steps+1):
        if step%output_every==0 or step==steps:
            finite=bool(np.all(np.isfinite(U)) and all(np.all(np.isfinite(s)) for s in surfaces))
            if not finite:
                defects.append({'step':step,'reason':'NONFINITE_STATE'});break
            sampled=[]
            for j,s in enumerate(surfaces):
                g=diagnostics(G,U,s,volume0[j])
                sampled.append({'mesh':list(mesh_levels[j]),'material_volume_drift':g['material_volume_relative_drift'],
                     'tangency_mean':g['vorticity_tangency_mean_abs_cos'],
                     'tangency_max':g['vorticity_tangency_max_abs_cos'],
                     'signed_volume':geometry(s)['volume_signed'], 'surface_area':g['area']})
            F=np.stack([(probes[:,j+1]-probes[:,j+4])/(2*epsilon) for j in range(3)],axis=2)
            det=np.linalg.det(F)
            signed=np.array([x['signed_volume'] for x in sampled])
            orientation=np.sign(signed)
            if previous_orientation is None:previous_orientation=orientation.copy()
            if np.any(orientation != previous_orientation): defects.append({'step':step,'reason':'SIGNED_VOLUME_ORIENTATION_REVERSAL'})
            # expensive quality tests at initial/final only; NEVER claim all-step assurance
            quality=surface_quality_screen(surfaces[-1],probes=quality_probes) if step in (0,steps) else None
            measurements.append({'t':float(step*dt),'mesh':sampled,
                   'detF_min':float(np.min(det)), 'detF_max':float(np.max(det)),
                   'detF_max_abs_error':float(np.max(abs(det-1))),
                   'finest_mesh_quality':quality})
        if step<steps:U,surfaces,probes=_advect_bundle(G,U,surfaces,probes,dt)
    if not measurements:raise RuntimeError('No material measurements retained')
    max_volume=[max(r['mesh'][j]['material_volume_drift'] for r in measurements) for j in range(len(mesh_levels))]
    max_tangency=[max(r['mesh'][j]['tangency_mean'] for r in measurements) for j in range(len(mesh_levels))]
    delta=max(abs(r['mesh'][-1]['material_volume_drift']-r['mesh'][-2]['material_volume_drift']) for r in measurements)
    detmax=max(r['detF_max_abs_error'] for r in measurements)
    return {'schema':'A068-LONG-MATERIAL-TUBE-v0.4.4','authority':'DIAGNOSTIC_ONLY',
        'mesh_levels':[list(x) for x in mesh_levels], 'n':n,'dt':dt,'T_requested':T,
        'T_reached':measurements[-1]['t'], 'snapshot_every_steps':output_every,
        'sampled_snapshots':len(measurements),'not_continuously_monitored':output_every>1,
        'max_volume_drifts':max_volume,'max_tangency_mean':max_tangency,
        'max_detF_error':detmax,'finest_two_mesh_volume_delta_max':float(delta),
        'volume_screen_pass':bool(max_volume[-1]<.05),
        'detF_screen_pass':bool(detmax<.05),
        'mesh_agreement_screen_pass':bool(delta<.01),
        'surface_embeddedness_certified':False,'vortex_tube_qualified':False,
        'qualification':'UNRESOLVED_MESH_INTERSECTION_AND_SOURCE_PHYSICS',
        'defects':defects,'history':measurements}
