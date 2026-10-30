"""Reproducible numerical pilot and fail-closed scientific gate ledger.

Never calls a GPU or pybind11 probe a scientific backend. Independent C++ CLI
is a local parity control; only an installed _ring_native pybind11 extension may
be used as the Framework cpp scientific category.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,math,os,platform,shutil,subprocess,sys,uuid,zipfile
from pathlib import Path
import numpy as np
from .ring_model import trajectory,analysis,circulation

ROOT=Path(__file__).resolve().parents[1]
VERSION='v0.1.1'
PREFIX='electron_layer_leapfrogging'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(d):return json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False)
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def scenario(cfg,key,steps=None,ntheta=None):
 pars=cfg['initial_conditions_dimensionless'][key]
 y=np.column_stack((pars['radii'],pars['z'])).ravel()
 g=np.array(pars['gamma_signs'],float)
 a=np.asarray(pars['radii'],float)*cfg['core_ratio']
 steps=int(steps or cfg['pilot_steps'])
 dt=cfg['normalized_time_end']/steps
 sim=trajectory(y,g,a,dt=dt,steps=steps,ntheta=ntheta or cfg['angular_quadrature'])
 stats=analysis(sim['t'],sim['y'],sim['gamma'],sim['a2R'])
 return sim,stats,{'initial':y.tolist(),'gamma':g.tolist(),'core':a.tolist(),
                    'steps':steps,'dt':dt,'ntheta':ntheta or cfg['angular_quadrature'],
                    't_final':float(sim['t'][-1]),'self_constant':cfg['self_induction_constant']}

def cpp_cli(control,root=ROOT):
 binary=root/'build'/('ring_cli.exe' if os.name=='nt' else 'ring_cli')
 if not binary.exists():return None,{'executed':False,'reason':'no compiled independent C++ CLI'}
 y=control['initial'];g=control['gamma'];a=control['core']
 vals=[len(g),control['ntheta'],control['steps'],control['dt'],*y,*g,*a]
 payload=' '.join(str(x) for x in vals)+'\n'
 run=subprocess.run([str(binary)],input=payload,capture_output=True,text=True,timeout=120)
 if run.returncode!=0:return None,{'executed':False,'error':run.stderr,'exit_code':run.returncode}
 arr=np.fromstring(run.stdout,sep=' ').reshape((control['steps']+1,len(y)))
 return arr,{'executed':True,'actual_backend':'C++17_CLI_DIAGNOSTIC',
     'source_sha256':sha(root/'native'/'ring_core.hpp'),'compiled_binary_sha256':sha(binary),
     'precision':'float64','input_sha256':hashlib.sha256(canonical(control).encode()).hexdigest(),
     'physical_final_time_s':control['t_final']*(1.40897017e-15**2/circulation())}

def rel(a,b):
 x=np.asarray(a,float);y=np.asarray(b,float)
 return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-14))

def run(cfg_path,output,quick=False,try_cpp=False):
 cfg=json.loads(Path(cfg_path).read_text(encoding='utf8'))
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 state={'schema':'SST-ELECTRON-LAYER-RESULTS-1','created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'run_id':dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10],
        'input_sha256':sha(cfg_path),'model':cfg['model'],'status':'DEVELOPMENT_DIAGNOSTIC_ONLY',
        'python':sys.version,'platform':platform.platform(),'scenarios':{},'gates':{},'limits':[]}
 tscale=cfg['reference_scale']['radius_m']**2/circulation()
 state['units']={'R0_m':cfg['reference_scale']['radius_m'],'Gamma0_m2_s':circulation(),
                 't0_s':tscale,'density_kg_m3':cfg['reference_scale']['fluid_density_kg_m3']}
 names=['single','same','opposite','reverse']
 for name in names:
  sim,stats,control=scenario(cfg,name,steps=min(cfg['pilot_steps'],60) if quick else None)
  state['scenarios'][name]={'stats':stats,'input':control,'initial_data_sha256':hashlib.sha256(canonical(control).encode()).hexdigest()}
  write(output/f'{name}_trajectory.json',{'t_normalized':sim['t'].tolist(),
     't_s':(sim['t']*tscale).tolist(), 'r_z_normalized':sim['y'].tolist(),
     'R0_m':cfg['reference_scale']['radius_m'],'status':'PROXY_ONLY'})
  print('[SST][PROGRESS]',name,'DONE steps=',control['steps'],flush=True)
 _,_,control= scenario(cfg,'same',steps=min(cfg['pilot_steps'],60) if quick else None)
 baseline=json.loads((output/'same_trajectory.json').read_text())
 basefinal=np.asarray(baseline['r_z_normalized'][-1],float)
 spatial=[];temporal=[]
 for n in cfg['spatial_refinement_ntheta']:
  ss,_,_=scenario(cfg,'same',steps=control['steps'],ntheta=n)
  spatial.append({'ntheta':n,'final':ss['y'][-1].tolist()})
 for steps in cfg['temporal_refinement_steps']:
  if quick:steps=max(16,steps//2)
  tt,_,_=scenario(cfg,'same',steps=steps,ntheta=cfg['angular_quadrature'])
  temporal.append({'steps':steps,'dt':cfg['normalized_time_end']/steps,'final':tt['y'][-1].tolist()})
 spatial_error=rel(spatial[-1]['final'],spatial[-2]['final'])
 temporal_error=rel(temporal[-1]['final'],temporal[-2]['final'])
 state['refinement']={'spatial':spatial,'temporal':temporal,
      'spatial_last_rel_error':spatial_error,'temporal_last_rel_error':temporal_error,
      'fixed_physical_final_time_s':control['t_final']*tscale}
 cpp={'executed':False,'reason':'not attempted'}
 if try_cpp:
  c_arr,cpp=cpp_cli(control)
  if c_arr is not None:
   py_arr=np.asarray(baseline['r_z_normalized'])
   cpp['relative_L2']=rel(c_arr,py_arr)
   state['C++_CLI_comparison']=cpp
  else:state['C++_CLI_comparison']=cpp
 else:state['C++_CLI_comparison']=cpp
 def gate(name,status,reason,metrics=None,qualification='DIAGNOSTIC_ONLY'):
  state['gates'][name]={'status':status,'qualification':qualification,'reason':reason,'metrics':metrics or {}}
 gate('P01','PASS' if state['scenarios']['single']['stats']['core_proxy_relative_drift']<5e-3 else 'FAIL',
      'Proxy circulation and a²R are conserved by construction, not verified Euler circulation.',
      {'core_proxy_drift':state['scenarios']['single']['stats']['core_proxy_relative_drift']})
 gate('P02','UNRESOLVED', 'Multiple overtakes and full 3D finite-core Euler convergence are not certified; scan provides trajectories only.',
      {'observed_order_swaps':state['scenarios']['same']['stats']['crossing_count']})
 gate('P03','PASS','Opposite-sign two-ring control was numerically executed; no general physical stability claim.',
      {'order_swaps':state['scenarios']['opposite']['stats']['crossing_count']})
 gate('P04','UNRESOLVED','Independent toroidal material circulation and its full-field evolution not implemented.')
 gate('P05','UNRESOLVED','Order-swap events cannot establish discrete stable energy levels; no spectral/Euler provider.')
 gate('P06','UNRESOLVED','Spinor 2pi/4pi monodromy and exchange topology require a representation not supplied by Euler kinematics.')
 gate('P07','UNRESOLVED','No divergence-controlled 3D velocity field; jet/sprite analogy is excluded from physics conclusions.')
 gate('G0','UNRESOLVED','Requires official embedded v1.1.0 runtime FREEZE; not represented by independent pilot.')
 gate('G1','PASS','Analytic initial data and config hash recorded; no E010 atlas used.',
      {'config_sha256':state['input_sha256']})
 gate('G2','PASS' if spatial_error<=cfg['spatial_relative_tolerance'] and temporal_error<=cfg['temporal_relative_tolerance'] else 'FAIL',
      'Reduced-model numerical convergence ONLY; not spatial Euler-grid convergence.',
      {'spatial_quadrature_rel':spatial_error,'temporal_RK4_rel':temporal_error})
 gate('G3','UNRESOLVED','Blind discovery of spectral levels and 2pi/4pi properties not implemented.')
 gate('G4','UNRESOLVED','No independent held-out full-Euler provider.')
 gate('G5','UNRESOLVED',
      'C++ CLI parity local diagnostic ONLY; framework G5 requires pybind11 + official preflight.',
      {'cpp':cpp},'DIAGNOSTIC_ONLY')
 gate('P08','PASS' if cpp.get('executed') and cpp.get('relative_L2',1)<=cfg['backend_parity_relative_tolerance'] else 'UNRESOLVED',
      'Independent C++17 command-line parity; not the framework pybind11 backend.', {'cpp_relative_L2':cpp.get('relative_L2')})
 gate('G6','UNRESOLVED','No actual Intel XPU/CUDA science kernel. GPU probe never counts.')
 gate('G7','UNRESOLVED','Numerical resolution variants are not independent evidence families.')
 gate('G8','UNRESOLVED','No full 3D incompressible Euler finite-core closure or spinor transport.')
 gate('G9','NOT_EXECUTED','No scientific reveal performed.')
 state['limits']=['Biot-Savart core smoothing and thin-core self-induction are model assumptions.',
      'Self-induced core scaling a²R conservation is imposed.',
      'No C++ CLI counts as framework pybind11 by itself.',
      'No claimed physical electron, quantum spin, photon or discrete layers.',
      'All results based on normalized finite-dimensional ring ODE, not 3D Euler.']
 write(output/'RUN_SUMMARY.json',state)
 write(output/'GATE_LEDGER.json',state['gates'])
 write(output/'INPUT_PROVENANCE.json',{'config_path':str(cfg_path),'config_sha256':sha(cfg_path),
      'python_source_sha256':sha(ROOT/'science'/'ring_model.py'),
      'cpp_source_sha256':sha(ROOT/'native'/'ring_core.hpp')})
 return state

def pack(root=ROOT):
 out=root/(f'{PREFIX}_{VERSION}-outputs')
 if not out.exists():raise FileNotFoundError(out)
 archive=root.parent/(f'{PREFIX}_{VERSION}_outputs_BLIND.zip')
 if archive.exists():
  archive=root.parent/(f'{PREFIX}_{VERSION}_outputs__{uuid.uuid4().hex[:8]}_BLIND.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(out.rglob('*')):
   if f.is_file():z.write(f,f'{out.name}/{f.relative_to(out)}')
 (Path(str(archive)+'.sha256')).write_text(sha(archive)+'  '+archive.name+'\n')
 return archive

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--config',default=str(ROOT/'configs'/'pilot.json'))
 p.add_argument('--output',default=str(ROOT/(f'{PREFIX}_{VERSION}-outputs')))
 p.add_argument('--quick',action='store_true');p.add_argument('--cpp',action='store_true');p.add_argument('--archive',action='store_true')
 args=p.parse_args()
 st=run(args.config,args.output,quick=args.quick,try_cpp=args.cpp)
 print('STATUS:',st['status'],'spatial_error:',st['refinement']['spatial_last_rel_error'],'temporal_error:',st['refinement']['temporal_last_rel_error'])
 if args.archive:print('ARCHIVE:',pack())
 if any(st['gates'][g]['status']=='UNRESOLVED' for g in ('P04','P05','P06','G8')):
  print('SCIENTIFIC_CLAIM_UNRESOLVED (expected); official certification not run')
if __name__=='__main__':main()
