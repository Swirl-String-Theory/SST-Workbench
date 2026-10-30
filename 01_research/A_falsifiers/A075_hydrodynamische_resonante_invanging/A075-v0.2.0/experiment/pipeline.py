"""Framework v1.0.10 science adapter; does not impersonate framework freeze."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
from .science import run_suite

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    root=Path(root)
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"/'science'
    ledger.record('G0','PASS',metrics={'actual_mode':mode,'framework_version':'1.0.10'},
                  reason='Genuine v1.0.10 framework invoked science adapter',
                  actual_backend='python-numpy-spectral',authority='SOFTWARE_ONLY')
    refs={'A021':'b615595589551dafbcabddc223e554abeb6ab5a02a064fa96522af73d533e3e9',
          'A032':'e78411ee0a3a0cd770bd8293e117f44b1908bd419877b5163d5df21b71b9da0e'}
    ok=all(hashlib.sha256((root/'source_evidence'/f'{k}_README.md').read_bytes()).hexdigest()==v for k,v in refs.items())
    if not ok:
        ledger.run_evaluators({'G1':lambda:{'status':'FAIL','reason':'Immutable source evidence hash mismatch'}})
        raise RuntimeError('SOURCE HASH GATE FAILED')
    result=run_suite(root,mode if mode in ('BASIC','FULL') else 'PREVIEW',out)
    status=result['gates']['G2']['status']
    ledger.run_evaluators({
      'G1':lambda:{'status':'PASS','metrics':refs,'reason':'Exact A021/A032 method hash check','authority':'SOURCE_PROVENANCE'},
      'G2':lambda:{'status':status,'metrics':{k:v.get('diagnostics',{}) for k,v in result['cases'].items()},
                    'reason':'Independent temporal/spatial short-run periodic Euler screening; not final physical test',
                    'actual_backend':'numpy-fft64','authority':'NUMERICAL_SCREENING_ONLY'},
      'G3':lambda:{'status':'UNRESOLVED','metrics':{'retention_qualified':False,'post_exit_clock_cycles':None},
                    'reason':'No verified donor exit, independent clock or long time tail','authority':'NO_PHYSICAL_CLAIM'},
      'G4':lambda:{'status':'UNRESOLVED','reason':'No independent preregistered holdout','authority':'NOT_EXECUTED'},
      'G8':lambda:{'status':'UNRESOLVED','metrics':{'periodic_3d_euler_run':True,'pressure_poisson_implemented':True,
                     'weak_window_flux_implemented':True,'spatial_continuum_converged':False,'finite_core_converged':False},
                     'reason':'3D periodic Euler field implemented; full flux, finite-core and box convergences not qualified',
                     'authority':'PARTIAL_EULER_PROVIDER'}})
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fft64',
        'precision':'float64','authority':'DEVELOPMENT_ONLY'},'source_hashes':refs,
        'native_cpp_parity':'NOT_RUN','sycl_gpu_parity':'NOT_RUN','physical_answer':'UNRESOLVED',
        'science_gate_file':str(out/'A075_GATES.json'),'status':'DEVELOPMENT_ONLY'}
