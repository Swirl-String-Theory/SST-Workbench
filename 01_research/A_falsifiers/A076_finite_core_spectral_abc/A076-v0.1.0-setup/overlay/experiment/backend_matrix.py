"""Framework v1.1.0: actual Python+compiled C++ regularized ring kernel control.

G10 certifies the static Biot-Savart SUBKERNEL only. It does not certify the
full Fourier eigenproblem. Both kernels process exactly the same pinned ring.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def data():
    ang=np.arange(48,dtype=float)*2*math.pi/48.
    p=np.column_stack((4.*np.cos(ang),4.*np.sin(ang),np.zeros(48)))
    q=np.array([[0,0,.5],[1,2,1.5],[-3,1,.7],[2,-.2,3.1],
          [-1,-2,-1],[.2,1,-2.5],[3,-3,2],[1.9,-1.2,-.7]],dtype=np.float64)
    gamma=1.;core=1.
    raw={'geometry':'fixed ring R/a=4; N=48; eight preregistered queries',
         'p':p.tolist(),'q':q.tolist(),'gamma':gamma,'a':core}
    sha=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return p,q,gamma,core,sha

def gpu_eval(p,q,gamma,a,provider):
    import torch
    device='xpu:0' if provider=='intel' else 'cuda:0'
    P=torch.tensor(p,device=device,dtype=torch.float32)
    Q=torch.tensor(q,device=device,dtype=torch.float32)
    dl=torch.roll(P,-1,0)-P;mid=.5*(P+torch.roll(P,-1,0));r=Q[:,None,:]-mid[None,:,:]
    den=(r*r).sum(-1)+a*a
    vv=(torch.cross(dl[None,:,:].expand_as(r),r,dim=-1)/(den*torch.sqrt(den))[:,:,None]).sum(1)*gamma/(4*math.pi)
    if provider=='intel':torch.xpu.synchronize()
    else:torch.cuda.synchronize()
    if vv.device.type!=('xpu' if provider=='intel' else 'cuda'):raise RuntimeError('wrong actual device')
    return vv.cpu().numpy()

def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
    from sst_falsifier.backends.python_ref import biot_savart
    from sst_falsifier import progress
    root=Path(root);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    p,q,gamma,a,inp=data()
    provider=cfg.get('gpu',{}).get('provider','intel')
    res={}
    for i,k in enumerate(('py','cpp','gpu'),1):
        if not devices.get(k,{}).get('available'):
            res[k]={'executed':False,'reason':'preflight unavailable'};continue
        try:
            with progress.phase('BACKEND',completed=i-1,total=3,backend=k):
                if k=='py':
                    z=biot_savart(p,q,gamma=gamma,core=a)
                    src=root/'_sst_runtime'/'sst_falsifier'/'backends'/'python_ref.py';actual='python'
                elif k=='cpp':
                    from native_ext import _sst_native
                    z=_sst_native.biot_savart(p,q,gamma,a)
                    src=root/'native'/'cpp'/'native.cpp';actual='pybind11'
                else:
                    z=gpu_eval(p,q,gamma,a,provider)
                    src=root/'experiment'/'backend_matrix.py'
                    actual='torch_xpu' if provider=='intel' else 'torch_cuda'
                obs=np.asarray(z,dtype=float).ravel()
                if len(obs)!=24 or not np.all(np.isfinite(obs)):raise ValueError('bad kernel control')
                payload={'actual_backend':actual,'executed':True,'input_sha256':inp,
                         'observable':obs.tolist(),'precision':'float32' if k=='gpu' else 'float64',
                         'physical_final_time':None,'scope':'STATIC_KERNEL_CONTROL_ONLY'}
                if k=='cpp':payload['compiled_binary_sha256']=devices['cpp']['modules'][0]['sha256']
                if k=='gpu':payload['device_type']='xpu' if provider=='intel' else 'cuda'
                fp=out/f'{k}.json';fp.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n',encoding='utf8')
                res[k]={'actual_backend':actual,'executed':True,'source_path':str(src),
                    'source_sha256':digest(src),'evidence_path':str(fp),'evidence_sha256':digest(fp),
                    'observable':obs.tolist(),'input_sha256':inp}
        except Exception as exc:
            res[k]={'executed':False,'error':f'{type(exc).__name__}: {exc}'}
    return res
