from __future__ import annotations
import argparse, os, shutil, subprocess, sys, tempfile, json
from pathlib import Path
from common import digest, dump, read, unique, guard, sha_record

BASE=Path(__file__).resolve().parent
CLONE=BASE/'acquisition_workspace'/'A058-v0.2.9'
MANIFEST=BASE/'acquisition_workspace'/'CLONE_MANIFEST.json'
GUARDS=['run_all.cmd','README.md','configs/default.json','tools/run_budget.py','tools/budget_acquisition.py','run_freeze.cmd','run_install.cmd']

def code_fingerprints(src):
    src=Path(src); pieces=[]
    for f in src.rglob('*'):
        if not f.is_file():continue
        rel=f.relative_to(src)
        if any(p in ('private','campaign','outputs','.venv','build','dist','__pycache__','.pytest_cache') for p in rel.parts):continue
        if f.suffix.lower() in ('.py','.cmd','.json','.toml','.yaml','.yml','.cpp','.h','.hpp','.c'):
            pieces.append((rel.as_posix(),digest(f)))
    return dict(sorted(pieces))

def contract(src):
    src=Path(src)
    guard(src.is_dir(),'Original A058-v0.2.9 instance folder missing')
    for r in GUARDS:guard((src/r).is_file(),f'Original v0.2.9 required path missing: {r}')
    c=read(src/'configs/default.json')
    guard(c.get('schema')=='A058-TREFOIL-SLIDER-RESPONSE-8','Wrong A058 contract')
    guard(c.get('axes')==['S0','S1','S2','S3','S4','S5','S6','S7'],'8 registered axes required')
    guard(c.get('references')==['R0','R1','R2','R3','R4','R5'],'6 references required')
    guard(len(c['activation_controls'])==1,'1 independent switch control required')
    guard(c['response_budgets']['BASIC']['checkpoints']==[32,128,512],'BASIC checkpoints changed')
    guard(c['response_budgets']['2048']['checkpoints']==[32,128,512,2048],'2048 checkpoints changed')
    guard(c['response_budgets']['32768']['checkpoints']==[32,128,512,2048,8192,32768],
        '32768 checkpoints changed')
    guard(c['response_budgets']['32768']['max_conditions']==31,'Heavy selection max not 31')
    guard(c['topology']['baseline_n']==300 and c['topology']['topology_id']=='T00','300-bead T00 source required')
    guard(c['ladder']['k_max']-c['ladder']['k_min']+1==33,'Expected 33 multipliers including default')
    return {'version':'A058-v0.2.9 original engine','framework_pin':'v1.0.8 LOCAL_VALIDATED_CANDIDATE',
        'registration_count':6+1+8*32*1+8*1, # 6 + 1 + 8*33 = 271
        'source_fingerprints':{r:digest(src/r) for r in GUARDS},
        'complete_code_manifest':code_fingerprints(src),
        'source_root':str(src.resolve()),'budget_modes':['BASIC','2048','32768']}

def prepare(src):
    guard(not CLONE.exists() and not MANIFEST.exists(),'Acquisition clone already exists; never overwrite. Use STATUS or new coordinator version.')
    origin=Path(src).resolve()
    guard(BASE not in origin.parents and origin!=BASE,'Do not recursively clone coordinator')
    info=contract(origin)
    CLONE.parent.mkdir(parents=True,exist_ok=True)
    def ignore(path,names):
        skip={'.venv','__pycache__','.pytest_cache','.git','build','dist','outputs','.mypy_cache','campaign_logs'}
        if Path(path).name in ('runs','_runs') and Path(path).parent.name=='campaign':skip |=set(names)
        return {x for x in names if x in skip or x.endswith('.pyd') or x.endswith('.obj')}
    shutil.copytree(origin,CLONE,ignore=ignore,symlinks=False)
    # Preserve private commitments and keys for exact frozen-protocol continuation (never publish clone).
    for secret in ('private/OPAQUE_ID_KEY.bin','private/REVEAL_NONCE.bin'):
        guard((CLONE/secret).is_file() and (CLONE/secret).stat().st_size==32,
              f'Sealed source private material missing: {secret}; no silent rekey')
    # Source clone keeps its frozen protocol, not a fresh statistically independent campaign.
    info['clone_root']=str(CLONE.resolve());info['clone_source_fingerprints']={r:digest(CLONE/r) for r in GUARDS}
    info['clone_complete_code_manifest']=code_fingerprints(CLONE)
    guard(info['source_fingerprints']==info['clone_source_fingerprints'],'Clone source hash mismatch')
    guard(info['complete_code_manifest']==info['clone_complete_code_manifest'],'Full scientific code manifest mismatch')
    info['registry_equation']='6 references + 1 activation + 8 axes*33 nondefault = 271'
    info['counts']={'references':6,'switch_control':1,'axis_conditions':264,'total':271}
    info['physical_run_status']='NOT_RUN'
    info['blind_integrity']='EXISTING_COMMITMENT_CONTINUATION_NOT_FRESH_RANDOMIZATION'
    dump(MANIFEST,info)
    print('PREPARED non-mutating clone',CLONE)
    print('NEXT on Windows: bridge.py INSTALL; bridge.py FREEZE; then BASIC, 2048, 32768')

