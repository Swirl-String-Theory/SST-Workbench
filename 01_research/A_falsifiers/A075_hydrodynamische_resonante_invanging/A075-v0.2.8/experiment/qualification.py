"""A075-v0.2.8 qualification diagnostics: source resolution and operator parity.

A fixed-grid numerical-operator check is NOT proof of fully independent
solver trajectories, finite-core convergence, or long-lived energy capture.
The pinned Framework v1.1.0 runtime is never modified by these functions.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import hashlib, json, os
import numpy as np
from .euler3d import Config, Euler3D


def file_sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def inspect_sources(root):
    """Use the actual Framework resolver and verify complete byte identity."""
    root=Path(root).resolve()
    from sst_falsifier.source_registry import resolve_source_contract
    wb=Path(os.getenv('SST_WORKBENCH_ROOT') or root.parents[3]).resolve()
    payload=resolve_source_contract(root/'source_contract.json',root=wb)
    contract=json.loads((root/'source_contract.json').read_text(encoding='utf8'))
    expected={s['source_id']:s.get('expected_sha256') for s in contract['sources']}
    rows=[]
    for row in payload['sources']:
        wanted=expected.get(row['source_id'])
        row={**row, 'expected_sha256':wanted,'hash_match':bool(row.get('exists') and wanted and row.get('sha256')==wanted)}
        rows.append(row)
    valid=bool(rows) and all(r['hash_match'] for r in rows)
    return {'schema':'A075-SOURCE-RESOLUTION-1','workbench_root':str(wb),'passed':valid,
            'sources':rows,'methodology_note':'A021/A032 packaged README evidence is not a full original experimental dataset; no independent source replication is claimed.'}


def _reference_fields(root):
    for knot in ('0_1','3_1'):
        c=Config(n=16,box=10.0,dt=.01,final_time=.02,core=.5,geometry=knot,
                 xyz_root=str(Path(root)/'inputs'),threads=2,backend='cpu-scipy-fft')
        s=Euler3D(c)
        uh,_=s.initial_velocity()
        yield knot,c,uh,s.rhs(uh)


def parity_screen(root, category):
    """Two genuine analytic knot fields, operator RHS only, no dummy backend."""
    root=Path(root).resolve()
    if category not in {'cpp','gpu'}:raise ValueError('category must be cpp|gpu')
    identity='pybind11-cross3' if category=='cpp' else 'pytorch-xpu-spectral-rhs'
    result={'schema':'A075-OPERATOR-PARITY-1','category':category,'operator':identity,
            'physical_qualification':False,'precision':'float64' if category=='cpp' else 'float32',
            'threshold_relative_l2':1e-9 if category=='cpp' else 2e-3,
            'source_sha256':file_sha256(root/('native/cpp/native.cpp' if category=='cpp' else 'experiment/euler_torch.py')),
            'cases':[],'status':'UNRESOLVED','qualification':'NUMERICAL_OPERATOR_DIAGNOSTIC_ONLY'}
    try:
        if category=='cpp':
            # The framework's own verified pybind11 builder can prepare this
            # backend before the mandatory 2/3 execution stage. Never fall
            # back to Python if compilation fails.
            from sst_falsifier.native_build import build_pybind
            build=build_pybind(root,verbose=False)
            if not build.success:
                raise RuntimeError('Native pybind11 build failed: '+str(build.error))
            from .native import load_cpp
            module=load_cpp()
            result['compiled_binary_sha256']=file_sha256(module.__file__)
            result['actual_backend']='pybind11'
        else:
            import torch
            if not torch.xpu.is_available() or not getattr(torch.version,'xpu',None):
                raise RuntimeError('PyTorch XPU unavailable (never count CPU torch as a GPU test)')
            result['actual_backend']='torch_xpu'
            result['gpu_device']=str(torch.xpu.get_device_name(0))
        for knot,c,uh,reference in _reference_fields(root):
            if category=='cpp':
                obj=Euler3D(replace(c,backend='cpp-hybrid'))
                comparison=obj.rhs(uh)
            else:
                from .euler_torch import TorchEuler3D
                obj=TorchEuler3D(replace(c,backend='arc-xpu',gpu_precision='fp32'))
                candidate=obj.to_device(uh)
                comparison=obj.rhs(candidate).detach().cpu().numpy()
                torch.xpu.synchronize()
            denom=max(float(np.linalg.norm(reference.ravel())),1e-30)
            rel=float(np.linalg.norm((comparison-reference).ravel())/denom)
            ok=bool(np.isfinite(rel) and rel<=result['threshold_relative_l2'])
            result['cases'].append({'knot':knot,'grid':16,'relative_l2':rel,'pass':ok,'finite':bool(np.isfinite(comparison).all())})
        result['status']='PASS' if all(z['pass'] for z in result['cases']) else 'FAIL'
    except Exception as exc:
        result['status']='UNRESOLVED'
        result['reason']=f'{type(exc).__name__}: {exc}'
    return result


def topology_inputs(root):
    root=Path(root)
    rows=[]
    for k in ('5_2','6_1'):
        p=root/'inputs'/f'KNOT_{k}_N2048_ORIG.xyz'
        rows.append({'knot':k,'file':str(p.relative_to(root)),'present':p.is_file(),
                     'sha256':file_sha256(p) if p.is_file() else None,
                     'independent_topology_certified':False})
    return {'status':'UNRESOLVED','files':rows,'reason':'Only byte availability tested; independent topology, embeddings and physical replication remain unqualified.'}


def domain_gate(domain):
    if not domain:
        return {'status':'UNRESOLVED','reason':'Optional periodic-box study not requested; no free-space claim'}
    knots=domain.get('knots',{})
    performed=bool(knots) and all(x.get('execution')=='EXECUTED' for x in knots.values())
    return {'status':'PASS' if performed else 'UNRESOLVED',
      'reason':'Periodic box diagnostic completed at constant dx; NOT free-space certification' if performed else 'Some boxes or knots were not evaluated',
      'metrics':{'executed':performed,'physical_free_space_pass':False,'periodic_images_present':True,
       'knots':{k:{'execution':v.get('execution'),'last_pair_difference':v.get('last_pair_difference')} for k,v in knots.items()},
       'fixed_physical_dx':domain.get('fixed_physical_dx'),'fixed_core_sigma':domain.get('fixed_core_sigma')}}
