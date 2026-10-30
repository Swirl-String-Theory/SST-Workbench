"""Strict, unqualified trajectory adapter for external 3D Euler runs."""
from pathlib import Path
import hashlib, json
import numpy as np

def read_external(path):
    path=Path(path)
    with np.load(path, allow_pickle=False) as f:
        keys=set(f.files)
        required={'times_s','q_m','qdot_m_s','trial_ids','metadata_json'}
        if not required <= keys: raise ValueError(f'missing external keys: {sorted(required-keys)}')
        t=np.array(f['times_s'],dtype=float)
        q=np.array(f['q_m'],dtype=float); v=np.array(f['qdot_m_s'],dtype=float)
        ids=np.array(f['trial_ids'])
        meta=json.loads(str(f['metadata_json'].item()))
    if q.shape!=v.shape or q.ndim!=2 or len(t)!=q.shape[1]: raise ValueError('q and qdot must be (independent_trial,time)')
    if q.shape[0]<80 or q.shape[1]<12: raise ValueError('need >=80 independent trials and >=12 times')
    if len(set(map(str, ids)))!=len(ids): raise ValueError('duplicate independent trial ID')
    if len(ids)!=len(q): raise ValueError('trial ids do not match number of trials')
    if not np.all(np.isfinite(q)) or not np.all(np.isfinite(v)) or not np.all(np.isfinite(t)): raise ValueError('nonfinite data')
    if np.any(np.diff(t)<=0): raise ValueError('times must increase strictly')
    for k in ('solver_name','solver_revision','source_manifest_sha256','observable_definition','geometry_manifest_sha256','core_model','boundary_conditions'):
        if not meta.get(k): raise ValueError(f'provenance missing: {k}')
    k0=len(t)//2; lag=max(1,k0//3); future=max(1,(len(t)-k0-1)//2)
    d={'current':np.column_stack((q[:,k0],v[:,k0])),
       'history':np.column_stack((q[:,k0-lag],v[:,k0-lag])),
       'target':q[:,k0+future]}
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    meta.update({'file_sha256':h,'n_independent_trials':len(q),'sampling_t_s':[t[k0-lag],t[k0],t[k0+future]],
                 'status':'UNVERIFIED_EXTERNAL_PROVENANCE',
                 'required_additional_evidence':['independence and matched state audit','spatial convergence','temporal convergence','finite-core convergence','conservation and topology','two real backend parity','phase carrier qualification']})
    return d,meta