def status():
    m=read(MANIFEST) if MANIFEST.exists() else None
    data={'acquisition_clone_present':bool(CLONE.exists()),'clone_manifest':m,
        'run_tiers':{k:(CLONE/'campaign'/'runs'/k).exists() for k in ('BASIC','2048','32768')},
        'active_run_exists':(CLONE/'campaign'/'active_run.json').exists(),
        'physical_reproducibility':'UNVERIFIED_UNTIL_NATIVE_WINDOWS_KNOTPLOT_LOGS_INSPECTED'}
    print(json.dumps(data,indent=2))
    return data

def validate_clone():
    guard(MANIFEST.exists() and CLONE.exists(),'Run PREPARE with original source first')
    m=read(MANIFEST)
    guard(m['source_fingerprints']=={r:digest(CLONE/r) for r in GUARDS},'Cloned source/config hash changed: new version required')
    guard(m['complete_code_manifest']==code_fingerprints(CLONE), 'Source code changed since clone; original protocol must not be silently modified')
    contract(CLONE)
    return m

def launch(mode):
    m=validate_clone()
    guard(os.name=='nt','Native KnotPlot acquisition requires Windows; no simulation/fake fallback')
    if mode=='32768':
        guard(any((CLONE/'campaign'/'runs'/k).exists() for k in ('BASIC','2048')),
              '32768 blocked until original-runner BASIC/2048 acquisition exists')
    # Run exact original instance launch scripts in the cloned tree.
    launcher=CLONE/('run_install.cmd' if mode=='INSTALL' else 'run_freeze.cmd' if mode=='FREEZE' else 'run_all.cmd')
    guard(launcher.exists(),f'Required original launcher missing: {launcher}')
    cmd=['cmd','/d','/c',str(launcher)] if mode in ('INSTALL','FREEZE') else ['cmd','/d','/c',str(launcher),mode]
    print('Executing registered original runner:',cmd,'cwd=',CLONE,flush=True)
    ret=subprocess.run(cmd,cwd=CLONE,check=False)
    out=unique(BASE/'execution_logs','A058v030-'+mode)
    dump(out/'COORDINATOR_EXECUTION.json',{
        'requested_mode':mode,'engine':'A058-v0.2.9 unchanged cloned source',
        'original_source_fingerprints':m['source_fingerprints'],'exit_code':ret.returncode,
        'certification':'UNREVIEWED_NATIVE_RESULT','physical_conclusion':'NOT_INFERRED_FROM_EXIT_CODE',
        'required_followup':'Inspect native KnotPlot logs, actual bead geometry and gate ledger in clone'} )
    if ret.returncode: raise SystemExit(ret.returncode)
    print('OS process returned 0. Run STATUS and inspect full original ledger; no physics PASS inferred.')


