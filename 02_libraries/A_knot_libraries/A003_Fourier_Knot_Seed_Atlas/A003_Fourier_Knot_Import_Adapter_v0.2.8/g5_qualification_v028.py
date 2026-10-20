#!/usr/bin/env python3
"""A003 v0.2.8.1: independent bounded F3/F4 corrected G5 4-resolution campaign.

Only measured corrected-provider observations can pass G5Q1..Q4. Historical v0.2.7
outputs are reference regression data, never substituted for live measurements.
Uses exact-source-pinned SST Falsifier Framework v1.0.10 GateLedger; NOT a full
preregistered, blind or reveal-authoritative framework instance.
"""
from __future__ import annotations
import argparse, hashlib, json, os, secrets, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
import numpy as np
from fourier_atlas_adapter import (ADAPTER_ROOT, ADAPTER_VERSION, resolve_atlas_root,
    validate_atlas, read_xyz, safe_atlas_file, sha256_file)
from a003_diagnostic_v027 import load_framework, json_write
from g5_extended import extended_g5_screen, PROJECTION_ANGLES, known_polynomial_reference, rotation_for_projection
from g5_crossing_tolerance_v027 import scoped_pyknotid_crossing_fix, cutoff_report
from crossing_trace import crossing_trace
from report_v028 import render_qualification_report

TARGET_SEEDS=('fibonacci_torus_F3','fibonacci_torus_F4')
RESOLUTIONS=(1200,2400,4800,9600)
PROJECTIONS=(0,1)
MIRRORS=(False,True)
EXPECTED_TOTAL=32
FIXTURE=ADAPTER_ROOT/'tests'/'fixtures'/'g5_v027_live_corrected_lowres.json'
FIXTURE_SHA256='a1281aa88252cd3d8afb09bf81a5c060a6c05da6540900ca0084b352e46db164'
SCHEMA='sst.a003.corrected-g5-qualification/1'


def key(x):
    return (x['id'],int(x['N']),int(x['projection']),bool(x['mirror']))


def expected_keys(ns=RESOLUTIONS):
    return {(sid,n,p,m) for sid in TARGET_SEEDS for n in ns for p in PROJECTIONS for m in MIRRORS}


def obs_map(rows):
    out={}
    for x in rows:
        k=key(x)
        if k in out:raise ValueError(f'duplicate provider observation {k}')
        out[k]=x
    return out


def flatten(ext):
    return [{**x,'id':seed['id']} for seed in ext.get('seed_results',[])
            if seed['id'] in TARGET_SEEDS for x in seed.get('observations',[])]


def fixture_read():
    if sha256_file(FIXTURE)!=FIXTURE_SHA256:
        raise RuntimeError('v0.2.7 historical low-resolution fixture modified')
    d=json.loads(FIXTURE.read_text(encoding='utf-8'))
    if (d.get('schema')!='sst.a003.g5.corrected-baseline/1' or
        d.get('origin')!='USER_V027_LIVE_PROVIDER_CORRECTED_2026_10_19'):
        raise RuntimeError('historical corrected baseline provenance invalid')
    ref=obs_map(d['observations'])
    if set(ref)!=expected_keys((1200,2400)):
        raise RuntimeError('incomplete historical corrected low-resolution fixture')
    return d,ref


def validate_observations(ext):
    if ext.get('provider') != 'pyknotid':
        return {'status':'UNRESOLVED','reason':'No real pyKnotID provider evidence', 'observations':0}
    try:
        rows=obs_map(flatten(ext))
    except (TypeError,KeyError,ValueError) as exc:
        return {'status':'FAIL','reason':str(exc),'observations':0}
    missing=expected_keys()-set(rows)
    extra=set(rows)-expected_keys()
    if extra or missing:
        return {'status':'UNRESOLVED','reason':'Missing/unexpected provider observations',
                'missing':[list(v) for v in sorted(missing)],'extra':[list(v) for v in sorted(extra)],
                'observations':len(rows)}
    if ext.get('status')=='FAIL_INVARIANT_SCREEN':
        return {'status':'FAIL','reason':'Provider reports invariant mismatch','observations':len(rows)}
    if any(row.get('status')=='PROVIDER_ERROR_UNRESOLVED' for row in ext.get('seed_results',[])):
        return {'status':'UNRESOLVED','reason':'Provider failed on one or more cases','observations':len(rows)}
    return {'status':'PASS','reason':'32 fresh corrected provider observations complete','observations':len(rows)}


