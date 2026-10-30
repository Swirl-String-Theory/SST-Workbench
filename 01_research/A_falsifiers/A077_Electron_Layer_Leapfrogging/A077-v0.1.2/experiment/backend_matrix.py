"""Real science-backend hook for Framework v1.1.0.

Only Python and an actually installed C++ pybind11 science extension are declared.
A framework preflight is not execution. No GPU records are fabricated.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
from science.ring_model import trajectory,circulation


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _json(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()

def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
 root=Path(root);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
 config=json.loads((root/'configs'/'pilot.json').read_text())
 case=config['initial_conditions_dimensionless']['same']
 y=np.column_stack((case['radii'],case['z'])).reshape(-1).tolist()
 g=[float(v) for v in case['gamma_signs']]
 a=[float(x)*config['core_ratio'] for x in case['radii']]
 steps=int(config['pilot_steps']);dt=config['normalized_time_end']/steps
 ntheta=int(config['angular_quadrature']);k=float(config['self_induction_constant'])
 input_data={'y':y,'gamma':g,'core':a,'steps':steps,'dt':dt,'ntheta':ntheta,'k':k}
 input_hash=hashlib.sha256(_json(input_data)).hexdigest()
 R0=config['reference_scale']['radius_m'];gamma0=circulation(R0,config['reference_scale']['speed_m_s'])
 t_final=steps*dt*(R0*R0/gamma0)
 results={}
 for kind in ('py','cpp','gpu'):
  if kind=='gpu':
   results[kind]={'executed':False,'reason':'No Intel/CUDA physical ring science kernel implemented; no phantom GPU backend.'}
   continue
  if not devices.get(kind,{}).get('available'):
   results[kind]={'executed':False,'reason':'Required actual backend not available from preflight'}
   continue
  try:
   if kind=='py':
    sim=trajectory(y,g,a,dt=dt,steps=steps,ntheta=ntheta,self_constant=k)
    sample=np.asarray(sim['y'],dtype=np.float64)[::max(1,steps//16)].ravel()
    if (steps%max(1,steps//16))!=0: sample=np.r_[sample,np.asarray(sim['y'][-1])]
    source=root/'science'/'ring_model.py';name='python';binary=None
   else:
    from native_ext import _sst_native
    arr=np.asarray(_sst_native.ring_integrate(y,g,a,dt,steps,ntheta,k),dtype=np.float64).reshape((steps+1,len(y)))
    sample=arr[::max(1,steps//16)].ravel()
    if (steps%max(1,steps//16))!=0: sample=np.r_[sample,arr[-1]]
    source=root/'native'/'cpp'/'native.cpp';name='pybind11';binary=Path(_sst_native.__file__)
   obs=sample.astype(float).tolist()
   record={'actual_backend':name,'executed':True,'input_sha256':input_hash,
       'observable':obs,'precision':'float64','physical_final_time':t_final,
       'science_model':'regularized_filament_proxy','source_role':'DIAGNOSTIC_ONLY'}
   if binary is not None:record['compiled_binary_sha256']=_sha(binary)
   evidence=out/f'{kind}.json';evidence.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
   results[kind]={'actual_backend':name,'executed':True,'source_path':str(source),
       'source_sha256':_sha(source),'evidence_path':str(evidence),'evidence_sha256':_sha(evidence),
       'observable':obs,'input_sha256':input_hash}
   if kind=='cpp':
    results[kind]['warning']='Framework validates pybind11 binary against preflight; any mismatch must block.'
  except Exception as exc:
   results[kind]={'executed':False,'error':f'{type(exc).__name__}: {exc}'}
 return results
