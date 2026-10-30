"""A999 deterministic numeric integration control on an exported E010 dataset.
No SI units, no Euler dynamics, no independent physical source replication.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen_input(root):
    from sst_falsifier.pklsa_integration import _load_bridge,resolve_paths
    from sst_falsifier.config import load_instance_config
    import sys
    root=Path(root)
    spec=json.loads((root/'input'/'CONTROL_PIN.json').read_text())
    science=json.loads((root/'science_contract.json').read_text())
    registered=science.get('dataset_pin',{})
    for field,value in (('record',spec.get('record')),('manifest_sha256',spec.get('manifest_sha256')),('gamma',spec.get('gamma')),('core_fraction',spec.get('core_fraction'))):
        if registered.get(field)!=value:raise RuntimeError('A999 input pin changed from frozen science contract: '+field)
    paths=resolve_paths(root,load_instance_config(root)); bridge=_load_bridge(paths['adapter'])
    ds=bridge.ConsumerDataset(root/'input'/'e010_export')
    if ds.verification.get('status')!='PASS_DATASET_INTEGRITY_ONLY':raise RuntimeError('E010 export integrity failed')
    if ds.verification.get('manifest_sha256')!=spec['manifest_sha256']:raise RuntimeError('E010 export manifest changed from preregistered pin')
    if ds.list_ids()!=[spec['record']]:raise RuntimeError('Unanticipated dataset records')
    parts=ds.load(spec['record'])
    if len(parts)!=1:raise ValueError('Expected exactly one closed filament component')
    p=np.asarray(parts[0],dtype=np.float64)
    if p.ndim!=2 or p.shape[1]!=3 or p.shape[0]<8 or not np.isfinite(p).all():raise ValueError('invalid E010 filament')
    center=np.mean(p,axis=0)
    radius=float(np.max(np.linalg.norm(p-center,axis=1)))
    if not (np.isfinite(radius) and radius>0):raise ValueError('degenerate knot scale')
    offsets=np.asarray([[1.7,.2,.3],[-1.4,.5,.8],[.2,-1.5,.6],[1.1,1.1,-.5],[-.8,-1.2,1.2],[.5,.7,2],[1.8,-.6,-.1],[-.3,1.6,1]],dtype=np.float64)
    q=center+radius*offsets
    gamma=float(spec['gamma']);core=radius*float(spec['core_fraction'])
    payload={'record':spec['record'],'dataset_manifest_sha256':spec['manifest_sha256'],
        'points':p.tolist(),'queries':q.tolist(),'core':core,'gamma':gamma,
        'discretization':'periodic midpoint regularized Biot-Savart, non-SI'}
    input_id=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return p,q,gamma,core,input_id

def gpu_value(p,q,gamma,core,provider):
    import torch
    device='xpu:0' if provider=='intel' else 'cuda:0'
    P=torch.as_tensor(p,dtype=torch.float32,device=device)
    Q=torch.as_tensor(q,dtype=torch.float32,device=device)
    nxt=torch.roll(P,-1,0);dl=nxt-P;mids=.5*(P+nxt)
    r=Q[:,None,:]-mids[None,:,:]
    d=(r*r).sum(-1)+float(core)**2
    term=torch.cross(dl[None,:,:].expand_as(r),r,dim=-1)
    v=gamma/(4*math.pi)*(term/(d*torch.sqrt(d))[:,:,None]).sum(dim=1)
    (torch.xpu.synchronize if provider=='intel' else torch.cuda.synchronize)()
    if v.device.type!=('xpu' if provider=='intel' else 'cuda'):raise RuntimeError('Wrong GPU execution device')
    return v.cpu().numpy()

def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
    from sst_falsifier.backends.python_ref import biot_savart
    root=Path(root);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    p,q,gamma,core,input_id=frozen_input(root)
    results={}
    provider=cfg.get('gpu',{}).get('provider','intel')
    for kind in ('py','cpp','gpu'):
        if not devices.get(kind,{}).get('available'):
            results[kind]={'executed':False,'reason':'backend not available'}
            continue
        try:
            if kind=='py':
                value=biot_savart(p,q,gamma=gamma,core=core)
                src=root/'_sst_runtime'/'sst_falsifier'/'backends'/'python_ref.py'
                actual='python'
            elif kind=='cpp':
                from native_ext import _sst_native
                value=_sst_native.biot_savart(p,q,gamma,core)
                src=root/'native'/'cpp'/'native.cpp'
                actual='pybind11'
            else:
                value=gpu_value(p,q,gamma,core,provider)
                src=root/'experiment'/'backend_matrix.py'
                actual='torch_xpu' if provider=='intel' else 'torch_cuda'
            obs=np.asarray(value,dtype=np.float64).reshape(-1)
            if obs.size!=24 or not np.isfinite(obs).all():raise ValueError('invalid observable')
            evidence={'actual_backend':actual,'executed':True,'input_sha256':input_id,
                      'observable':obs.tolist(),'precision':'float32' if kind=='gpu' else 'float64',
                      'physical_final_time':None,'scope':'static E010 geometry; no dynamics or physical time',
                      'record':json.loads((root/'input'/'CONTROL_PIN.json').read_text())['record']}
            if kind=='gpu':evidence['device_type']='xpu' if provider=='intel' else 'cuda'
            if kind=='cpp':evidence['compiled_binary_sha256']=devices['cpp']['modules'][0]['sha256']
            target=out/(kind+'.json');target.write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n',encoding='utf8')
            results[kind]={'actual_backend':actual,'executed':True,'source_path':str(src),
                'source_sha256':digest(src),'evidence_path':str(target),'evidence_sha256':digest(target),
                'observable':obs.tolist(),'input_sha256':input_id}
        except Exception as exc:
            results[kind]={'executed':False,'reason':f'{type(exc).__name__}: {exc}'}
    return results
