"""Science-specific A075 v0.1.0 evaluators for the frozen Framework v1.0.10.

Critical: a short-time self-energy redistribution is NOT a capture measurement.
"""
from __future__ import annotations
import json,hashlib
from pathlib import Path
from dataclasses import asdict
from typing import Any
import numpy as np
from .model import Case,run,initialize,hamiltonian_parts

def _write_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    sci=out/'science';sci.mkdir(parents=True,exist_ok=True)
    # Protocol had already been verified by the genuine v1.0.10 runner.
    ledger.record('G0','PASS',metrics={'actual_mode':mode,'framework_version':'1.0.10'},reason='Framework verified the frozen protocol before science evaluation',actual_backend='python-fp64',authority='SOFTWARE_ONLY')
    hashes={}
    for parent in ('A021','A032'):
        b=(root/'source_evidence'/f'{parent}_README.md').read_bytes()
        hashes[parent]=hashlib.sha256(b).hexdigest()
    source=json.loads((root/'source_contract.json').read_text(encoding='utf-8'))
    source_expected={x['source_id']:x.get('expected_sha256') for x in source['sources']}
    source_ok=all(hashes[x]==source_expected[x] for x in hashes)
    ca=Case(n=24,dt=0.05,final_time=1.0,zsep=0.7,a=0.22)
    cb=Case(n=24,dt=0.025,final_time=1.0,zsep=0.7,a=0.22)
    cc=Case(n=32,dt=0.025,final_time=1.0,zsep=0.7,a=0.22)
    far=Case(n=24,dt=0.05,final_time=1.0,zsep=12.0,a=0.22)
    runs={}
    for key,case in [('base',ca),('dt_half',cb),('n32',cc),('far',far)]:
        data,coords=run(case)
        runs[key]=data
        _write_json(sci/(key+'.json'),data)
        np.savez_compressed(sci/(key+'_snapshots.npz'),coordinates=coords)
    # fixed time; independent spatial/temporal gates must check each refinement separately.
    dt_err=abs(runs['base']['final_total_energy']-runs['dt_half']['final_total_energy'])/max(abs(runs['dt_half']['final_total_energy']),1e-15)
    ns_err=abs(runs['dt_half']['final_total_energy']-runs['n32']['final_total_energy'])/max(abs(runs['n32']['final_total_energy']),1e-15)
    null_e=hamiltonian_parts(initialize(24,zsep=12.0),(1.0,1.0),0.22)
    near_e=hamiltonian_parts(initialize(24,zsep=0.7),(1.0,1.0),0.22)
    mutual_ratio=abs(float(null_e[2]))/max(abs(float(near_e[2])),1e-15)
    diag={'relative_total_energy_drift':runs['base']['relative_energy_drift'],'relative_impulse_drift':runs['base']['relative_impulse_drift'],'temporal_refinement_final_energy_difference':dt_err,'spatial_refinement_final_energy_difference':ns_err,'mutual_null_to_near_ratio':mutual_ratio,'held_out_long_time_not_run':True,'physical_capture_fraction_not_measured':True}
    _write_json(sci/'diagnostics.json',diag)
    numerical_ok = (runs['base']['relative_energy_drift']<0.02 and
                    runs['base']['relative_impulse_drift']<0.02 and
                    mutual_ratio<0.03 and dt_err<1e-4 and ns_err<0.05)
    evaluators={
      'G1':lambda:{'status':'PASS' if source_ok else 'FAIL','metrics':hashes,'reason':'Byte-level A021/A032 source README SHA-256 admissibility' if source_ok else 'Source hash mismatch','authority':'SOURCE_PROVENANCE'},
      'G2':lambda:{'status':'PASS' if numerical_ok else 'FAIL','metrics':{**diag,'energy_drift_limit':0.02,'impulse_drift_limit':0.02,'far_to_near_max':0.03,'dt_diff_max':1e-4,'n_diff_max':0.05,'fixed_final_time_s':1.0},'reason':'Only short-run regularized filament no-loss, weak-coupling and refinement screening; NOT physical capture','actual_backend':'python-numpy-fp64','authority':'REDUCED_MODEL_ONLY'},
      'G3':lambda:{'status':'UNRESOLVED','metrics':{'measured_receiver_self_energy_change':runs['base']['receiver_self_energy_change'],'physical_capture_fraction':None,'late_window_periods':0},'reason':'No incoming finite-energy wavepacket, late post-encounter window, or full control-volume flux; no evidence of capture','authority':'NOT_PHYSICALLY_EVALUABLE'},
      'G4':lambda:{'status':'UNRESOLVED','metrics':{'independent_capture_holdout_count':0},'reason':'No independent capture demonstration to replicate; not a positive holdout result','authority':'NOT_EXECUTED'},
      'G8':lambda:{'status':'UNRESOLVED','metrics':{'full_3d_euler':False,'pressure_poisson':False,'volume_flux':False,'m_scan':[2,3,4,5,6,7],'m5_selected':False},'reason':'Full Euler provider and unconstrained azimuthal mode analysis are not implemented; cannot certify capture','authority':'NOT_EVALUABLE'},
    }
    ledger.run_evaluators(evaluators)
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REDUCED_MODEL_SCREENING'},'requested_native_backend':False,'native_cpp_parity':'NOT_RUN','sycl_gpu_parity':'NOT_RUN','source_hashes':hashes,'diagnostics':diag,'status':'DEVELOPMENT_ONLY'}