def triage(analysis_path,ledger_path,runlog_path=None):
    # Retrospective public evidence audit; do not edit original frozen campaign.
    guard(analysis_path and ledger_path,'TRIAGE needs --analysis and --ledger JSON')
    a=read(analysis_path); l=read(ledger_path)
    guard(a.get('schema') and a.get('registered_population_count')==271,
        'Expected existing A058 271-condition scientific acquisition output')
    st={v['gate_id']:v['status'] for v in l.get('records',[])}
    responses=a.get('responses',[])
    grouped={f'S{i}':[] for i in range(8)}
    for r in responses:
        if r.get('axis_id') in grouped:grouped[r['axis_id']].append(r)
    axis={}
    for k,rs in grouped.items():
        result=a.get('axis_summaries',{}).get(k,{})
        axis[k]={'valid_matched_responses':len(rs),
                 'registered_slider_conditions':33,
                 'unavailable_count':33-len(rs),
                 'maximum_shape_response':result.get('max_shape') if isinstance(result.get('max_shape'),(int,float)) and __import__('math').isfinite(result['max_shape']) else None,
                 'not_equilibrium':True}
    fixes=[
        {'id':'FIX-RUNTIME-STATE','priority':1,'issue':'G1 FAIL; parameter state was not verified for all attempted cases',
         'required':'Per-sector reset readback and exact slider/switch echo; compare requested values with runtime values; retain all failed cases'},
        {'id':'FIX-EXPORT','priority':2,'issue':'G2 FAIL; missing/garbled output geometries',
         'required':'Verify final x,y,z export after solver-count checkpoint, exact 300 beads, nonempty and SHA, timeout and path diagnostics'},
        {'id':'FIX-R4-GRAPHICS','priority':3,'issue':'Potential headless incompatibility in R4',
         'required':'Use source-native R4 graphics fallback only on actual machine; keep UNSUPPORTED_RUNTIME distinct from physics FAIL'},
        {'id':'FIX-G8','priority':4,'issue':'G8 FAIL; finite-time safety/classification incomplete',
         'required':'Recover safe final readback; do not mark fixed 512 iterations as convergence or equilibrium'},
        {'id':'FIX-BUDGET','priority':5,'issue':'No permission to infer long-time dynamics from BASIC',
         'required':'After authentic G1/G2/G8 retest, acquire 2048 matched horizon then blinded selection <=31 at 32768'}
    ]
    doc={'schema':'A058-REPAIR-TRIAGE-1','analysis_source':sha_record(analysis_path),
         'ledger_source':sha_record(ledger_path),'runlog_source':sha_record(runlog_path) if runlog_path else None,
         'registered_population':271,'attempted_in_runlog':a.get('runlog_entries'),
         'run_failures':a.get('run_failures'),'unsupported_runtime':a.get('unsupported_runtime'),
         'coordinate_complete_fraction':a.get('coordinate_complete_fraction'),
         'parameter_state_verified_fraction':a.get('parameter_state_verified_fraction'),
         'safe_final_verified_fraction':a.get('safe_final_verified_fraction'),
         'convergence_assessed':a.get('convergence_assessed'),'gate_status':st,
         'by_anonymous_axis':axis,'repairs':fixes,'physical_stability_verdict':'NOT_ESTABLISHED'}
    if runlog_path:
        from collections import Counter
        r=read(runlog_path)
        statuses=Counter(str(z.get('status','UNKNOWN')) for z in r.get('conditions',[]))
        doc['runtime_status_counts']=dict(statuses)
        doc['runlog_count']=len(r.get('conditions',[]))
    out=unique(BASE/'triage_outputs','A058triage')
    dump(out/'FIX_PLAN.json',doc)
    print(out,'Gates:',st,'attempted:',doc['attempted_in_runlog'],
          'failures:',doc['run_failures'],'unsupported:',doc['unsupported_runtime'])
    return doc

def selftest():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'configs').mkdir()
        cfg={ 'schema':'A058-TREFOIL-SLIDER-RESPONSE-8','axes':[f'S{i}' for i in range(8)],
        'references':[f'R{i}' for i in range(6)], 'activation_controls':[{'control_id':'A_R2_OFF'}],
        'response_budgets':{'BASIC':{'checkpoints':[32,128,512]},
        '2048':{'checkpoints':[32,128,512,2048]},
        '32768':{'checkpoints':[32,128,512,2048,8192,32768],'max_conditions':31}},
        'topology':{'baseline_n':300,'topology_id':'T00'},'ladder':{'k_max':16,'k_min':-16}}
        (p/'configs'/'default.json').write_text(json.dumps(cfg))
        (p/'tools').mkdir()
        for f in ('run_budget.py','budget_acquisition.py'):(p/'tools'/f).write_text('TEST')
        for f in ('run_freeze.cmd','run_install.cmd'):(p/f).write_text('TEST')
        (p/'run_all.cmd').write_text('rem TEST ONLY')
        (p/'README.md').write_text('TEST ONLY')
        assert contract(p)['registration_count']==271
        cfg['response_budgets']['BASIC']['checkpoints']=[32,513]
        (p/'configs'/'default.json').write_text(json.dumps(cfg))
        try:contract(p);raise AssertionError('Tampered fixed checkpoint was accepted')
        except ValueError:pass
    print('A058 SELFTEST PASS (mock configuration only); real Windows KnotPlot = NOT_RUN')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['SELFTEST','TRIAGE','PREPARE','STATUS','INSTALL','FREEZE','BASIC','2048','32768','FULL'])
    p.add_argument('--source',help='Absolute path to complete original A058-v0.2.9 folder')
    p.add_argument('--analysis');p.add_argument('--ledger');p.add_argument('--runlog')
    a=p.parse_args()
    if a.mode=='SELFTEST':selftest()
    elif a.mode=='TRIAGE':triage(a.analysis,a.ledger,a.runlog)
    elif a.mode=='PREPARE':guard(a.source,'Use --source path to actual local complete v0.2.9 tree');prepare(a.source)
    elif a.mode=='STATUS':status()
    else:launch(a.mode)
if __name__=='__main__':
    try:main()
    except Exception as e:print('FAIL-CLOSED:',e,file=sys.stderr);sys.exit(2)
