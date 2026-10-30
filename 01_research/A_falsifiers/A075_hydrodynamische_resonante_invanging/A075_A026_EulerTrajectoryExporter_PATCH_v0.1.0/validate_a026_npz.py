#!/usr/bin/env python3
"""Pure format check matching the A026 HSM v0.1.0 input schema.
Not independent source, solver, or scientific validation.
"""
import json, sys
from pathlib import Path
import numpy as np

def validate(path):
    p=Path(path)
    with np.load(p,allow_pickle=False) as f:
        required={'times_s','q_m','qdot_m_s','trial_ids','metadata_json'}
        assert required.issubset(f.files), f'missing keys: {required-set(f.files)}'
        t=f['times_s'];q=f['q_m'];v=f['qdot_m_s'];ids=f['trial_ids']
        meta=json.loads(f['metadata_json'].item())
    assert q.ndim==2 and q.shape==v.shape and q.shape[1]==len(t)
    assert q.shape[0]>=80 and q.shape[1]>=12, 'A026 intake requires >=80 independent trials and >=12 samples'
    assert ids.shape==(q.shape[0],) and len(set(map(str,ids)))==len(ids)
    assert np.isfinite(q).all() and np.isfinite(v).all() and np.isfinite(t).all()
    assert np.all(np.diff(t)>0)
    for k in ('solver_name','solver_revision','source_manifest_sha256','geometry_manifest_sha256','observable_definition','core_model','boundary_conditions'):
        assert meta.get(k),f'missing provenance {k}'
    # A026 v0.1.0 analyzer currently rejects features whose absolute std is <1e-14.
    # Check against the actual sampling indices; this is a numeric/software limitation.
    k0=len(t)//2;lag=max(1,k0//3)
    for idx in (k0,k0-lag):
        for a,name in ((q,'q'),(v,'qdot')):
            stdev=float(np.std(a[:,idx],ddof=0))
            assert stdev>=1e-14, f'A026 analyzer degeneracy cutoff: std({name} at sample {idx}) = {stdev:g} < 1e-14. Use calibrated feature scaling or a reviewed A026 analysis patch.'
    return {'n_trials':len(q),'n_samples':len(t),'sampled_t_s':[float(t[k0-lag]),float(t[k0])],
            'model':meta['solver_name'],'physics_status':meta.get('physics_status','NOT_DECLARED'),
            'format':'PASS_NOT_PHYSICS_CERTIFICATION'}

if __name__=='__main__':
    try:print(json.dumps(validate(sys.argv[1]),indent=2))
    except Exception as ex:print('FORMAT_REFUSED:',str(ex),file=sys.stderr);sys.exit(2)
