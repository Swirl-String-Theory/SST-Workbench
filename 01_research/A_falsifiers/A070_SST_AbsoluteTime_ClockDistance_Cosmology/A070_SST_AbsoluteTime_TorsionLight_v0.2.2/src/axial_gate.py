"""A070 v0.2.2 axial-only synthetic reference. Does not contain reveal truth."""
from pathlib import Path
import json, hashlib, numpy as np
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'preregistration'/'AXIAL_SCIENCE_CONTRACT.json').read_text())

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inertial_omega_group(kvec,Omega=1.):
    kvec=np.asarray(kvec,float)
    km=float(np.linalg.norm(kvec))
    if km<=0: raise ValueError('zero wavevector')
    ez=np.array([0.,0.,1.])
    return 2*Omega*kvec[2]/km,2*Omega*(ez/km-kvec[2]*kvec/km**3)

def axial_null_phase(z,t,k,U=0.):
    """Exact scalar azimuthal advective-null control (background swirl=0)."""
    z=np.asarray(z,float)
    t=np.asarray(t,float)
    return np.exp(1j*k*(z[None,:]-U*t[:,None]))

def check_axial(kvec):
    v=np.asarray(kvec,float)
    return np.linalg.norm(v[:2])<=1.e-12*np.linalg.norm(v) and v[2]!=0.

def estimate_time_phase(series,t):
    # shape (k, time), at a fixed axial point; signed frequency
    p=np.unwrap(np.angle(series),axis=1)
    tc=t-t.mean()
    return -np.sum(p*tc[None,:],axis=1)/np.sum(tc**2)

def classify(wavenumbers,frequency,U):
    k=np.asarray(wavenumbers,float); f=np.asarray(frequency,float)
    if len(k)!=4 or np.any(k<=0) or len(f)!=len(k): raise ValueError('invalid grid')
    eps=C['masked_synthetic']['classification']
    vlab=f/k; vi=vlab-U
    spread=np.std(vi)/(max(abs(np.mean(vi)),1.e-12))
    if np.max(np.abs(vlab))<eps['static_max_lab_speed']:
        mode='stationary'
    elif np.max(np.abs(vi))<eps['advection_max_intrinsic_speed']:
        mode='passive_advection'
    elif abs(np.mean(vi))>=eps['wave_min_intrinsic_speed'] and spread < eps['max_k_dependent_speed_cv']:
        mode='propagation_signature_unqualified'
    else:
        mode='unknown'
    return {'classification':mode,'background_speed':float(U),'mean_lab_phase_speed':float(np.mean(vlab)),
            'mean_intrinsic_phase_speed':float(np.mean(vi)),'k_speed_cv':float(spread)}

def analyze():
    man=json.loads((ROOT/'blind_axial'/'manifest.json').read_text())
    result=[]
    for item in man['datasets']:
        path=ROOT/'blind_axial'/item['file']
        if digest(path)!=item['sha256']: raise RuntimeError('dataset hash mismatch: '+item['id'])
        with np.load(path,allow_pickle=False) as z:
            t=z['t'];k=z['k'];s=z['real']+1j*z['imag']; U=float(z['background_U_z'])
            if not np.array_equal(k,np.array(C['masked_synthetic']['wave_numbers_dimensionless'])): raise ValueError('k mismatch')
            if len(t)!=C['masked_synthetic']['time_samples']: raise ValueError('t mismatch')
            w=estimate_time_phase(s,t)
            cls=classify(k,w,U)
            result.append({'masked_id':item['id'],'dataset_sha256':item['sha256'],'estimated_omega':w.tolist(),**cls})
    return {'status':'SYNTHETIC_AXIAL_ONLY_NOT_PHYSICAL','axial_contract_sha256':digest(ROOT/'preregistration'/'AXIAL_SCIENCE_CONTRACT.json'),
            'axial_manifest_sha256':digest(ROOT/'blind_axial'/'manifest.json'),'results':result}

def freeze(obj):
    return hashlib.sha256((json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()

def run():
    obj=analyze();h=freeze(obj)
    lock=ROOT/'results'/'AXIAL_FROZEN_SHA256.txt'; res=ROOT/'results'/'AXIAL_BLIND_CLASSIFICATION.json'
    if lock.exists() and lock.read_text().strip()!=h: raise RuntimeError('axial sealed lock mismatch')
    res.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    if not lock.exists(): lock.write_text(h+'\n')
    return {'status':'PASS_SYNTHETIC_AXIAL_BLIND_FROZEN','classified':{i['masked_id']:i['classification'] for i in obj['results']},'sha256':h}

def verify():
    obj=analyze();h=freeze(obj)
    assert (ROOT/'results'/'AXIAL_FROZEN_SHA256.txt').read_text().strip()==h
    assert json.loads((ROOT/'results'/'AXIAL_BLIND_CLASSIFICATION.json').read_text())==obj
    return {'status':'PASS','sha256':h}
