"""A065-v0.3.9 *genuine*, fail-closed A003 v0.2.3 external adapter integration.

No external code is vendored, no seed files are forged. A003-v0.1.2
coordinates remain geometry-only even when used to generate a diagnostic
Gaussian 3D vortex. This is NOT source-native PKLSA/Euler dynamics.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

ADAPTER_SOURCE_SHA256 = '29c370a358ddf8969357db6eb2469cb526610046b0af3a58075589a3218e75e9'
ADAPTER_AUX_SHA256 = '882697658e34951ed0aaf26222b91e5a2f54024d1f4b82c552c4a221c036b795'
ATLAS_MANIFEST_SHA256 = '01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d'
VERSION = '0.2.3'
ATLAS_VERSION = 'v0.1.2'

class SourceIntegrityError(RuntimeError):
    pass

def sha(path: Path)->str:
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()

def _locate(root:Path, name:str, envvar:str, suffix:tuple[str,...]):
    override=os.getenv(envvar,'').strip()
    if override:
        p=Path(override).expanduser()
        if not p.is_dir():raise SourceIntegrityError(f'{envvar} override does not exist: {p}')
        return p.resolve()
    # These local paths are explicit *locations*, not scientific authority.
    wb=os.getenv('SST_WORKBENCH_ROOT','').strip()
    bases=[Path(wb)] if wb else []
    bases.extend([root,*root.parents])
    bases.append(Path(r'C:\workspace\projects\SST-Workbench'))
    for base in bases:
        p=base.joinpath(*suffix)
        if p.is_dir():return p.resolve()
    return None

def adapter_root(root:Path):
    return _locate(root,'A003', 'SST_A003_ADAPTER_ROOT',(
        '02_libraries','A_knot_libraries','A003_Fourier_Knot_Seed_Atlas',
        'A003_Fourier_Knot_Import_Adapter_v0.2.3'))

def atlas_root(root:Path, adapter:Path):
    override=os.getenv('SST_ATLAS_ROOT','').strip()
    if override:
        p=Path(override).expanduser()
        if not p.is_dir():raise SourceIntegrityError('SST_ATLAS_ROOT override not found: '+str(p))
        return p.resolve()
    if (adapter.parent/'A003-v0.1.2').is_dir():return (adapter.parent/'A003-v0.1.2').resolve()
    return None

def _record(status,reason,metrics=None,executed=None):
    return {'status':status,'reason':reason,'metrics':metrics or {},'execution_status':executed or ('NOT_EXECUTED' if status=='NOT_RUN_PREREQUISITE' else 'EXECUTED')}

def _load_original_adapter(path:Path):
    original=path/'fourier_atlas_adapter.py'
    aux=path/'gates_g4_g5.py'
    if not original.is_file() or not aux.is_file():
        raise SourceIntegrityError('A003 0.2.3 adapter source modules missing')
    if sha(original)!=ADAPTER_SOURCE_SHA256 or sha(aux)!=ADAPTER_AUX_SHA256:
        raise SourceIntegrityError('A003 v0.2.3 source SHA256 mismatch; external adapter altered')
    release=path/'RELEASE.json'
    if not release.is_file():raise SourceIntegrityError('A003 release manifest absent')
    if sha(release)!='04ddb797d78e2b8034e3044c03630e26bce7b4b71b5e39c5e60601fc9db87e04':
        raise SourceIntegrityError('A003 RELEASE.json hash mismatch')
    # Load *real source code* and its sibling gate functions, never replicate
    # the adapter's parser, hash audit or provenance contract.
    if str(path) not in sys.path:sys.path.insert(0,str(path))
    spec=importlib.util.spec_from_file_location('a003_original_adapter_v023',original)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.ADAPTER_VERSION!=VERSION or mod.ATLAS_VERSION!=ATLAS_VERSION or mod.PINNED_ATLAS_MANIFEST_SHA256!=ATLAS_MANIFEST_SHA256:
        raise SourceIntegrityError('A003 adapter runtime interface disagrees with frozen precommit')
    return mod

def _screen_geometry(adapter,root,manifest,record,pre):
    # Execute true A003 hash-verified xyz import; no reparametrization or fitted core.
    p=adapter.safe_atlas_file(root,record['file'])
    if adapter.sha256_file(p)!=record['sha256']:raise SourceIntegrityError('A003 selected source file altered: '+record['file'])
    xyz=adapter.read_xyz(p,pre['source_resolution'])
    return {'xyz':xyz,'source_sha256':record['sha256'],'source_file':record['file'],
            'polyline_length':adapter.polyline_length(xyz),'seed_id':record['id']}

def evaluate(root:Path,*,compute_volume:bool=True,persist:bool=True):
    from triadic.native_core_v038 import gaussian_vorticity,spectral_helmholtz,cross_sections
    import numpy as np
    root=Path(root)
    pre_path=root/'preregistration'/'A003_V039.json'
    pre=json.loads(pre_path.read_text('utf8'))
    if pre.get('schema')!='A065-A003-CORE-V039-PREREG-1' or pre.get('release')!='v0.3.9' or pre.get('atlas_manifest_sha256')!=ATLAS_MANIFEST_SHA256:
        raise SourceIntegrityError('A065 v0.3.9 preregistration invalid')
    out={'schema':'A065-A003-V039-RESULT-1','release':'v0.3.9',
         'source_class':'FOURIER_GEOMETRIC_SEEDS_ONLY_NOT_NATIVE_EULER',
         'preregistration_sha256':sha(pre_path),'gates':{},'seed_results':[],
         'physical_euler':'UNRESOLVED','physical_casimir':'UNRESOLVED'}
    g=out['gates']
    adapter_path=adapter_root(root)
    if adapter_path is None:
        g['G33']=_record('NOT_RUN_PREREQUISITE','External A003 v0.2.3 adapter folder unavailable',{'expected_dir':'A003_Fourier_Knot_Import_Adapter_v0.2.3'})
        g['G34']=_record('NOT_RUN_PREREQUISITE','A003 adapter unavailable; no atlas can be authenticated')
        g['G35']=_record('NOT_RUN_PREREQUISITE','A003 seed unavailable; cannot fabricate 3D source')
    else:
        a=_load_original_adapter(adapter_path)
        out['adapter']={'root':str(adapter_path),'version':a.ADAPTER_VERSION,'sha256':ADAPTER_SOURCE_SHA256}
        g['G33']=_record('PASS','Original A003 source and release metadata SHA256 verified; no code vendoring',out['adapter'])
        atlas_path=atlas_root(root,adapter_path)
        if atlas_path is None:
            g['G34']=_record('NOT_RUN_PREREQUISITE','Original A003-v0.1.2 atlas not available; adapter ZIP does not contain 384 XYZ assets')
            g['G35']=_record('NOT_RUN_PREREQUISITE','No authenticated original A003 trefoil geometry; no synthetic substitute promoted')
        else:
            # Actual A003 full 384-source audit (including pinned SHA256, resolution,
            # sampling and mirror/projection intentionally omitted for CPU cost).
            registry,report=a.validate_atlas(atlas_path,diagram=False)
            if registry['atlas_manifest_sha256']!=ATLAS_MANIFEST_SHA256 or report['status']!='GEOMETRIC_IMPORT_QUALIFIED' or report['source_records']!=384:
                raise SourceIntegrityError('A003 atlas did not pass complete original adapter audit')
            out['atlas']={'root':str(atlas_path),'manifest_sha256':registry['atlas_manifest_sha256'],
                          'records':report['source_records'],'status':report['status'],
                          'independent_euler_providers':0}
            g['G34']=_record('PASS','Real A003 adapter validated all original atlas records; geometry only',out['atlas'])
            all_rows={ (r['id'],r['sampling'],r['points']):r for r in registry['records']}
            sections_config=json.loads((root/'preregistration'/'SOURCE_NATIVE_CORE_V038.json').read_text('utf8'))
            for seed_id in pre['seeds']:
                key=(seed_id,pre['sampling'],pre['source_resolution'])
                if key not in all_rows:raise SourceIntegrityError('Missing preregistered A003 seed: '+str(key))
                item=_screen_geometry(a,atlas_path,registry,all_rows[key],pre)
                row={k:v for k,v in item.items() if k!='xyz'}
                if compute_volume:
                    xyz=item['xyz'][::pre['core3d_stride']].copy()
                    extent=float(np.max(np.abs(xyz)))
                    L=max(float(pre['box_min_size']), 2.6*extent+4*float(pre['dimensionless_a']))
                    omega=gaussian_vorticity(xyz,n=pre['core3d_grid_n'],L=L,
                                             a=pre['dimensionless_a'],gamma=pre['dimensionless_gamma'])
                    flow=spectral_helmholtz(omega,L)
                    sections=cross_sections(flow['omega'],flow['u'],flow['grad_p'],xyz,L,sections_config)
                    admitted=[s for s in sections if s['section_admissible']]
                    row.update({'grid_n':pre['core3d_grid_n'],'grid_box_length':L,
                                'gaussian_a_assumed_NOT_INFERRED':pre['dimensionless_a'],
                                'geometry_input_nodes':len(xyz),
                                'source_class':'SYNTHETIC_GAUSSIAN_FROM_AUTHENTIC_A003_GEOMETRY',
                                'flow_diagnostics':{k:v for k,v in flow.items() if not isinstance(v,np.ndarray)},
                                'sections':sections,'admissible_sections':len(admitted),
                                'heldout_5pct_pass':bool(admitted) and all(max(s['heldout_velocity_rms_relative'],s['heldout_radial_pressure_gradient_rms_relative'])<pre['holdout_prediction_tolerance'] for s in admitted)})
                    if persist:
                        dest=root/'outputs'/f'A003_V039_{seed_id}_SYNTHETIC_3D.npz';dest.parent.mkdir(exist_ok=True,parents=True)
                        np.savez_compressed(dest,omega=flow['omega'],u=flow['u'],p=flow['p'],dx=np.float64(L/pre['core3d_grid_n']),L=np.float64(L))
                        row['field_npz_sha256']=sha(dest)
                        row['field_npz_path']=str(dest.relative_to(root)).replace('\\','/')
                out['seed_results'].append(row)
            if compute_volume:
                ok=all(x['heldout_5pct_pass'] for x in out['seed_results'])
                g['G35']=_record('PASS' if ok else 'FAIL','Explicit Gaussian synthetic core diagnostics on original A003 3_1 seeds; independent physical targets NOT supplied',
                                 {'num_seeds':len(out['seed_results']),'admitted_sections':{x['seed_id']:x['admissible_sections'] for x in out['seed_results']},
                                  'source_class':'SYNTHETIC_DIAGNOSTIC_ONLY'})
            else:
                g['G35']=_record('UNRESOLVED','3D numerical diagnostic not requested',{'num_geometry_seeds':len(out['seed_results'])},executed='NOT_EXECUTED')
    g['G36']=_record('UNRESOLVED','No independent time-evolved source-native 3D Euler vorticity AND physically independent pressure/velocity holdout. A003 geometric atlas cannot supply them.',
                     {'qualified_euler_sources':0,'a003_geometry_is_not_euler':True})
    if persist:
        dst=root/'outputs'/'A003_V039_RESULT.json';dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf8')
    return out
