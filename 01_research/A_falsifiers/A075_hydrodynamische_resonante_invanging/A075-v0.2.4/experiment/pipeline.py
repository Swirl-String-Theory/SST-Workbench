"""Framework v1.0.10 science adapter; does not impersonate framework freeze."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from typing import Any
from .science import run_suite,run_matrix

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
    overrides=json.loads(os.environ.get('A075_RUNTIME_OPTIONS_JSON','{}'))
    profile=mode if mode in ('BASIC','EXTENDED','FULL') else 'PREVIEW'
    if overrides.get('domain_study_only'):
        from .science import _resolve
        from .domain import run_domain_study
        resolved=_resolve(profile,overrides)
        domain=run_domain_study(root,profile,out/'domain_study',resolved)
        result={'gates':{'G2':{'status':'UNRESOLVED'}},'cases':{},
                'resolved_options':resolved,'domain_study':domain}
    elif overrides.get('backends'):
        matrix=run_matrix(root,profile,out,overrides)
        # Matrix may contain diagnostics of multiple providers. The physical G2
        # remains UNRESOLVED until *all* independent convergence requirements close.
        result={'gates':{'G2':{'status':'UNRESOLVED'}},'cases':{},
                'resolved_options':overrides,'matrix':matrix}
    else:
        result=run_suite(root,profile,out,overrides=overrides)
    (out/'EXECUTION_OPTIONS.json').write_text(json.dumps({'schema':'A075-EXECUTION-OPTIONS-1',
        'requested':overrides,'resolved':result['resolved_options'],
        'qualification':'EXPLORATORY_RUNTIME_CHOICES_NOT_POSTHOC_CERTIFICATION'},indent=2)+'\n',encoding='utf8')
    status=result['gates']['G2']['status']
    ledger.run_evaluators({
      'G1':lambda:{'status':'PASS','metrics':refs,'reason':'Exact A021/A032 method hash check','authority':'SOURCE_PROVENANCE'},
      'G2':lambda:{'status':status,'metrics':{k:v.get('diagnostics',{}) for k,v in result['cases'].items()},
                    'reason':'Independent temporal/spatial short-run periodic Euler screening; not final physical test',
                    'actual_backend':result['resolved_options']['backend'],'authority':'NUMERICAL_SCREENING_ONLY'},
      'G3':lambda:{'status':'UNRESOLVED','metrics':{'retention_qualified':False,'post_exit_clock_cycles':None},
                    'reason':'No verified donor exit, independent clock or long time tail','authority':'NO_PHYSICAL_CLAIM'},
      'G4':lambda:{'status':'UNRESOLVED','reason':'No independent preregistered holdout','authority':'NOT_EXECUTED'},
      'G8':lambda:{'status':'UNRESOLVED','metrics':{'periodic_3d_euler_run':True,'pressure_poisson_implemented':True,
                     'weak_window_flux_implemented':True,'periodic_domain_sensitivity_completed':bool(result.get('domain_study',{}).get('executed')),'free_space_provider':False,'spatial_continuum_converged':False,'finite_core_converged':False},
                     'reason':'3D periodic Euler field implemented; domain study is periodic image sensitivity only; no nonperiodic Euler solver or certified post-exit flux',
                     'authority':'PARTIAL_EULER_PROVIDER'}})
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':result['resolved_options']['backend'],
        'precision':'float64','authority':'DEVELOPMENT_ONLY'},'source_hashes':refs,
        'native_cpp_parity':'PARTIAL_HYBRID_ONLY' if (overrides.get('backends') and matrix.get('backends',{}).get('cpp',{}).get('execution')=='EXECUTED') else 'NOT_RUN',
        'sycl_gpu_parity':'TORCH_XPU_SCREENING_ONLY' if (overrides.get('backends') and matrix.get('backends',{}).get('gpu',{}).get('execution')=='EXECUTED') else 'NOT_RUN','runtime_options':result['resolved_options'],'physical_answer':'UNRESOLVED',
        'domain_study':result.get('domain_study',{}),'science_gate_file':str(out/'A075_GATES.json'),'status':'DEVELOPMENT_ONLY'}
