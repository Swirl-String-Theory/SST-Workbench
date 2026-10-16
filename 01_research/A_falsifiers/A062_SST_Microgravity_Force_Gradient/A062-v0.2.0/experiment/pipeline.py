"""Non-invasive scientific plug-in for the frozen SST Falsifier Framework v1.0.7.

Canonical framework is REQUIRED and is not bundled; standalone tests are not
promoted into framework certification. Do not modify the framework itself.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from microgravity.runner import run

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'shared_framework':'1.0.7','mode':mode},
      reason='Canonical framework validated frozen protocol before science entry')
    result=run(mode if mode in ('BASIC','FULL','CERTIFY') else 'FULL')
    st=result['local_gates']
    def register(gid,status,reason,metrics=None,authority='REFERENCE',backend='python-fp64'):
        if gid not in ledger.defs:return
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by frozen framework profile');return
        ledger.record(gid,status,reason=reason,metrics=metrics or {},actual_backend=backend,authority=authority)
    register('G1',st['P1'],'Two E011 static source providers verified by raw SHA256',
             {'upstream_providers':2,'not_dynamics_ready':True})
    register('G2','PASS' if st['P2']==st['P3']=='PASS' else 'FAIL',
             'Separate numerical convergence and Kelvin impulse reciprocity checks',
             {'convergence':result['convergence'],'reciprocity':result['max_reciprocity_residual']})
    register('G3','PASS' if st['P4']==st['P5']=='PASS' else 'FAIL',
             'No G used by filament solver; inverse-square and orientation gates scored independently',
             {'slope':{p:q['farfield_exponent'] for p,q in result['providers'].items()},
              'orientation_gate':st['P5']})
    register('G4','UNRESOLVED','No experimentally withheld multiseparation raw force data')
    register('G5',st['P8'],'Native independent C++17 strict FP64 parity',result['native_cpp_fp64'],
             authority='CERTIFICATION' if st['P8']=='PASS' else 'NONE',
             backend='cpp-fp64' if result['native_cpp_fp64']['executed'] else 'unavailable')
    register('G6','UNRESOLVED','No GPU kernel in CPU scientific campaign',authority='NONE',backend='not_requested')
    register('G7',st['P6'],'Independent E011 Gilbert/KnotPlot primary-provider source cross check',
             {'provider_rel_amplitude_at_R5':result['provider_rel_force_amplitude_at_R5']})
    register('G8','UNRESOLVED','Pressure core underresolved; no full Euler dynamics or particle mass closure',
             {'Poisson':result['poisson_diagnostic'],'macrogravity_identified':False})
    return {'schema':'SST-BACKEND-MANIFEST-2',
      'python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},
      'cpp_fp64':result['native_cpp_fp64'],'sycl_gpu':{'requested':False,'authority':'SCREENING_ONLY'},
      'science':'PKLSA centreline Euler-vortex-filament impulse exchange, no derived gravitational force'}
