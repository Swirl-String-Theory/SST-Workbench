"""Fail-closed external PKLSA geometry importer. Static geometry != dynamic qualification."""
import numpy as np
from pathlib import Path
import hashlib

def inspect(path):
    path=Path(path);d=np.load(path,allow_pickle=False)
    names=list(d.files)
    aliases=['points','xyz','vertices','centerline','curve','coords']
    candidates=[]
    for k in names:
        a=d[k]
        if a.ndim==2 and a.shape[-1]==3 and np.issubdtype(a.dtype,np.number) and np.isfinite(a).all():candidates.append(k)
    if not candidates:return {'status':'UNRESOLVED','reason':'No finite Nx3 curve found','keys':names}
    k=next((a for a in aliases if a in candidates),candidates[0]);a=d[k].astype(float)
    if len(a)<32:return {'status':'FAIL','reason':'<32 points'}
    edges=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
    return {'status':'STATIC_GEOMETRY_ONLY', 'sha256_file':hashlib.sha256(path.read_bytes()).hexdigest(),
      'array_key':k,'N':len(a),'length_geometry_units':float(edges.sum()),
      'min_segment':float(edges.min()),'max_segment':float(edges.max()),
      'dynamic_reconnection_gate':'UNRESOLVED','Euler_gate':'UNRESOLVED',
      'independent_provider_qualification':'UNRESOLVED',
      'warning':'Geometry alone does not establish trajectories, material identity, vortex core or 3D reconnection.'}
