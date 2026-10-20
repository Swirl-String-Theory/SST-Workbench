#!/usr/bin/env python3
"""A003 v0.2.7: bounded, framework-1.0.10 GateLedger diagnostics after scientific FAIL.

Important: this is a *framework ledger integration*, not a generated/blind framework
instance, and must not claim framework source freeze or reveal eligibility.
Protocol/source integrity errors are fatal; negative measured invariants are not.
"""
from __future__ import annotations
import argparse, hashlib, importlib, json, os, platform, secrets, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
import numpy as np
from fourier_atlas_adapter import (ADAPTER_ROOT, ADAPTER_VERSION,
    resolve_atlas_root, validate_atlas, read_xyz, safe_atlas_file, sha256_file)
from gates_g4_g5 import bind_physical_scale
from g5_extended import (extended_g5_screen, analytic_braid_screen,
    rotation_for_projection, PROJECTION_ANGLES)
from crossing_trace import crossing_trace
from diagnostic_pdf import render_report
from g5_crossing_tolerance_v027 import scoped_pyknotid_crossing_fix, scoped_pyknotid_python_backend, cutoff_report, ANGULAR_SINE_TOLERANCE

FRAMEWORK_VERSION='1.0.10'
# SHA-256 of the actual v1.0.10 gates.py fetched from the user's SST-Workbench Drive.
PINNED_FRAMEWORK_GATES_SHA256='e5756c90a34d482e3dec7e0e9a22a131f7b8968f5de492832963f3063008a055'
FRAMEWORK_REL=Path('06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10')
FAMILY='fibonacci_torus'
TARGET_SEEDS=('fibonacci_torus_F3','fibonacci_torus_F4')
SCHEMA='sst.a003.framework-1.0.10-diagnostic/1'


