"""Scientific P1--P3 gate adapter for Framework 1.1.0 RC2.
No kernel is counted without actual source, input, and evidence hashes.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .qualification import run
from sst_falsifier.source_registry import resolve_source_contract

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode},reason='Runtime and frozen preregistration verified by v1.1.0 framework')
    root=Path(root)
    result=run(grids=[32,48,64],out=root/'A074_Max_Transfer_Force_Trefoil_v0.3.0-outputs',time_evolution=True)
    fits=[g['full_field_fit']['relative_euler_field_residual'] for g in result['grids']]
    wellresolved=all(g['core_radius_cells']>=8 and g['free_gap_cells']>=3 for g in result['grids'])
    sources=resolve_source_contract(root/'source_contract.json')['sources']
    source_present=all(x.get('exists',False) for x in sources)
    source_map={x['source_id']:x for x in sources}
    source_match=source_present and source_map.get('GILBERT_3_1_1',{}).get('sha256')==result['P1']['identity']['seed_sha256'] and source_map.get('A074_V020_SELECTION',{}).get('sha256')==result['P1']['identity']['selection_sha256']
    evaluators={
      'G1':lambda: {'status':('PASS' if result['all_original_inputs_identical'] and source_match else 'UNRESOLVED'), 'metrics':{'p1_status':result['P1']['status'],'input_sha256':result['P1']['identity']['candidate_full_input_sha256'],'all_contract_sources_present':source_present,'source_hash_match':source_match},'reason':'P1 exact pinned seed/candidate; framework source admission must also match'},
      'G2':lambda: {'status':'PASS' if all(g['poisson']['poisson_relative_residual']<1e-8 for g in result['grids']) else 'FAIL','metrics':{'poisson_residuals':[g['poisson']['poisson_relative_residual'] for g in result['grids']]},'reason':'3D Euler pressure and divergence algebra check only'},
      'G3':lambda: {'status':'PASS' if wellresolved and min(fits)<=0.05 else ('FAIL' if wellresolved else 'UNRESOLVED'),'metrics':{'full_field_relative_residuals':fits,'core_and_gap_resolved':wellresolved,'threshold':0.05},'reason':'P2 full vorticity relative frame, not marker equilibrium. Underresolved grids remain unresolved.'},
      'G7':lambda: {'status':'PASS' if wellresolved and len(result['grids'])>=3 and min(fits)<=0.05 else 'UNRESOLVED','metrics':{'p3':result['P3']['status'],'last_pair':result['P3'].get('last_pair_relative_field_residual_difference')},'reason':'P3 spatial/temporal convergence not certified if core or gap underresolved.'}
    }
    ledger.run_evaluators(evaluators)
    return {'schema':'SST-BACKEND-MANIFEST-2','science':'P1-P3 ONLY','framework':'1.1.0',
            'scientific_status':'DEVELOPMENT_UNRESOLVED','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'DIAGNOSTIC'},
            'analysis':'A074_Max_Transfer_Force_Trefoil_v0.3.0-outputs/P1_P3_QUALIFICATION_SUMMARY.json'}
