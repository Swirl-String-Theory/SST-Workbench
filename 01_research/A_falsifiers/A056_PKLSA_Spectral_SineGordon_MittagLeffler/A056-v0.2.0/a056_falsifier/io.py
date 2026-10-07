from __future__ import annotations
from pathlib import Path
import numpy as np
from .util import read_json, sha256_file
from sst_falsifier_framework.sources import validate_dynamic_metadata

def load_case(npz_path):
    p=Path(npz_path); z=np.load(p,allow_pickle=False)
    for k in ('t','s','phi'):
        if k not in z: raise ValueError(f'{p.name}: missing {k}')
    t=np.asarray(z['t'],float); s=np.asarray(z['s'],float); phi=np.asarray(z['phi'],float)
    if phi.shape != (len(t),len(s)): raise ValueError(f'{p.name}: phi shape {phi.shape} != {(len(t),len(s))}')
    rd_t=np.asarray(z['ringdown_t'],float) if 'ringdown_t' in z else None
    rd=np.asarray(z['ringdown'],float) if 'ringdown' in z else None
    meta_path=p.with_suffix('.json'); meta=read_json(meta_path) if meta_path.exists() else {}
    contract=validate_dynamic_metadata(meta,synthetic=bool(meta.get('synthetic',False)))
    return {"path":p,"sha256":sha256_file(p),"meta_sha256":sha256_file(meta_path) if meta_path.exists() else None,
            "t":t,"s":s,"phi":phi,"ringdown_t":rd_t,"ringdown":rd,"meta":meta,"contract":contract}

def discover_cases(input_dir): return [load_case(p) for p in sorted(Path(input_dir).glob('*.npz'))]
def uniformity(x):
    d=np.diff(np.asarray(x,float)); m=float(np.mean(d));
    return float(np.max(np.abs(d-m))/max(abs(m),1e-30)),m
