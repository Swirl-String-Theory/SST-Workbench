"""Dimensionless, pre-registered, model-selection pipeline. Never opens reveal."""
from pathlib import Path
import numpy as np, hashlib, json, math
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'preregistration'/'SCIENCE_CONTRACT.json').read_text())
CANDIDATES=('stationary','advective_reference','inertial_reference','synthetic_isotropic_linear')
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,obj): Path(path).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
def classify(k,angles,frequency):
    f=np.asarray(frequency,float); k=np.asarray(k,float); th=np.deg2rad(np.asarray(angles,float))
    if f.shape!=(len(angles),len(k)): raise ValueError('wrong frequency grid')
    maxf=float(np.max(f)); policy=C['classifier_policy']
    if maxf<policy['stationary_max_abs_frequency']:
        return dict(label='stationary',max_omega=maxf,relative_rms=0.0,coefficient=0.0,runner_up_rel_rms=None)
    if maxf<policy['valid_nonstationary_min_max_frequency']:
        return dict(label='unknown',max_omega=maxf,relative_rms=None,coefficient=None,runner_up_rel_rms=None)
    cos=np.abs(np.cos(th))[:,None]
    g={'advective_reference':cos*k[None,:], 'inertial_reference':np.broadcast_to(cos,f.shape),'synthetic_isotropic_linear':np.broadcast_to(k[None,:],f.shape)}
    denom=np.linalg.norm(f)
    fits=[]
    for name, shape in g.items():
        coeff=max(0.,float(np.sum(shape*f)/np.sum(shape*shape)))
        rel=float(np.linalg.norm(f-coeff*shape)/denom)
        fits.append((rel,name,coeff))
    fits.sort()
    best, second=fits[0],fits[1]
    allow=best[0] <= policy['max_rel_rms_residual'] and second[0]>=policy['ambiguous_ratio']*best[0]
    return dict(label=best[1] if allow else 'unknown',max_omega=maxf,
                relative_rms=best[0],coefficient=best[2],runner_up_rel_rms=second[0],
                candidate_residuals={name:round(rel,9) for rel,name,coef in fits})
def scan_dataset(path):
    with np.load(path,allow_pickle=False) as z:
        t=np.asarray(z['t']); k=np.asarray(z['k']); angles=np.asarray(z['angles_deg']); real=np.asarray(z['real']); imag=np.asarray(z['imag'])
    if real.shape!=(len(angles),len(k),len(t)) or real.shape != imag.shape: raise ValueError('shape mismatch')
    if list(angles)!=C['angles_deg'] or list(k)!=C['k_dimensionless']: raise ValueError('preregistered grid mismatch')
    # Vectorized least-squares phase slope; no smoothing or hand-selected frequency window.
    phase=np.unwrap(np.arctan2(imag,real),axis=-1)
    centered=t-t.mean(); slope=np.sum(phase*centered[None,None,:],axis=-1)/np.sum(centered**2)
    f=np.abs(slope)
    return classify(k,angles,f),f.tolist()
def analyze():
    manifest=json.loads((ROOT/'blind'/'manifest.json').read_text())
    outputs=[]
    for item in manifest['datasets']:
        path=ROOT/'blind'/item['file']
        if digest(path)!=item['sha256']: raise RuntimeError('blind checksum failed '+item['id'])
        cl,f=scan_dataset(path)
        outputs.append({'masked_id':item['id'],'result':cl,'frequencies_dimensionless':f,'verified_sha256':item['sha256']})
    return {'status':'SYNTHETIC_REFERENCE_ONLY_NOT_PKLSA','contract_sha256':digest(ROOT/'preregistration'/'SCIENCE_CONTRACT.json'),
            'manifest_sha256':digest(ROOT/'blind'/'manifest.json'),'outputs':outputs}
def freeze_digest(result):
    return hashlib.sha256((json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
def run_blind():
    obj=analyze()
    res=ROOT/'results'/'BLIND_CLASSIFICATION.json'
    lock=ROOT/'results'/'FROZEN_SHA256.txt'
    old=lock.read_text().strip() if lock.exists() else None
    new=freeze_digest(obj)
    if old is not None and old != new: raise RuntimeError('FROZEN lock mismatch; release cannot be overwritten')
    dump(res,obj)
    if old is None: lock.write_text(new+'\n')
    return {'status':'PASS_FROZEN_BLIND_REPRODUCIBLE','dataset_count':len(obj['outputs']), 'lock_sha256':new,
            'classified':{r['masked_id']:r['result']['label'] for r in obj['outputs']}}
def verify_lock():
    want=(ROOT/'results'/'FROZEN_SHA256.txt').read_text().strip()
    actual=freeze_digest(analyze())
    assert actual==want,'frozen run not reproducible'
    assert json.loads((ROOT/'results'/'BLIND_CLASSIFICATION.json').read_text())==analyze()
    return {'status':'PASS','freeze':want}
def selftest():
    import unittest
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
