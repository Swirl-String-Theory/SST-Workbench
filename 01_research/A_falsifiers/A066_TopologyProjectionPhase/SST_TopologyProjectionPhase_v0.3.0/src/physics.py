"""Strict external PKLSA source validation: static geometry != physical dynamics."""
from __future__ import annotations
import json,hashlib
from pathlib import Path
import numpy as np
from .topology3d import knot_signature,link_signature,min_nonlocal_self_distance
from .euler import diagnose_velocity_grid,diagnose_vertex_transport

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def mesh_surface(path, vertices, triangles):
    from collections import deque
    import numpy as np
    V=np.asarray(vertices,dtype=float); F=np.asarray(triangles,dtype=np.int64)
    if F.ndim!=2 or F.shape[1]!=3 or not len(F) or not np.isfinite(V).all():
        raise ValueError('Invalid triangle mesh')
    if F.min()<0 or F.max()>=len(V):raise ValueError('Out-of-bounds triangle indices')
    edges=np.sort(np.concatenate((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]),axis=0),axis=1)
    unique,counts=np.unique(edges,axis=0,return_counts=True)
    # Components from surface triangle graph (not a knot's material components).
    adj=[[] for _ in range(len(V))]
    for a,b in unique:
        adj[a].append(int(b));adj[b].append(int(a))
    seen=np.zeros(len(V),dtype=bool);components=0
    for start in range(len(V)):
        if not seen[start]:
            components+=1;seen[start]=True;queue=deque([start])
            while queue:
                for nxt in adj[queue.popleft()]:
                    if not seen[nxt]:seen[nxt]=True;queue.append(nxt)
    chi=int(len(V)-len(unique)+len(F))
    closed=bool((counts==2).all())
    genus=int((2*components-chi)//2) if closed and (2*components-chi)%2==0 else None
    return {'status':'SURFACE_MESH_ONLY','source_sha256':sha(path),
        'vertices':int(len(V)),'triangles':int(len(F)),'unique_edges':int(len(unique)),
        'surface_components':int(components),'euler_characteristic':chi,
        'genus_if_orientable_and_closed':genus,'manifold_without_boundary':closed,
        'boundary_edges':int(np.sum(counts==1)),'nonmanifold_edges':int(np.sum(counts>2)),
        'coordinate_units':'source metadata (vertices_m suggests meters; numerical magnitudes unvalidated)',
        'G09_CENTERLINE_KNOT':'UNRESOLVED_NO_CENTERLINE',
        'G11_EULER':'UNRESOLVED_NO_TRAJECTORY',
        'warning':'Surface genus alone does not identify the embedded knot; never connect triangle-mesh vertices into a vortex curve.'}


def static_geometry(path):
    path=Path(path)
    with np.load(path,allow_pickle=False) as f:
        keys=list(f.files)
        if 'triangles' in f and 'vertices_m' in f:
            return mesh_surface(path,f['vertices_m'],f['triangles'])
        candidates=[]
        for name in keys:
            a=f[name]
            if a.ndim==2 and a.shape[1]==3 and np.issubdtype(a.dtype,np.number) and len(a)>=32 and np.isfinite(a).all():
                candidates.append(name)
        if not candidates:return {'status':'UNRESOLVED_NO_CURVE','available_keys':keys}
        name=next((k for k in ('points','xyz','vertices','centerline','curve','coords') if k in candidates),candidates[0])
        p=np.asarray(f[name],dtype=float)
    edges=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    return {'status':'STATIC_TOPOLOGY_DIAGNOSTIC','source_sha256':sha(path),'source_key':name,
      'point_count':int(len(p)),'polygon_length_source_units':float(edges.sum()),
      'min_nonlocal_self_separation_source_units':min_nonlocal_self_distance(p),
      'knot_signature':knot_signature(p),'G11_EULER':'UNRESOLVED_NO_TRAJECTORY',
      'G12_PHYSICAL_RECONNECT':'UNRESOLVED_NO_TRAJECTORY',
      'limitations':['Not a time series','Input coordinates may not be SI meters',
           'Alexander determinant is not a complete knot invariant',
           'No material identifiers, velocities, vorticity grid or independent PDE convergence.']}

def dynamic_data(path,metadata_path=None):
    path=Path(path)
    with np.load(path,allow_pickle=False) as f:d={k:f[k] for k in f.files}
    required=['t','filaments','present','gamma']
    if any(k not in d for k in required):return {'status':'UNRESOLVED_REQUIRED_ARRAYS','required':required,'keys':list(d)}
    t,cur,pres,gamma=[d[k] for k in required]
    if cur.ndim!=4 or cur.shape[0]!=len(t) or cur.shape[-1]!=3 or pres.shape!=cur.shape[:2] or gamma.shape!=pres.shape:
        return {'status':'FAIL_SHAPE_CONTRACT'}
    if not np.all(np.diff(t)>0):return {'status':'FAIL_TIME_ORDER'}
    meta=json.loads(Path(metadata_path).read_text()) if metadata_path else {}
    unit_check=(meta.get('spatial_units')=='m' and meta.get('time_units')=='s' and meta.get('circulation_units')=='m^2/s')
    idx=[0,len(t)//2,len(t)-1]
    frames=[]
    for i in idx:
        frame=link_signature(cur[i],pres[i],gamma[i])
        frame.update({'frame_index':i,'time_input_units':float(t[i])})
        frames.append(frame)
    result={'status':'EXTERNAL_TIME_SERIES_DIAGNOSTIC','source_sha256':sha(path),
       'units_qualified':unit_check,'frames':frames,
       'G09_ALEXANDER_AND_LINK':'QUALIFIED_GEOMETRY' if all(all(k['status']=='QUALIFIED' for k in frame['knots']) and all(k['status']=='QUALIFIED' for k in frame['links']) for frame in frames) else 'UNRESOLVED',
       'G10_KELVIN_COMPONENTS':'UNRESOLVED_NO_MATERIAL_IDS',
       'G11_EULER':'UNRESOLVED_NO_VELOCITY_FIELD',
       'G12_PHYSICAL_RECONNECT':'UNRESOLVED','G13_SPATIOTEMPORAL_CONVERGENCE':'UNRESOLVED',
       'G14_INDEPENDENT_PROVIDER':'UNRESOLVED','G15_SI_UNITS':'PASS' if unit_check else 'UNRESOLVED',
       'warning':'Geometric topology and Euler dynamics are different certification layers.'}
    if 'material_ids' in d:
        mids=np.asarray(d['material_ids']).astype(str).tolist()
        if len(set(mids))==len(mids) and len(mids)==pres.shape[1]:
            stable=True;changes=[]
            for j in range(pres.shape[1]):
                active=np.flatnonzero(pres[:,j])
                if len(active)>1:
                    ga=gamma[active,j]
                    changes.append(float(np.max(np.abs(ga-ga[0]))/max(abs(ga[0]),1e-30)))
            result['gamma_material_max_relative_change']=max(changes) if changes else None
            result['G10_KELVIN_COMPONENTS']='PASS_SCREEN_ONLY' if changes and max(changes)<1e-8 else 'UNRESOLVED_OR_FAILED'
    if 'u_vertices' in d:
        result['vertex_transport']=diagnose_vertex_transport(t,cur,pres,d['u_vertices'],d.get('material_ids'))
    fields=['x_m','y_m','z_m','u_grid']
    if all(k in d for k in fields) and unit_check:
        result['euler_grid']=diagnose_velocity_grid(t,d['x_m'],d['y_m'],d['z_m'],d['u_grid'])
        result['G11_EULER']='PASS_SCREEN_ONLY' if result['euler_grid']['pass_screen'] else 'FAIL_RESIDUAL_SCREEN'
    result['source_metadata']=meta
    return result
