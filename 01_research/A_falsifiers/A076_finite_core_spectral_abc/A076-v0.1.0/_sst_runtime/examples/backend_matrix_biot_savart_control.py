"""EXAMPLE ONLY: 2/3 Biot--Savart discretization control for a generated instance.

Copy to experiment/backend_matrix.py ONLY when this numerical benchmark is a
registered component of the falsifier's science contract. Uses a fixed synthetic
circle; substitute a pinned ConsumerDataset export for actual knot intake.
Never infer Euler stability, an SI calibration, or independent source replication.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _gpu_eval(points,queries,provider):
    import torch
    dev='xpu:0' if provider=='intel' else 'cuda:0'
    p=torch.tensor(points,dtype=torch.float32,device=dev);q=torch.tensor(queries,dtype=torch.float32,device=dev)
    pp=torch.roll(p,shifts=-1,dims=0)
    dl=pp-p;mids=(pp+p)*0.5
    r=q[:,None,:]-mids[None,:,:]
    D=(r*r).sum(dim=-1)+0.04**2
    v=(torch.cross(dl[None,:,:].expand_as(r),r,dim=-1)/(D*torch.sqrt(D))[:,:,None]).sum(dim=1)/(4.0*math.pi)
    if provider=='intel':torch.xpu.synchronize()
    else:torch.cuda.synchronize()
    return v.cpu().numpy().astype(float)

def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
    from sst_falsifier.backends.python_ref import biot_savart
    import importlib
    root=Path(root);output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    angles=np.linspace(0,2*math.pi,48,endpoint=False)
    points=np.column_stack((np.cos(angles),np.sin(angles),np.zeros_like(angles)))
    queries=np.array([[0.0,0.0,0.3],[0.3,0.1,0.2],[-0.2,0.2,0.4]],dtype=np.float64)
    inputs={'points':points.tolist(),'queries':queries.tolist(),'gamma':1.0,'core':0.04,
            'note':'dimensionless synthetic control, not SI-calibrated knot dynamics'}
    input_id=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    results={}
    for kind,actual in [('py','python'),('cpp','pybind11'),('gpu','torch_xpu' if cfg.get('gpu',{}).get('provider','intel')=='intel' else 'torch_cuda')]:
        if not devices.get(kind,{}).get('available'):continue
        try:
            if kind=='py':
                value=biot_savart(points,queries,gamma=1.0,core=0.04)
                src=root/'_sst_runtime'/'sst_falsifier'/'backends'/'python_ref.py'
                # Source for the independent Python kernel lives inside frozen instance runtime.
            elif kind=='cpp':
                from native_ext import _sst_native
                value=_sst_native.biot_savart(points,queries,1.0,0.04)
                src=root/'native'/'cpp'/'native.cpp'
            else:
                value=_gpu_eval(points,queries,cfg.get('gpu',{}).get('provider','intel'))
                src=root/'experiment'/'backend_matrix.py'
            observable=np.asarray(value,dtype=float).reshape(-1).tolist()
            payload={'actual_backend':actual,'executed':True,'input_sha256':input_id,
                     'observable':observable,'precision':'float32' if kind=='gpu' else 'float64',
                     'physical_final_time':None,'experiment':'synthetic regularized Biot-Savart control'}
            if kind=='gpu':payload['device_type']='xpu' if cfg.get('gpu',{}).get('provider','intel')=='intel' else 'cuda'
            if kind=='cpp':payload['compiled_binary_sha256']=devices['cpp']['modules'][0]['sha256']
            target=output_dir/f'{kind}.json';target.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n',encoding='utf8')
            results[kind]={'actual_backend':actual,'executed':True,'source_path':str(src),
                           'source_sha256':_sha(src),'evidence_path':str(target),
                           'evidence_sha256':_sha(target),'observable':observable,'input_sha256':input_id}
        except Exception as e:
            # Do not misclassify an import error, unsupported kernel, or device problem as executed.
            results[kind]={'executed':False,'error':f'{type(e).__name__}: {e}'}
    return results