def compare_reference(rows, reference, ns):
    comparisons=[]
    for sid,n,projection,mirror in sorted(expected_keys(ns)):
        current=rows.get((sid,n,projection,mirror))
        ref=reference.get((sid,n if n in (1200,2400) else 2400,projection,mirror))
        if ref is None or current is None:
            comparisons.append({'id':sid,'N':n,'projection':projection,'mirror':mirror,
                                'status':'UNRESOLVED','reason':'Missing observed or reference case'})
            continue
        same= (current['alexander_coefficients']==ref['alexander_coefficients'] and
               current['vassiliev_3']==ref['vassiliev_3'])
        comparisons.append({'id':sid,'N':n,'projection':projection,'mirror':mirror,
                            'status':'MATCH' if same else 'MISMATCH',
                            'reference_alexander':ref['alexander_coefficients'],
                            'observed_alexander':current['alexander_coefficients'],
                            'reference_v3':ref['vassiliev_3'],'observed_v3':current['vassiliev_3']})
    state='FAIL' if any(v['status']=='MISMATCH' for v in comparisons) else \
          'UNRESOLVED' if any(v['status']=='UNRESOLVED' for v in comparisons) else 'PASS'
    return {'status':state,'comparisons':comparisons,'matched':sum(x['status']=='MATCH' for x in comparisons),
            'total':len(comparisons)}


def check_four_level_symmetry(rows, registry):
    checks=[]
    for sid in TARGET_SEEDS:
        rec=next(r for r in registry['records'] if r['id']==sid and r['points']==1200 and r['sampling']=='uniform_t')
        expected=known_polynomial_reference(rec)
        expected_v3=next(rows[k]['vassiliev_3'] for k in sorted(rows) if k[0]==sid and k[1]==1200 and k[2]==0 and not k[3])
        for n in RESOLUTIONS:
            for proj in PROJECTIONS:
                o=rows.get((sid,n,proj,False)); m=rows.get((sid,n,proj,True))
                if not o or not m:
                    checks.append({'id':sid,'N':n,'projection':proj,'status':'UNRESOLVED'})
                    continue
                condition=(o['alexander_coefficients']==expected and m['alexander_coefficients']==expected and
                           o['vassiliev_3']==expected_v3 and m['vassiliev_3']==-expected_v3 and
                           expected_v3!=0)
                checks.append({'id':sid,'N':n,'projection':proj,'status':'PASS' if condition else 'FAIL',
                               'expected_v3':expected_v3,'observed_v3':o['vassiliev_3'],
                               'mirror_v3':m['vassiliev_3']})
    result='FAIL' if any(x['status']=='FAIL' for x in checks) else \
           'UNRESOLVED' if any(x['status']=='UNRESOLVED' for x in checks) else 'PASS'
    return {'status':result,'checks':checks}


def source_guard_geometry(atlas,registry):
    """Fast source-derived angular check at all four resolutions, both seeds, P1.

    Check smallest |sin| of independent crossing-like candidate edges from
    the existing independent detector only at the historical failing pair.
    This guards the exact fixed crossing and emits no topological certification.
    """
    rows=[]
    # Pre-registered candidate edges at the historical F3 P1 crossing.
    historic={1200:(65,1041),2400:(131,2083)}
    for n,(i,j) in historic.items():
        name=f'xyz/fibonacci_torus_F3_uniform_t_N{n}.xyz'
        rec=next(r for r in registry['records'] if r['file']==name)
        src=safe_atlas_file(atlas,name)
        if sha256_file(src)!=rec['sha256']:raise RuntimeError('F3 source mutated during qualification')
        pts=read_xyz(src,n)@rotation_for_projection(1).T
        check=cutoff_report(pts[i+1,:2]-pts[i,:2],pts[(j+1)%n,:2]-pts[j,:2])
        rows.append({'N':n,'candidate_edges':[i,j],**check})
    good=(not rows[0]['stock_guard_rejects'] and rows[1]['stock_guard_rejects'] and
          all(not x['corrected_guard_rejects'] for x in rows))
    return {'status':'PASS' if good else 'FAIL','cases':rows,
            'high_resolution_claim':'NOT_RUN; historical pair only; four-resolution evidence is provider-based'}


