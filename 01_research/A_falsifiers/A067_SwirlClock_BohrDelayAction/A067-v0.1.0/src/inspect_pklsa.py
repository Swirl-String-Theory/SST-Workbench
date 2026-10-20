"""Fail-closed classification of real PKLSA source as dynamic evidence or geometry only."""
from __future__ import annotations
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
PINNED_STATIC_SHA='9f745ebdf546deafc7f10ffa7ecf3d86c191b1e85f405646985b3aa66e56d108'

def inspect(path:Path)->dict:
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    with np.load(path,allow_pickle=False) as z:
        arrays={k:{'shape':list(z[k].shape),'dtype':str(z[k].dtype)} for k in z.files}
        is_mesh=('vertices_m' in z.files and 'triangles' in z.files)
        eligible=('times_s' in z.files and 'velocity_ms' in z.files and z['velocity_ms'].ndim>=5 and z['velocity_ms'].shape[0]==len(z['times_s']))
    kind='DYNAMIC_SCHEMA_PRESENT_NOT_QUALIFIED' if eligible else ('STATIC_GEOMETRY_ONLY' if is_mesh else 'UNRECOGNIZED_SCHEMA')
    return {'file':path.name,'sha256':sha,'matches_pinned_static_pklsa':sha==PINNED_STATIC_SHA,
            'schema_kind':kind,'arrays':arrays,'clock_and_action_qualified':False,
            'reason':'Full time-dependent carrier, material phase, independent delay, and canonical momentum remain required.'}
if __name__=='__main__':
    import sys
    p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'inputs'/'PKLSA_STATIC_CANDIDATE_SURFACE.npz'
    v=inspect(p);print(json.dumps(v,indent=2))