def json_write(path:Path,payload:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    # exclusive create protects non-overwriting evidence (run directory itself is unique).
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(payload,f,ensure_ascii=False,indent=2,sort_keys=True,default=str)
        f.write('\n')


def framework_root(cli:Path|None)->Path:
    override=cli or (Path(os.environ['SST_FRAMEWORK_ROOT']) if os.getenv('SST_FRAMEWORK_ROOT') else None)
    if override:return override.expanduser().resolve()
    for base in (ADAPTER_ROOT,*ADAPTER_ROOT.parents):
        path=base / FRAMEWORK_REL
        if path.is_dir():return path.resolve()
    raise RuntimeError('SST Framework v1.0.10 not found: set SST_FRAMEWORK_ROOT or --framework-root')


def load_framework(cli:Path|None):
    """Only exact directory/release version accepted; no unrelated PYTHONPATH fallback."""
    root=framework_root(cli)
    meta_path=root/'RELEASE_INFO.json'
    if not meta_path.is_file():raise RuntimeError('framework RELEASE_INFO.json missing')
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    if meta.get('version')!=FRAMEWORK_VERSION or meta.get('name')!='SST_Falsifier_Framework':
        raise RuntimeError('framework identity/version mismatch: expected SST_Falsifier_Framework/1.0.10')
    gates=root/'sst_falsifier'/'gates.py'
    if not gates.is_file():raise RuntimeError('framework GateLedger source missing')
    actual_gates_hash=sha256_file(gates)
    if actual_gates_hash!=PINNED_FRAMEWORK_GATES_SHA256:
        raise RuntimeError('framework gates.py SHA256 differs from reviewed v1.0.10 source; refuse unverified pin')
    # Avoid importing different already-installed framework.
    existing=sys.modules.get('sst_falsifier')
    if existing is not None:
        loc=Path(existing.__file__).resolve()
        if not loc.is_relative_to(root):
            raise RuntimeError(f'wrong framework already imported: {loc}')
    sys.path.insert(0,str(root))
    mod=importlib.import_module('sst_falsifier.gates')
    if Path(mod.__file__).resolve()!=gates.resolve() or not all(hasattr(mod,s) for s in
       ('GateDefinition','GateLedger','GateInputsUnavailable')):
        raise RuntimeError('pinned framework GateLedger API mismatch')
    return root,meta,mod,sha256_file(gates)


def gate_definitions(mod):
    D=mod.GateDefinition
    return [
        D('G0','Pinned atlas source and all SHA-256 inputs are admissible'),
        D('G1','384 XYZ import structure and sampling levels are valid',('G0',)),
        D('G2','Geometric projection mirror diagnostic agrees',('G0',)),
        D('G3','BASIC/FULL geometry converges at frozen thresholds',('G1',)),
        D('G4','Explicit conditional scale maps source units to meters',('G1',)),
        D('G5a','Independent XYZ Alexander-polynomial screen',('G0','G1')),
        D('G5b','Signed degree-three invariant and mirror diagnostic',('G5a',)),
        D('G5c','Analytic torus braid references (NOT independent XYZ topology)',('G0',)),
        D('G5d','Frozen-primary projection/resolution invariance',('G5a','G5b')),
        D('G5e','Independent raw crossing/Gauss/Wirtinger determinant trace',('G5a',)),
        D('G5f','Cross-check stock provider determinant against independent raw diagram',('G5a','G5e')),
    D('G5g','Recompute bounded G5 using scoped angular crossing correction',('G5a','G5e')),
    D('G5h','Paired stock/corrected comparison with fixed F3 regression',('G5a','G5g','G5e')),
    D('G5i','Direct first-bad-crossing absolute versus angular cutoff',('G5a','G5e')),
        D('G6','PKLSA Euler/finite-core vortex dynamics (not implemented)',('G0','G1','G5a')),
    ]


def status_extended(subgate:str, ext:dict)->tuple[str,str]:
    if ext.get('status')=='PROVIDER_UNAVAILABLE':return 'UNRESOLVED','Provider unavailable'
    if subgate=='G5a':
        if ext.get('status')=='FAIL_INVARIANT_SCREEN' or any(
            r.get('G5a_polynomial')=='MISMATCH' for r in ext.get('seed_results',[])):
            return 'FAIL','At least one primary Alexander invariant mismatch'
        if ext.get('subgates',{}).get('G5a')=='PASS_SCREEN_NOT_CERTIFIED':
            return 'PASS','Tested bounded polynomial screen matched (not knot classification)'
        return 'UNRESOLVED','Polynomial screen incomplete, skipped or provider failed'
    if subgate=='G5b':
        v=ext.get('subgates',{}).get('G5b')
        if v=='PASS_MIRROR_DIAGNOSTIC_ONLY':return 'PASS','Nonzero mirror-odd v3 diagnostic only'
        if any(x.get('G5b_mirror_odd')=='FAIL_MIRROR_ODD_RELATION' for x in ext.get('seed_results',[])):
            return 'FAIL','v3 reflection-odd identity violated'
        return 'UNRESOLVED','No stable nonzero chirality witness across primary cases'
    if subgate=='G5d':
        if any(x.get('G5d_projection_resolution')=='FAIL' for x in ext.get('seed_results',[])):
            return 'FAIL','Frozen-primary projection/mesh disagreement (extra projections cannot rescue)'
        if ext.get('subgates',{}).get('G5d')=='PASS_TESTED_CASES_ONLY':
            return 'PASS','Tested primary projection/mesh cases stable only'
        return 'UNRESOLVED','Unrun or incomplete projection/mesh witnesses'
    raise ValueError(subgate)


def run_diagnostic(*, atlas:Path, root:Path, out_root:Path,
                   run_provider:bool=True, geometry_provider:Callable|None=None,
                   max_crossings:int=12, replay_extended:dict|None=None,
                   run_corrected:bool=True, corrected_provider:Callable|None=None)->tuple[int,Path,dict]:
    fw,meta,mod,gate_hash=load_framework(root)
    # Security/provenance preflight is fail-closed. It must not be downgraded to
    # diagnostic scientific FAIL nor run with missing/mutated source files.
    registry,report=validate_atlas(atlas)
    g4=bind_physical_scale(registry,report,assumed_core_radius_units=0.05)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'_'+secrets.token_hex(5)
    out_root.mkdir(parents=True,exist_ok=True)
    run_dir=out_root/run_id;run_dir.mkdir(exist_ok=False)
    selected={'records':[r for r in registry['records'] if r['family']==FAMILY]}
    ledger=mod.GateLedger(gate_definitions(mod),strict_dependencies=False)
    cache={}

    def e_geometry():
        status=report.get('gate_results',{})
        return {k:('PASS' if status.get(k)=='PASS' else 'UNRESOLVED') for k in
                ('G0_MANIFEST_SCHEMA','G1_HASH_AND_XYZ','G2_GEOMETRIC_MIRROR_DIAGNOSTIC','G3_SAMPLING_CONVERGENCE')}

    geom=e_geometry()
    def e_ext():
        if 'extended' not in cache:
            if replay_extended is not None:
                cache['extended']=replay_extended
            elif not run_provider:
                cache['extended']={'status':'PROVIDER_NOT_RUN','subgates':{},'seed_results':[],
                    'reason':'--skip-provider explicitly selected', 'scientific_status':'NOT_CERTIFIED'}
            else:
                if geometry_provider is not None:
                    cache['extended']=extended_g5_screen(selected,report,atlas,enabled=True,
                        sampling='uniform_t',resolutions=(1200,2400),max_crossings=max_crossings,
                        geometry_provider=geometry_provider,projection_diagnostics=True)
                else:
                    from gates_g4_g5 import _pyknotid_numpy_legacy_compatibility
                    from importlib.metadata import PackageNotFoundError
                    try:
                        with _pyknotid_numpy_legacy_compatibility():
                            with scoped_pyknotid_python_backend() as stock_meta:
                                cache['extended']=extended_g5_screen(selected,report,atlas,enabled=True,
                                    sampling='uniform_t',resolutions=(1200,2400),max_crossings=max_crossings,
                                    projection_diagnostics=True)
                        cache['stock_dispatch']=stock_meta
                    except (ImportError,PackageNotFoundError) as ex:
                        cache['extended']={'status':'PROVIDER_UNAVAILABLE','error':str(ex),
                                            'seed_results':[],'subgates':{},'provider':'none'}
            json_write(run_dir/'g5_provider_observations.json',cache['extended'])
        return cache['extended']

    def e_a():
        status,reason=status_extended('G5a',e_ext()) if run_provider or replay_extended is not None else ('UNRESOLVED','Provider intentionally not run')
        return {'status':status,'reason':reason,'metrics':{'extended_status':e_ext().get('status')}}
    def e_b():
        status,reason=status_extended('G5b',e_ext()) if run_provider or replay_extended is not None else ('UNRESOLVED','Provider intentionally not run')
        return {'status':status,'reason':reason}
    def e_c():
        refs=[{'id':rec['id'],**analytic_braid_screen(rec)} for rec in
              sorted((r for r in selected['records'] if r['sampling']=='uniform_t' and r['points']==1200),key=lambda r:r['id'])]
        json_write(run_dir/'g5c_references.json',{'references':refs,'scientific_limit':'source-declared p,q only'})
        ok=bool(refs) and all(r['status']=='PASS_BRAID_REFERENCE_ONLY' for r in refs)
        return {'status':'PASS' if ok else 'FAIL','reason':'Reference algebra only; does not identify XYZ topology',
                'metrics':{'checked_references':len(refs),'geometrically_independent':False}}
    def e_d():
        status,reason=status_extended('G5d',e_ext()) if run_provider or replay_extended is not None else ('UNRESOLVED','Provider intentionally not run')
        return {'status':status,'reason':reason}
    def e_crossings():
        rows=[]
        for seed in TARGET_SEEDS:
            for n in (1200,2400):
                name=f'xyz/{seed}_uniform_t_N{n}.xyz'
                rec=next((r for r in selected['records'] if r['file']==name),None)
                if rec is None:raise RuntimeError('pinned seed missing from verified source registry')
                src=safe_atlas_file(atlas,name)
                if sha256_file(src)!=rec['sha256']:raise RuntimeError('post-audit source mutation')
                pts=read_xyz(src,n)
                for projection in (0,1):
                    q=pts@rotation_for_projection(projection).T
                    tr=crossing_trace(q)
                    json_write(run_dir/f'raw_crossings_{seed}_N{n}_P{projection}.json',tr)
                    rows.append({'id':seed,'N':n,'projection':projection,
                        'crossing_count':tr['crossing_count'],'ambiguous_count':sum(c['over']=='ambiguous' for c in tr['crossings']),
                        'nearly_degenerate_crossings':tr['nearly_degenerate_crossings'],
                        'diagram_determinant':tr['diagram_determinant']['value'],
                        'trace_file':f'raw_crossings_{seed}_N{n}_P{projection}.json'})
        cache['crossing_rows']=rows
        json_write(run_dir/'g5e_raw_crossing_summary.json',{'schema':'sst.a003.g5e/1','cases':rows,
                'scientific_limit':'diagram coloring determinant is not full Alexander polynomial or isotopy certification'})
        good=all(row['ambiguous_count']==0 and row['nearly_degenerate_crossings']==0 and
                 row['diagram_determinant']==(3 if row['id'].endswith('F3') else 1) for row in rows)
        return {'status':'PASS' if good else 'FAIL','reason':'Exact integer diagram determinant at t=-1; no pyknotid',
                'metrics':{'cases':len(rows),'all_expected_determinants_match':good}}
    def e_compare():
        observed={(r['id'],x['N'],x['projection']):x for r in e_ext().get('seed_results',[])
                  for x in r.get('observations',[]) if x.get('mirror') is False}
        if not observed:
            return {'status':'UNRESOLVED','reason':'No pyknotid primary observations available for comparison'}
        comparisons=[]
        for x in cache['crossing_rows']:
            got=observed.get((x['id'],x['N'],x['projection']))
            if not got:
                comparisons.append({**x,'status':'UNRESOLVED_PROVIDER_CASE_MISSING'})
            else:
                determinant=abs(sum(c*((-1)**i) for i,c in enumerate(got['alexander_coefficients'])))
                matched=determinant==x['diagram_determinant']
                comparisons.append({**x,'provider_alexander_coefficients':got['alexander_coefficients'],
                    'provider_determinant':determinant,'match':matched,
                    'status':'MATCH' if matched else 'MISMATCH'})
        json_write(run_dir/'g5f_provider_diagram_comparison.json',{'schema':'sst.a003.g5f/1','comparisons':comparisons})
        if any(c['status']=='MISMATCH' for c in comparisons):status='FAIL'
        elif any(c['status']=='UNRESOLVED_PROVIDER_CASE_MISSING' for c in comparisons):status='UNRESOLVED'
        else:status='PASS'
        return {'status':status,'reason':'Independent diagram determinant vs provider polynomial at t=-1',
                'metrics':{'compared':sum('match' in x for x in comparisons),'mismatches':sum(x['status']=='MISMATCH' for x in comparisons)}}

    def e_corrected():
        if not run_provider or replay_extended is not None or not run_corrected:
            cache['corrected']={'status':'NOT_RUN','reason':'replay, skip-provider or explicit skip-corrected; no new provider evidence'}
            json_write(run_dir/'g5_corrected_provider_observations.json',cache['corrected'])
            return {'status':'UNRESOLVED','reason':'Corrected provider not executed; replay cannot qualify new evidence'}
        if 'corrected' not in cache:
            if corrected_provider is not None:
                # Used ONLY by unit/integration tests; distinguish a test-double from real provider.
                ext=extended_g5_screen(selected,report,atlas,enabled=True,sampling='uniform_t',
                      resolutions=(1200,2400),max_crossings=max_crossings,
                      geometry_provider=corrected_provider,projection_diagnostics=True)
                patch_meta={'provider_kind':'TEST_DOUBLE_NO_SCIENTIFIC_EVIDENCE'}
            else:
                from gates_g4_g5 import _pyknotid_numpy_legacy_compatibility
                from importlib.metadata import PackageNotFoundError
                try:
                    with _pyknotid_numpy_legacy_compatibility():
                        with scoped_pyknotid_crossing_fix() as patch_meta:
                            ext=extended_g5_screen(selected,report,atlas,enabled=True,
                                  sampling='uniform_t',resolutions=(1200,2400),
                                  max_crossings=max_crossings,projection_diagnostics=True)
                except (ImportError,PackageNotFoundError) as ex:
                    ext={'status':'PROVIDER_UNAVAILABLE','error':str(ex),
                         'seed_results':[],'subgates':{},'provider':'none'}
                    patch_meta={'provider_kind':'NOT_AVAILABLE'}
                # Framework should receive the original exception for a bad patch/environment;
                # provider errors inside G5 become UNRESOLVED observations, not fake PASS.
            cache['corrected']=ext
            cache['patch_metadata']=patch_meta
            json_write(run_dir/'g5_corrected_provider_observations.json',
                       {'patch_metadata':patch_meta,'observation':ext,
                        'scientific_limit':'bounded provider correction, not full knot/chirality certification'})
        ext=cache['corrected']
        status,reason=status_extended('G5a',ext)
        if ext.get('provider')=='test-double':
            return {'status':'UNRESOLVED','reason':'Test-double correction cannot serve as scientific provider evidence'}
        checked={x['id']:x for x in ext.get('seed_results',[]) if x.get('observations')}
        if not all(x in checked for x in TARGET_SEEDS):
            return {'status':'UNRESOLVED','reason':'Missing bounded F3/F4 corrected provider observations'}
        if status=='PASS':
            for sid in TARGET_SEEDS:
                row=checked[sid]
                if (row.get('G5a_polynomial')!='MATCH' or
                    row.get('G5d_projection_resolution')!='PASS' or
                    row.get('G5b_mirror_odd')!='PASS_NONZERO_MIRROR_ODD_DIAGNOSTIC_ONLY'):
                    return {'status':'FAIL','reason':f'Corrected case {sid} incomplete or contradictory'}
        return {'status':status,'reason':reason+'; only bounded F3/F4, not topology certified',
                'metrics':{'corrected_extended_status':ext.get('status'),
                           'bounded_provider_seeds':list(checked),'scope_restored':True}}

    def e_paired():
        original=e_ext()
        corrected=cache.get('corrected',{})
        def rows(ext):
            return {(r['id'],x['N'],x['projection'],x['mirror']):x for r in ext.get('seed_results',[])
                    for x in r.get('observations',[])}
        st,fx=rows(original),rows(corrected)
        details=[]
        for sid in TARGET_SEEDS:
            for n in (1200,2400):
                for proj in (0,1):
                    for mirror in (False,True):
                        key=(sid,n,proj,mirror)
                        s=st.get(key);f=fx.get(key)
                        if s is None or f is None:
                            details.append({'seed':sid,'N':n,'projection':proj,'mirror':mirror,'status':'UNRESOLVED'})
                            continue
                        sdet=abs(sum(c*(-1)**i for i,c in enumerate(s['alexander_coefficients'])))
                        fdet=abs(sum(c*(-1)**i for i,c in enumerate(f['alexander_coefficients'])))
                        details.append({'seed':sid,'N':n,'projection':proj,'mirror':mirror,
                            'stock_det':sdet,'corrected_det':fdet,
                            'stock_v3':s['vassiliev_3'],'corrected_v3':f['vassiliev_3'],
                            'status':'MATCH' if s==f else 'CHANGED'})
        anomalous=[r for r in details if r['seed']=='fibonacci_torus_F3' and
                   r['N']==2400 and r['projection']==1 and not r['mirror']]
        target=anomalous[0] if anomalous else {}
        fixed_expected=(target.get('stock_det')==1 and target.get('corrected_det')==3 and
                        target.get('corrected_v3')==-1)
        unchanged=[r for r in details if r.get('status') not in ('UNRESOLVED',) and
            not (r['seed']=='fibonacci_torus_F3' and r['N']==2400 and r['projection']==1)]
        # Both normal and mirror of the failure may change: do not require only the
        # direct target to change, but require every other case to be stable.
        unchanged_good=all(r['status']=='MATCH' for r in unchanged)
        full=len(details)==16 and all(r['status']!='UNRESOLVED' for r in details)
        candidate_pass=bool(fixed_expected and unchanged_good and full)
        json_write(run_dir/'g5h_stock_corrected_comparison.json',{
            'schema':'sst.a003.g5h.paired/1', 'cases':details,
            'f3_N2400_P1_fix_match':fixed_expected,'other_primary_cases_unchanged':unchanged_good,
            'all_primary_observations_present':full,
            'scientific_limit':'A provider software correction does NOT alone certify knot topology or chirality'})
        if not full or corrected_provider is not None or target.get('stock_det')!=1:
            status='UNRESOLVED'
        elif candidate_pass:
            status='PASS'
        else:
            status='FAIL'
        return {'status':status,'reason':'Measured stock/corrected provider comparison (F3 frozen issue)',
                'metrics':{'f3_stock_to_fixed_1_to_3':fixed_expected,
                           'other_cases_stable':unchanged_good,'all_cases_present':full}}

    def e_numeric_cutoff():
        rows=[]
        expected_pairs={1200:(65,1041),2400:(131,2083)}
        for n,(i,j) in expected_pairs.items():
            name=f'xyz/fibonacci_torus_F3_uniform_t_N{n}.xyz'
            rec=next(r for r in selected['records'] if r['file']==name)
            src=safe_atlas_file(atlas,name)
            if sha256_file(src)!=rec['sha256']:
                raise RuntimeError('historical F3 numerical probe hash mismatch')
            q=read_xyz(src,n)@rotation_for_projection(1).T
            u=q[i+1,:2]-q[i,:2]
            v=q[(j+1)%n,:2]-q[j,:2]
            rows.append({'N':n,'edges':[i,j],**cutoff_report(u,v)})
        valid=(len(rows)==2 and
               not rows[0]['stock_guard_rejects'] and rows[1]['stock_guard_rejects'] and
               all(not row['corrected_guard_rejects'] for row in rows) and
               all(row['normalized_abs_sin']>0.2 for row in rows))
        json_write(run_dir/'g5i_numeric_guard_evidence.json',{'schema':'sst.a003.g5i.numeric-guard/1',
            'cases':rows,'angular_sine_tolerance':ANGULAR_SINE_TOLERANCE,
            'source_mutated':False,'numerical_control_only':True,'gate_pass':valid})
        return {'status':'PASS' if valid else 'FAIL','reason':'Frozen F3 P1 edge crossing threshold control; no provider inference',
                'metrics':{'original_rejects_at_2400':rows[1]['stock_guard_rejects'],
                           'fixed_accepts_at_2400':not rows[1]['corrected_guard_rejects']}}

    gr=report['gate_results']
    ev={
      'G0':lambda:{'status':'PASS' if geom['G0_MANIFEST_SCHEMA']=='PASS' else 'UNRESOLVED','metrics':{'atlas_manifest_sha256':sha256_file(atlas/'manifest.json')}},
      'G1':lambda:{'status':'PASS' if geom['G1_HASH_AND_XYZ']=='PASS' else 'UNRESOLVED','metrics':{'XYZ':report['source_records']}},
      'G2':lambda:{'status':'PASS' if geom['G2_GEOMETRIC_MIRROR_DIAGNOSTIC']=='PASS' else 'UNRESOLVED'},
      'G3':lambda:{'status':'PASS' if geom['G3_SAMPLING_CONVERGENCE']=='PASS' else 'UNRESOLVED'},
      'G4':lambda:{'status':'PASS' if g4['status']=='PASS_DIMENSIONAL_HYPOTHESIS_ONLY' else 'UNRESOLVED',
          'reason':'ASSUMED core radius; PASS is dimensional consistency only',
          'metrics':{'meters_per_atlas_unit':g4.get('meters_per_atlas_unit'),'physics_certified':False}},
      'G5a':e_a,'G5b':e_b,'G5c':e_c,'G5d':e_d,'G5e':e_crossings,'G5f':e_compare,'G5g':e_corrected,'G5h':e_paired,'G5i':e_numeric_cutoff,
      # No G6 evaluator: framework explicitly records UNRESOLVED / NOT_EXECUTED.
    }
    # Framework 1.0.10 executes G5e/G5f even when G5a FAIL.
    ledger.run_evaluators(ev)
    ledger_data=ledger.to_dict()
    json_write(run_dir/'GATE_LEDGER.json',ledger_data)
    failed=[r['gate_id'] for r in ledger_data['records'] if r['status']=='FAIL']
    unresolved=[r['gate_id'] for r in ledger_data['records'] if r['status']=='UNRESOLVED']
    summary={'schema':SCHEMA,'adapter_version':ADAPTER_VERSION,'framework':{
        'version':FRAMEWORK_VERSION,'release_status':meta.get('status'),
        'framework_root':str(fw),'gates_py_sha256':gate_hash,
        'integration_level':'GateLedger.run_evaluators; NOT a generated framework instance or blind/reveal certification'},
       'atlas_version':'v0.1.2','atlas_manifest_sha256':sha256_file(atlas/'manifest.json'),
       'run_id':run_id,'created_utc':datetime.now(timezone.utc).isoformat(),
       'sciences':{'g0_g3':'PASS','g4':'PASS_DIMENSIONAL_HYPOTHESIS_ONLY','g5':'NOT_CERTIFIED','g6':'NOT_RUN'},
       'failed_gates':failed,'unresolved_gates':unresolved,
       'diagnostics_continued_after_fail':bool(failed and any(r['gate_id']=='G5e' and r['execution_status']=='EXECUTED' for r in ledger_data['records'])),
       'final_scientific_status':'FAIL_UNQUALIFIED' if failed else 'UNRESOLVED_NOT_CERTIFIED',
       'exit_code':2 if failed else 3,'version_pin_actual':True,
       'unsafe_claims_disabled':True,'reveal_performed':False,'pklsa_euler_run':False,
       'crossing_correction_mode':'STOCK_AND_SCOPED_FIXED' if run_provider and run_corrected and replay_extended is None else 'NOT_EXECUTED',
       'corrected_provider_status':cache.get('corrected',{}).get('status','NOT_RUN'),
       'stock_crossing_backend':cache.get('stock_dispatch',{}).get('backend','REPLAY_OR_TEST_DOUBLE'),
       'provider_observations_origin':'HISTORICAL_REPLAY_NOT_NEW_EVIDENCE' if replay_extended is not None else
           'LIVE_PROVIDER' if run_provider else 'PROVIDER_SKIPPED'}
    json_write(run_dir/'DIAGNOSTIC_RUN_SUMMARY.json',summary)
    lines=['# A003 v0.2.7 — framework 1.0.10 diagnostic execution','',
        f'- Run ID: `{run_id}`',f'- Framework: `{FRAMEWORK_VERSION}` ({meta.get("status")})',
        '- G5 independent topological certification: **NOT CERTIFIED**',
        '- G6/PKLSA: **NOT RUN**','',
        '| Gate | Measured status | Execution | Scientific qualification | Blocked by |',
        '|---|---|---|---|---|']
    for row in ledger_data['records']:
        lines.append(f"| {row['gate_id']} | {row['status']} | {row['execution_status']} | {row['qualification']} | {', '.join(row['blocked_by']) or '—'} |")
    lines+=['','Scientific negative findings remain negative; diagnostics continue without promoting downstream claims.',
            'The raw crossing detector is independent of pyknotid but is not a complete knot invariant.']
    (run_dir/'DIAGNOSTIC_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    pdf_status=render_report(run_dir,ledger_data,summary)
    json_write(run_dir/'PDF_RENDER.json',pdf_status)
    # Failure always visible to caller. Do not mask a scientific FAIL with a successful diagnostic run.
    return summary['exit_code'],run_dir,summary


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas',type=Path,default=None)
    p.add_argument('--framework-root',type=Path,default=None)
    p.add_argument('--out-root',type=Path,default=ADAPTER_ROOT.parent/(ADAPTER_ROOT.name+'-outputs'))
    p.add_argument('--skip-corrected',action='store_true',help='run stock route only; record corrected G5 as UNRESOLVED')
    p.add_argument('--skip-provider',action='store_true',help='diagnostic geometry-only smoke; reports G5 UNRESOLVED')
    p.add_argument('--max-crossings',type=int,default=12)
    p.add_argument('--replay-v025',action='store_true',help='replay user-supplied v0.2.5 observed G5 FAIL, never claim a new measurement')
    args=p.parse_args(argv)
    try:
        atlas=resolve_atlas_root(args.atlas)
        if args.replay_v025 and args.skip_provider:
            p.error('--replay-v025 and --skip-provider are mutually exclusive')
        replay=None
        if args.replay_v025:
            fixture=ADAPTER_ROOT/'tests'/'fixtures'/'g5_v025_extended_replay.json'
            historic=json.loads(fixture.read_text(encoding='utf-8'))
            if (historic.get('source_adapter_version')!='0.2.5' or
                    historic.get('atlas_manifest_sha256')!=sha256_file(atlas/'manifest.json')):
                raise RuntimeError('frozen historical G5 replay and atlas hash disagree')
            replay=historic['extended_g5_screen']
        rc,run_dir,summary=run_diagnostic(atlas=atlas,root=args.framework_root,out_root=args.out_root,
                               run_provider=not args.skip_provider,max_crossings=args.max_crossings,
                               replay_extended=replay,run_corrected=not args.skip_corrected)
        print(json.dumps({'run_dir':str(run_dir),'exit_code':rc,'failed_gates':summary['failed_gates'],
                'unresolved_gates':summary['unresolved_gates'],
                'diagnostics_continued_after_fail':summary['diagnostics_continued_after_fail']},indent=2))
        return rc
    except Exception as exc:
        # Programmer exceptions are fatal and not recorded as a scientific FAIL.
        print(f'FATAL_INTEGRITY_OR_EXECUTION_ERROR: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 4

if __name__=='__main__':raise SystemExit(main())