def run_campaign(*,atlas:Path,framework:Path|None,out_root:Path,run_provider=True,
                 geometry_provider:Callable|None=None, max_crossings=12):
    fw,fw_meta,mod,gates_sha=load_framework(framework)
    registry,report=validate_atlas(atlas)  # fail-closed all 384 manifest entries
    hist,ref=fixture_read()
    selected={'records':[r for r in registry['records'] if r['id'] in TARGET_SEEDS]}
    expected_files=expected_keys()
    src_set={(r['id'],r['points'],r['sampling']) for r in selected['records']}
    if not all((sid,n,'uniform_t') in src_set for sid in TARGET_SEEDS for n in RESOLUTIONS):
        raise RuntimeError('missing required N=1200/2400/4800/9600 XYZ source')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'_'+secrets.token_hex(5)
    out_root.mkdir(parents=True,exist_ok=True)
    run_dir=out_root/run_id;run_dir.mkdir(exist_ok=False)
    cache={}

    def provider_observation():
        if 'provider' not in cache:
            patch={'provider_kind':'NOT_RUN'}
            if not run_provider:
                ext={'status':'NOT_RUN','provider':'none','seed_results':[], 'reason':'--skip-provider: no new evidence'}
            elif geometry_provider is not None:
                ext=extended_g5_screen(selected,report,atlas,enabled=True,sampling='uniform_t',
                    resolutions=RESOLUTIONS,max_crossings=max_crossings,
                    geometry_provider=geometry_provider,projection_diagnostics=False)
                patch={'provider_kind':'TEST_DOUBLE_NOT_SCIENTIFIC_EVIDENCE'}
            else:
                from gates_g4_g5 import _pyknotid_numpy_legacy_compatibility
                from importlib.metadata import PackageNotFoundError
                try:
                    with _pyknotid_numpy_legacy_compatibility():
                        with scoped_pyknotid_crossing_fix() as patch:
                            ext=extended_g5_screen(selected,report,atlas,enabled=True,
                                sampling='uniform_t',resolutions=RESOLUTIONS,
                                max_crossings=max_crossings,projection_diagnostics=False)
                except (ImportError,PackageNotFoundError) as exc:
                    ext={'status':'PROVIDER_UNAVAILABLE','provider':'none','seed_results':[], 'error':str(exc)}
                    patch={'provider_kind':'NOT_INSTALLED'}
            cache['provider']=ext;cache['patch']=patch
            json_write(run_dir/'g5_corrected_four_resolutions.json',{
                'schema':'sst.a003.g5.v028.live-provider/1','observation':ext,'patch_metadata':patch,
                'expected_cases':EXPECTED_TOTAL,'scientific_limit':'4-resolution invariant screen; not complete topological or physics certification'})
        return cache['provider']

    def validate_provider():
        ext=provider_observation()
        if geometry_provider is not None:
            return {'status':'UNRESOLVED','reason':'Test-double; no scientific provider evidence','metrics':{'test_double':True}}
        ans=validate_observations(ext)
        cache['validate_provider']=ans
        return {'status':ans['status'],'reason':ans['reason'], 'metrics':{'observations':ans['observations'],
            'provider':ext.get('provider'),'external_provider_real':ext.get('provider')=='pyknotid'}}

    def comparisons(which):
        provider_observation()
        if 'compared' not in cache:
            rows=obs_map(flatten(cache['provider']))
            low=compare_reference(rows,ref,(1200,2400))
            high=compare_reference(rows,ref,(4800,9600))
            symmetry=check_four_level_symmetry(rows,registry) if expected_keys().issubset(set(rows)) else {'status':'UNRESOLVED','checks':[]}
            cache['compared']={'low':low,'high':high,'symmetry':symmetry}
            json_write(run_dir/'g5_qualification_comparisons.json',{'schema':'sst.a003.g5.v028.comparisons/1',
                'baseline_source_sha256':hist['source_v027_output_json_sha256'],**cache['compared'],
                'historical_fail_is_not_overwritten':True})
        result=cache['compared'][which]
        if geometry_provider is not None or cache['provider'].get('provider')!='pyknotid':
            return {'status':'UNRESOLVED','reason':'Provider missing/test-double, comparison not real evidence',
                    'metrics':{'tested':result.get('total',0)}}
        return {'status':result['status'],'reason':f'{which} corrected-provider consistency',
                'metrics':{'tested':result.get('total',len(result.get('checks',[]))),
                           'matched':result.get('matched')}}

    def independent_diagrams():
        if 'diagrams' not in cache:
            rows=[]
            for sid in TARGET_SEEDS:
                for n in RESOLUTIONS:
                    file=f'xyz/{sid}_uniform_t_N{n}.xyz'
                    rec=next(r for r in registry['records'] if r['file']==file)
                    src=safe_atlas_file(atlas,file)
                    if sha256_file(src)!=rec['sha256']:
                        raise RuntimeError('Atlas mutated while checking independent diagrams')
                    pts=read_xyz(src,n)
                    for proj in PROJECTIONS:
                        trace=crossing_trace(pts@rotation_for_projection(proj).T)
                        name=f'raw_diagram_{sid}_N{n}_P{proj}.json'
                        json_write(run_dir/name,trace)
                        rows.append({'id':sid,'N':n,'projection':proj,
                            'crossings':trace['crossing_count'],
                            'ambiguous':sum(c['over']=='ambiguous' for c in trace['crossings']),
                            'near_degenerate':trace['nearly_degenerate_crossings'],
                            'determinant':trace['diagram_determinant']['value'],
                            'trace_file':name,'source_sha256':rec['sha256']})
            cache['diagrams']=rows
            json_write(run_dir/'g5q_independent_diagram_summary.json',{
                'schema':'sst.a003.g5q.raw-diagrams/1','cases':rows,
                'scientific_limit':'Independent determinant at t=-1; not full Alexander or knot certification'})
        rows=cache['diagrams']
        good=len(rows)==16 and all(r['ambiguous']==0 and r['near_degenerate']==0 and
            r['determinant']==(3 if r['id'].endswith('F3') else 1) for r in rows)
        return {'status':'PASS' if good else 'FAIL',
                'reason':'Independent 16 projected XYZ diagrams checked at four resolutions',
                'metrics':{'diagrams':len(rows),'all_match_declared_determinants':good}}

    def paired_diagrams():
        provider_observation()
        if 'diagrams' not in cache:independent_diagrams()
        rows=obs_map(flatten(cache['provider']))
        matched=[]
        for d in cache['diagrams']:
            for mirror in MIRRORS:
                obs=rows.get((d['id'],d['N'],d['projection'],mirror))
                if obs is None:
                    matched.append({'id':d['id'],'N':d['N'],'projection':d['projection'],'mirror':mirror,
                                    'status':'UNRESOLVED'})
                    continue
                coefficients=obs['alexander_coefficients']
                got=abs(sum(c*(-1)**i for i,c in enumerate(coefficients)))
                matched.append({'id':d['id'],'N':d['N'],'projection':d['projection'],'mirror':mirror,
                                'provider_determinant':got,'diagram_determinant':d['determinant'],
                                'status':'MATCH' if got==d['determinant'] else 'MISMATCH'})
        json_write(run_dir/'g5q_provider_diagram_comparison.json',{
            'schema':'sst.a003.g5q.provider-vs-diagram/1','cases':matched})
        if cache['provider'].get('provider')!='pyknotid' or geometry_provider is not None:
            return {'status':'UNRESOLVED','reason':'No real corrected provider for diagram comparison'}
        state='FAIL' if any(x['status']=='MISMATCH' for x in matched) else \
              'UNRESOLVED' if any(x['status']=='UNRESOLVED' for x in matched) else 'PASS'
        return {'status':state,'reason':'Provider determinants versus independent raw diagram at four resolutions',
                'metrics':{'matched':sum(x['status']=='MATCH' for x in matched),'total':len(matched)}}

    D=mod.GateDefinition
    defs=[D('G0','Full source atlas manifest integrity'),
          D('G1','Four resolutions, two Fibonacci torus XYZ seed inputs',('G0',)),
          D('G5Q0','Frozen independent v0.2.7 live corrected baseline provenance',('G0',)),
          D('G5Q1','Real corrected provider produced 32 observations',('G0','G1')),
          D('G5Q2','Corrected N=1200/2400 agrees v0.2.7 live baseline',('G5Q0','G5Q1')),
          D('G5Q3','Corrected N=4800/9600 agrees matched lower-resolution invariants',('G5Q1','G5Q2')),
          D('G5Q4','Four-level projection invariance and mirror-odd v3',('G5Q1','G5Q2','G5Q3')),
          D('G5Q5','Independent numerical crossing threshold control',('G0',)),
          D('G5Q6','Independent raw diagrams at all 4 levels (16 geometries)',('G0','G1')),
          D('G5Q7','32 corrected provider-vs-diagram determinant comparisons',('G5Q1','G5Q6')),
          D('G6','PKLSA Euler/finite-core vortex dynamics (not implemented)',('G0','G5Q4'))]
    ledger=mod.GateLedger(defs,strict_dependencies=False)
    good_source=all(report['gate_results'].get(g)=='PASS' for g in
        ('G0_MANIFEST_SCHEMA','G1_HASH_AND_XYZ','G2_GEOMETRIC_MIRROR_DIAGNOSTIC','G3_SAMPLING_CONVERGENCE'))
    ledger.run_evaluators({
        'G0':lambda:{'status':'PASS' if good_source else 'FAIL','reason':'Full 384-file source audit','metrics':{'records':384}},
        'G1':lambda:{'status':'PASS','reason':'F3/F4 at all four levels from verified XYZ'},
        'G5Q0':lambda:{'status':'PASS','reason':'v0.2.7 user-observed fixture SHA256 matches',
                    'metrics':{'baseline_rows':16,'fixture_sha256':FIXTURE_SHA256}},
        'G5Q1':validate_provider,
        'G5Q2':lambda:comparisons('low'),
        'G5Q3':lambda:comparisons('high'),
        'G5Q4':lambda:comparisons('symmetry'),
        'G5Q5':lambda:{'status':source_guard_geometry(atlas,registry)['status'],
                       'reason':'Stock threshold changes verdict on frozen F3 crossing; normalized guard remains stable'},
        'G5Q6':independent_diagrams,
        'G5Q7':paired_diagrams,
    })
    data=ledger.to_dict();json_write(run_dir/'GATE_LEDGER.json',data)
    json_write(run_dir/'g5_historical_crossing_guard.json',source_guard_geometry(atlas,registry))
    statuses={r['gate_id']:r['status'] for r in data['records']}
    evals=tuple(g for g in statuses if g!='G6')
    failures=[g for g in evals if statuses[g]=='FAIL']
    unresolved=[g for g in evals if statuses[g]!='PASS' and statuses[g]!='FAIL']
    complete=(not failures and not unresolved and all(statuses[g]=='PASS' for g in evals))
    exit_code=2 if failures else 3 if not complete else 0
    summary={'schema':SCHEMA,'adapter_version':ADAPTER_VERSION,
             'framework':{'version':'1.0.10','source_status':fw_meta.get('status'),
                          'root':str(fw),'gates_py_sha256':gates_sha,
                          'integration':'REAL GateLedger; NOT generated blind framework instance'},
             'source_atlas_version':'v0.1.2','source_manifest_sha256':sha256_file(atlas/'manifest.json'),
             'release_frozen':False,'baseline_historical_stock_fail_preserved':True,
             'v027_baseline_json_sha256':hist['source_v027_output_json_sha256'],
             'run_id':run_id,'provider':cache.get('provider',{}).get('provider','none'),
             'provider_status':cache.get('provider',{}).get('status','NOT_RUN'),
             'full_resolution_levels':list(RESOLUTIONS),
             'expected_provider_observations':EXPECTED_TOTAL,
             'measured_provider_observations':len(flatten(cache.get('provider',{}))),
             'corrected_g5_bounded_result':'PASS_INVARIANT_SCREEN_NOT_CERTIFIED' if complete else
                 'FAIL_INVARIANT_SCREEN' if failures else 'UNRESOLVED',
             'knot_topology_certified':False,'chirality_certified':False,
             'g6_pklsa_euler_run':False,'reveal_performed':False,
             'scientific_scope':'F3 T(2,3), F4 T(3,5) corrected pyknotid at 4 mesh levels, 2 projections, mirrors',
             'failed_gates':failures,'unresolved_gates':unresolved,
             'full_diagnostic_after_fail':True,'exit_code':exit_code}
    json_write(run_dir/'QUALIFICATION_SUMMARY.json',summary)
    pdf=render_qualification_report(run_dir,data,summary)
    json_write(run_dir/'PDF_RENDER.json',pdf)
    return exit_code,run_dir,summary


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas',type=Path,default=None)
    p.add_argument('--framework-root',type=Path,default=None)
    p.add_argument('--out-root',type=Path,default=ADAPTER_ROOT.parent/(ADAPTER_ROOT.name+'-outputs'))
    p.add_argument('--skip-provider',action='store_true',help='provenance smoke, no new G5 evidence')
    p.add_argument('--max-crossings',type=int,default=12)
    opts=p.parse_args(argv)
    try:
        atlas=resolve_atlas_root(opts.atlas)
        code,folder,summary=run_campaign(atlas=atlas,framework=opts.framework_root,
                  out_root=opts.out_root,run_provider=not opts.skip_provider,max_crossings=opts.max_crossings)
        print(json.dumps({'run_dir':str(folder),'exit_code':code,'screen':summary['corrected_g5_bounded_result'],
            'failed':summary['failed_gates'],'unresolved':summary['unresolved_gates']},indent=2))
        return code
    except Exception as exc:
        print(f'FATAL_INTEGRITY_OR_EXECUTION_ERROR: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 4

if __name__=='__main__':raise SystemExit(main())
