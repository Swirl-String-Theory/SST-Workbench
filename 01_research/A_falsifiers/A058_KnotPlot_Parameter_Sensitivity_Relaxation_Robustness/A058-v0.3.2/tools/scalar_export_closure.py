"""A058-v0.3.8: native scalar export closure, additive and evidence-first.

Historical v0.3.7 four-case test is immutable.  New 2 x 3 matched-horizon
KnotPlot probes use the empirically validated data-open -> compute -> data
ordering and compare each native CSV row to its own XYZ snapshot.

A PASS is strictly numerical measurement qualification, NEVER physical
convergence, continuous collision safety, or stability.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from distribution_audit import BASE_SCRIPT, required_source, sha_file
from native_measurement import (Evidence, digest, csv_observation, geom_metrics,
                                qualify_case, read_json, tolerance, write_json,
                                xyz_points, _get_readback, _safe_pass, FATAL)
from shortcut_runtime import knotplot_path, resolve_launcher

SCHEMA = 'A058-NATIVE-SCALAR-EXPORT-CLOSURE-1'
ITERATIONS = (32, 128, 512)
DSTEPS = (1, 4)
CASES = tuple((d, n) for d in DSTEPS for n in ITERATIONS)
STATUS_PASS = 'QUALIFIED_NUMERICAL_EXPORT_ONLY'
POSITIVE = 'dstep_{d}_before'
NEGATIVE = 'dstep_{d}_after'


def _new_directory(out: Path) -> Path:
    out = Path(out).expanduser().resolve()
    if out.exists():
        raise FileExistsError(f'Refusing to overwrite existing output directory: {out}')
    out.mkdir(parents=True, exist_ok=False)
    return out


def _script(dstep: int, iterations: int) -> str:
    if (dstep, iterations) not in CASES:
        raise ValueError('Condition not in registered v0.3.8 closure matrix')
    commands = BASE_SCRIPT + [f'dstep = {dstep}',
        'echo A058_V038_INITIAL_STATE_BEGIN', 'parameters', 'echo A058_V038_INITIAL_STATE_END',
        'echo A058_SAFE_START', 'safe', 'echo A058_SAFE_START_END',
        f'go {iterations}',
        'echo A058_V038_FINAL_STATE_BEGIN', 'parameters', 'echo A058_V038_FINAL_STATE_END',
        'echo A058_SAFE_FINAL', 'safe', 'echo A058_SAFE_FINAL_END',
        # EXACTLY the empirically qualified ordering from the real 2026 v0.3.7 tests:
        # completed go -> data open/format/header -> length -> rog -> data -> close.
        'data open A058_native_metrics.csv', 'data format "/N,/l,/g,/I"', 'data header',
        'length', 'rog', 'data', 'data close', 'save A058_final.txt ascii']
    return '\n'.join(commands)+'\n'


def _runtime_script(source: str, folder: Path) -> str:
    paths = {'load A058_seed.kpf': 'load '+knotplot_path(folder/'A058_seed.kpf'),
             'data open A058_native_metrics.csv':'data open '+knotplot_path(folder/'A058_native_metrics.csv'),
             'save A058_final.txt ascii':'save '+knotplot_path(folder/'A058_final.txt')+' ascii'}
    lines = source.splitlines()
    for old, replacement in paths.items():
        hits = [i for i, line in enumerate(lines) if line == old]
        if len(hits) != 1:
            raise ValueError(f'Native script input/output command must appear once: {old}')
        lines[hits[0]] = replacement
    return '\n'.join(lines)+'\n'


def generate(dist: Path, out: Path) -> dict:
    dist = Path(dist).expanduser().resolve(strict=True)
    if not dist.is_file(): raise FileNotFoundError(dist)
    with zipfile.ZipFile(dist) as archive:
        root = required_source(archive)
        seed = archive.read(root+'basic/3.1')
    if len(seed) < 100: raise ValueError('Invalid distribution trefoil seed')
    out = _new_directory(out)
    rows = []
    for d, iterations in CASES:
        name = f'dstep_{d}_go_{iterations}'
        path = out/name
        path.mkdir()
        script = _script(d, iterations)
        (path/'probe.kpc').write_text(script, encoding='utf-8', newline='\n')
        (path/'A058_seed.kpf').write_bytes(seed)
        rows.append({'id':name, 'dstep':d, 'expected_iterations':iterations,
                     'seed_sha256':digest(seed), 'script_sha256':digest(script.encode('utf-8'))})
    receipt = {'schema':'A058-SCALAR-EXPORT-DESIGN-1',
               'parent_science_protocol':'A058-271-CONDITIONS-UNTOUCHED',
               'distribution_sha256':sha_file(dist), 'source_seed_sha256':digest(seed),
               'cases':rows, 'calibrated_export_sequence':['go N','data open','data format','data header',
                                      'length','rog','data','data close','save ascii'],
               'frozen_dsteps':list(DSTEPS),'fixed_observation_horizons':list(ITERATIONS),
               'alex_dependency':'EXCLUDED','physics_claim':'NONE',
               'no_collision_between_steps':'NOT_CERTIFIED'}
    write_json(out/'CLOSURE_DESIGN.json',receipt)
    return receipt


def _plan(out: Path) -> list[dict]:
    doc = read_json((out/'CLOSURE_DESIGN.json').read_bytes())
    rows = doc.get('cases', [])
    if doc.get('schema') != 'A058-SCALAR-EXPORT-DESIGN-1' or len(rows) != 6:
        raise ValueError('Incomplete or changed native closure design')
    if [(r.get('dstep'),r.get('expected_iterations')) for r in rows] != list(CASES):
        raise ValueError('Registration order/dstep/iteration horizons modified')
    expected_seed = doc['source_seed_sha256']
    plan = []
    for row in rows:
        folder = out/row['id']
        script = folder/'probe.kpc'; seed = folder/'A058_seed.kpf'
        if not script.is_file() or not seed.is_file():
            raise FileNotFoundError(f'Missing generated input for {row["id"]}')
        if sha_file(script)!=row['script_sha256'] or sha_file(seed)!=row['seed_sha256'] or sha_file(seed)!=expected_seed:
            raise ValueError(f'Input hash mismatch: {row["id"]}')
        data = script.read_text(encoding='utf-8')
        if data != _script(row['dstep'],row['expected_iterations']):
            raise ValueError(f'Probe command contract modified: {row["id"]}')
        for filename in ('probe.native.kpc','NATIVE_STDOUT_PRIVATE.log','A058_native_metrics.csv','A058_final.txt'):
            if (folder/filename).exists():
                raise FileExistsError(f'Previous native evidence must not be overwritten: {folder/filename}')
        plan.append({**row,'folder':folder,'runtime':_runtime_script(data,folder)})
    for name in ('NATIVE_RESULTS.json','NATIVE_LAUNCH_PRIVATE.json'):
        if (out/name).exists(): raise FileExistsError(f'Previous run evidence: {name}')
    return plan


def _state_param(log: str, marker: str, key: str) -> float | None:
    a = log.find(marker+'_BEGIN')
    b = log.find(marker+'_END', a+len(marker)) if a>=0 else -1
    if a<0 or b<0: return None
    segment=log[a+len(marker+'_BEGIN'):b]
    hits = re.findall(r'(?im)^\s*'+re.escape(key)+r'\s*=\s*([-+\d.eE]+)\s*$',segment)
    if len(hits) != 1: return None
    try:
        n=float(hits[0]);return n if math.isfinite(n) else None
    except ValueError: return None


def _state_switch(log: str, marker: str, key: str, expected: str) -> bool:
    a=log.find(marker+'_BEGIN'); b=log.find(marker+'_END', a+len(marker)) if a>=0 else -1
    if a<0 or b<0:return False
    hits=re.findall(r'(?im)^\s*'+re.escape(key)+r'\s*=\s*(on|off|true|false)\s*$',log[a:b])
    return len(hits)==1 and hits[0].casefold()==expected


def qualify_native(log_data: bytes|None, coords: bytes|None, csv_data: bytes|None,
                   *, dstep: int, iterations: int, native_script: bytes|None,
                   returncode: int|None, timedout: bool) -> dict:
    result={'scientific_status':'NUMERICAL_EXPORT_ONLY','expected_dstep':dstep,
            'expected_iterations':iterations,'returncode':returncode,'timeout':bool(timedout),
            'physical_convergence':'UNRESOLVED','continuous_collision_avoidance':'NOT_CERTIFIED',
            'alexander_polynomial':'NOT_REQUESTED'}
    if log_data is None or coords is None or csv_data is None or native_script is None:
        result['status']='FAIL_MISSING_NATIVE_EVIDENCE'
        return result
    txt=log_data.decode('utf-8',errors='replace')
    result.update({'native_log_sha256':digest(log_data),'coordinate_sha256':digest(coords),
                   'csv_sha256':digest(csv_data),'runtime_script_sha256':digest(native_script)})
    result['fatal_tokens']=[t for t in FATAL if t in txt.casefold()]
    result['start_safe']=_safe_pass(txt,'START')
    result['final_safe']=_safe_pass(txt,'FINAL')
    pre='A058_V038_INITIAL_STATE';post='A058_V038_FINAL_STATE'
    params={'initial_dstep':_state_param(txt,pre,'dstep'),
            'final_dstep':_state_param(txt,post,'dstep'),
            'initial_iteration':_state_param(txt,pre,'iteration'),
            'final_iteration':_state_param(txt,post,'iteration')}
    result['parameter_state']=params
    required_force={'velforce':'off','tanforce':'off','gravity':'off','thermalforce':'off'}
    result['force_guard_readback']={k:(_state_switch(txt,pre,k,v) and _state_switch(txt,post,k,v))
                                    for k,v in required_force.items()}
    result['parameter_gate']=(params['initial_dstep']==dstep and params['final_dstep']==dstep and
                              params['initial_iteration']==0 and params['final_iteration']==iterations and
                              all(result['force_guard_readback'].values()))
    try:
        geometry=geom_metrics(xyz_points(coords))
        result['geometry']=geometry
        geometry_ok=(geometry['nbeads']>=3 and geometry['min_edge']>0 and
                     all(math.isfinite(geometry[k]) and geometry[k]>0 for k in ('length','rg')))
    except (ValueError, OverflowError) as exc:
        result['geometry_parse_error']=type(exc).__name__
        geometry_ok=False;geometry=None
    result['geometry_gate']=geometry_ok
    nativecsv=csv_observation(csv_data)
    result['csv']=nativecsv
    csvv=nativecsv.get('values')
    result['csv_gate']=bool(csvv and geometry_ok and
      csvv['nbeads']==geometry['nbeads'] and csvv['iteration']==iterations and
      tolerance(csvv['length'],geometry['length']) and tolerance(csvv['rg'],geometry['rg']))
    script=native_script.decode('utf-8',errors='replace').splitlines()
    try:
        checks=[lambda x:x.startswith('data open '), lambda x:x.startswith('data format '),
                lambda x:x=='data header',lambda x:x=='length',lambda x:x=='rog',
                lambda x:x=='data',lambda x:x=='data close',lambda x:x.startswith('save ')]
        starts=[next(i for i,line in enumerate(script) if check(line)) for check in checks]
        ordering_ok=(starts==sorted(starts) and len(set(starts))==len(starts)
                     and all(sum(bool(check(line)) for line in script)==1 for check in checks)
                     and not any(line.startswith('alex ') for line in script))
    except StopIteration:
        ordering_ok=False
    result['script_order_gate']=(ordering_ok and f'go {iterations}' in script and
                                 f'dstep = {dstep}' in script and
                                 script.index(f'go {iterations}') < starts[0])
    result['process_gate']=(returncode==0 and not timedout and not result['fatal_tokens'])
    result['status']=(STATUS_PASS if all([result['process_gate'],result['parameter_gate'],
                                        result['start_safe'],result['final_safe'],
                                        result['geometry_gate'],result['csv_gate'],
                                        result['script_order_gate']]) else 'FAIL_SCALAR_EXPORT_CONTRACT')
    return result


def audit_v037(source: Path, out: Path) -> dict:
    """Four authentic 2026 branches prove paired positive/negative controls.

    Enforces hash binding to original native run receipts; no negative branch
    is allowed to be relabeled qualified merely to obtain an all-PASS report.
    """
    out=Path(out).expanduser().resolve()
    if out.exists(): raise FileExistsError('Closure audit output must be NEW')
    ev=Evidence(source)
    try:
        design=read_json(ev.read('MEASUREMENT_DESIGN.json',required=True))
        receipt=read_json(ev.read('NATIVE_RESULTS.json',required=True))
        registered=design.get('conditions',[])
        if [(x.get('dstep'),x.get('data_open_order')) for x in registered] != [(1,'before'),(1,'after'),(4,'before'),(4,'after')]:
            raise ValueError('Historical four-case design differs from preregistered order')
        conditions={}
        coords=[];seeds=[];facts=[]
        for row in registered:
            key=row['id'];d=row['dstep'];kind=row['data_open_order'];prefix=key+'/'
            log=ev.read(prefix+'NATIVE_STDOUT_PRIVATE.log',required=True)
            points=ev.read(prefix+'A058_final.txt',required=True)
            csvdata=ev.read(prefix+'A058_native_metrics.csv',required=True)
            script=ev.read(prefix+'probe.native.kpc',required=True)
            script0=ev.read(prefix+'probe.kpc',required=True)
            seed=ev.read(prefix+'A058_seed.kpf',required=True)
            original=receipt.get('conditions',{}).get(key)
            hashes_ok=(original is not None and original.get('process_returncode')==0 and
                       not original.get('timeout') and original.get('native_stdout_sha256')==digest(log) and
                       original.get('coordinate_sha256')==digest(points) and
                       original.get('runtime_script_sha256')==digest(script) and
                       row.get('seed_sha256')==digest(seed) and row.get('script_sha256')==digest(script0))
            native=qualify_case(log,points,csvdata,expected_dstep=d,runtime_script=script)
            body=script.decode('utf-8',errors='replace')
            first_data=body.find('data open ')
            first_length=body.find('\nlength\n')
            true_order=((kind=='before' and first_data>=0 and first_data<first_length) or
                        (kind=='after' and first_data>first_length>=0))
            expected=(native.get('status')=='QUALIFIED_NUMERICAL_MEASUREMENT_ONLY' if kind=='before'
                      else native.get('scalar_gate')=='FAIL' and native.get('csv',{}).get('values',{}).get('length')==0 and
                      native.get('csv',{}).get('values',{}).get('rg')==0)
            ok=bool(hashes_ok and true_order and expected and native.get('safe_start') and native.get('safe_final') and
                    native.get('parameter_gate')=='PASS' and native.get('script_gate')=='PASS' and
                    native.get('console_comparison',{}).get('length_matches_xyz') and
                    native.get('console_comparison',{}).get('rg_matches_xyz'))
            conditions[key]={'status':'EXPECTED_CONTROL_CONFIRMED' if ok else 'FAIL_OR_UNRESOLVED',
                             'expected_role':'POSITIVE' if kind=='before' else 'NEGATIVE',
                             'native_scalar_gate':native.get('scalar_gate'),
                             'native_parameter_gate':native.get('parameter_gate'),
                             'source_hashes_verified':bool(hashes_ok),
                             'runtime_order_verified':bool(true_order),
                             'coordinate_sha256':digest(points),'seed_sha256':digest(seed),
                             'csv_length':native.get('csv',{}).get('values',{}).get('length'),
                             'csv_rg':native.get('csv',{}).get('values',{}).get('rg')}
            coords.append(digest(points));seeds.append(digest(seed));facts.append(ok)
        controls_ok=(all(facts) and len(set(coords))==1 and len(set(seeds))==1)
        report={'schema':SCHEMA,'mode':'READ_ONLY_V037_ORDERING_CLOSURE',
          'historical_source_name':Path(source).name,
          'historical_source_sha256':sha_file(source) if Path(source).is_file() else None,
          'conditions':conditions,'positive_controls_pass':sum(x['status']=='EXPECTED_CONTROL_CONFIRMED' and x['expected_role']=='POSITIVE' for x in conditions.values()),
          'negative_controls_reproduce':sum(x['status']=='EXPECTED_CONTROL_CONFIRMED' and x['expected_role']=='NEGATIVE' for x in conditions.values()),
          'historical_method_closure':'PASS' if controls_ok else 'FAIL_OR_UNRESOLVED',
          'full_internal_cause':'NOT_ISOLATED','production_contract':'DATA_INITIALIZATION_BEFORE_SCALAR_COMPUTATION',
          'historical_source_mutated':False,'old_271_condition_protocol':'UNTOUCHED',
          'physics_validation':'NOT_CLAIMED'}
    finally:
        ev.close()
    out=_new_directory(out)
    write_json(out/'CLOSURE_AUDIT.json',report)
    _write_report(out/'CLOSURE_REPORT.md',report)
    _write_matrix(out/'CLOSURE_MATRIX.csv',report)
    return report


def _write_matrix(path: Path, report: dict):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f)
        w.writerow(['condition','role','qualification','scalar_gate','parameter_gate',
                    'source_hashes_verified','coordinate_sha256','csv_length','csv_rg'])
        for key,r in report['conditions'].items():
            w.writerow([key,r.get('expected_role','PRODUCTION'),r['status'],
                        r.get('native_scalar_gate', 'PASS' if r.get('csv_gate') else 'FAIL'),
                        r.get('native_parameter_gate', 'PASS' if r.get('parameter_gate') else 'FAIL'),
                        r.get('source_hashes_verified',r.get('source_seed_gate')),
                        r.get('coordinate_sha256'),r.get('csv_length',r.get('csv',{}).get('values',{}).get('length')),
                        r.get('csv_rg',r.get('csv',{}).get('values',{}).get('rg'))])


def _write_report(path: Path, report: dict):
    ok=report.get('historical_method_closure',report.get('native_scalar_closure','NOT_RUN'))
    content=['# A058 v0.3.8 — Native Scalar Export Closure','',
             f"Mode: `{report['mode']}`; closure: `{ok}`.",'',
             '| Case | Status |', '|---|---|']
    for k,r in report['conditions'].items(): content.append(f"| `{k}` | `{r['status']}` |")
    content += ['', '**Interpretation:** This qualifies only the numerical scalar-export workflow. '
                'A positive native geometry/CSV match is NOT a physical stability or convergence result.',
                '', 'No physical Euler/PKLSA, time-continuous collision, or asymptotic-attractor claim.',
                '', 'The original blind 271-condition campaign and existing native evidence are not changed.', '']
    path.write_text('\n'.join(content),encoding='utf-8',newline='\n')


def run_native(exe: str|Path, out: Path, timeout: int, *, dist: Path|None=None, workdir=None) -> dict:
    if timeout<=0: raise ValueError('timeout must be positive')
    out=Path(out).expanduser().resolve()
    if not out.exists():
        if dist is None: raise FileNotFoundError('Generate closure inputs first, or provide --dist for a NEW out directory')
        generate(dist,out)
    plan=_plan(out)  # checks all conditions before touching any native evidence
    launcher=resolve_launcher(exe,workdir_override=workdir)
    write_json(out/'NATIVE_LAUNCH_PRIVATE.json',{
        'exe':str(launcher.executable),'exe_sha256':sha_file(launcher.executable),
        'workdir':str(launcher.workdir),'workdir_source':launcher.workdir_source,
        'shortcut':str(launcher.shortcut) if launcher.shortcut else None,
        'io_policy':'ABSOLUTE_A058_EXPORT_PATHS','native_stdout_private':True})
    results={}
    for case in plan:
        wd=case['folder'];scriptfile=wd/'probe.native.kpc'
        scriptfile.write_text(case['runtime'],encoding='utf-8',newline='\n')
        log=wd/'NATIVE_STDOUT_PRIVATE.log'
        rc=None;timedout=False;reason=None
        try:
            with scriptfile.open('rb') as stream,log.open('xb') as stdout:
                cp=subprocess.run(launcher.command(),cwd=launcher.workdir,executable=str(launcher.executable),
                                  stdin=stream,stdout=stdout,stderr=subprocess.STDOUT,
                                  check=False,timeout=timeout)
                rc=cp.returncode
        except subprocess.TimeoutExpired:
            timedout=True
        except OSError as exc:
            reason=type(exc).__name__
        r=qualify_native(log.read_bytes() if log.exists() else None,
           (wd/'A058_final.txt').read_bytes() if (wd/'A058_final.txt').is_file() else None,
           (wd/'A058_native_metrics.csv').read_bytes() if (wd/'A058_native_metrics.csv').is_file() else None,
           dstep=case['dstep'],iterations=case['expected_iterations'],
           native_script=scriptfile.read_bytes(),returncode=rc,timedout=timedout)
        if reason:r['launch_error_type']=reason
        r['source_seed_gate']=sha_file(wd/'A058_seed.kpf')==case['seed_sha256']
        if not r['source_seed_gate']:
            r['status']='FAIL_SEED_INTEGRITY'
        r['input_design_sha256']=case['script_sha256']
        results[case['id']]=r
    doc={'schema':SCHEMA,'mode':'NEW_NATIVE_SCALAR_CLOSURE',
         'native_scalar_closure':'PASS' if all(r['status']==STATUS_PASS for r in results.values()) else 'FAIL_OR_UNRESOLVED',
         'qualified_conditions':sum(r['status']==STATUS_PASS for r in results.values()),
         'condition_count':len(results),'conditions':results,
         'report_scope':'FINITE_ITERATION_NUMERICAL_EXPORT_ONLY',
         'original_blind_271_conditions':'UNTOUCHED',
         'alexander':'NOT_USED',
         'between_checkpoint_collision_certification':'NOT_PROVIDED',
         'physical_convergence':'UNRESOLVED'}
    write_json(out/'NATIVE_RESULTS.json',doc)
    sub=out/'qualification';sub.mkdir(exist_ok=False)
    write_json(sub/'CLOSURE_AUDIT.json',doc)
    _write_matrix(sub/'CLOSURE_MATRIX.csv',doc)
    _write_report(sub/'CLOSURE_REPORT.md',doc)
    return doc


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('AUDIT_SCALAR_CLOSURE','GENERATE_SCALAR_CLOSURE','RUN_SCALAR_CLOSURE'))
    p.add_argument('--source',type=Path)
    p.add_argument('--dist',type=Path)
    p.add_argument('--exe',type=str)
    p.add_argument('--workdir',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--timeout',type=int,default=120)
    args=p.parse_args(argv)
    if args.mode=='AUDIT_SCALAR_CLOSURE' and args.source is None:p.error('--source is required')
    if args.mode=='GENERATE_SCALAR_CLOSURE' and args.dist is None:p.error('--dist is required')
    if args.mode=='RUN_SCALAR_CLOSURE' and args.exe is None:p.error('--exe is required')
    try:
        if args.mode=='AUDIT_SCALAR_CLOSURE':
            d=audit_v037(args.source,args.out); success=d['historical_method_closure']=='PASS'
        elif args.mode=='GENERATE_SCALAR_CLOSURE':
            d=generate(args.dist,args.out); success=True
        else:
            d=run_native(args.exe,args.out,args.timeout,dist=args.dist,workdir=args.workdir)
            success=d['native_scalar_closure']=='PASS'
        print(json.dumps({'mode':args.mode,'output':str(args.out),
                          'result':d.get('historical_method_closure',d.get('native_scalar_closure','DESIGN_GENERATED')),
                          'conditions':len(d.get('conditions',d.get('cases',[])))},sort_keys=True))
        return 0 if success else 2
    except (ValueError,OSError,KeyError,zipfile.BadZipFile,RuntimeError) as exc:
        print(f'A058 {args.mode} FAIL-CLOSED: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 3


if __name__=='__main__':
    raise SystemExit(main())
