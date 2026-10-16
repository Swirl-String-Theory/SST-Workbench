#!/usr/bin/env python3
"""Detached A058 32768 selector lock. Never edits source protocol or BLIND results.

Commands:
  python locked_heavy.py CHECK path_to_A058-v0.2.10
  python locked_heavy.py VERIFY path_to_A058-v0.2.10

All source-dependent heavy selection is delegated to the exact unmodified
A058-v0.2.10 scientific selection implementation, then verified bytewise.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import sys
from collections import Counter

HERE=Path(__file__).resolve().parent

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def hash_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()

def verify_sha(path,expected,meaning):
    if not Path(path).is_file():
        raise RuntimeError(f'{meaning} missing: {path}')
    actual=hash_file(path)
    if actual!=expected:
        raise RuntimeError(f'{meaning}: hash mismatch ({actual} != {expected})')

def canonical_json_bytes(obj):
    return (json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')

def verify_precondition(root):
    root=Path(root).resolve()
    lock=load(HERE/'HEAVY_SELECTION_LOCK.json')
    line=(HERE/'HEAVY_SELECTION_LOCK.sha256').read_text(encoding='ascii').strip().split()[0]
    verify_sha(HERE/'HEAVY_SELECTION_LOCK.json',line,'self-commitment')
    verify_sha(HERE/'SELECTION_ENGINE_EXPECTED.json',lock['selection_detail_hash_sha256'],'pinned selector output')
    if lock['source_version']!='v0.2.10':raise RuntimeError('wrong source version in lock')
    if not (root/'falsifier.toml').is_file():raise RuntimeError('select an intact A058-v0.2.10 instance root')
    txt=(root/'falsifier.toml').read_text(encoding='utf-8')
    if 'v0.2.10' not in txt:raise RuntimeError('instance must be A058-v0.2.10')
    for rel, expected in lock['source_program_sha256'].items():
        verify_sha(root/rel,expected,'source version '+rel)
    source=root/'campaign/runs/2048'
    for name,expected in lock['source_2048_file_sha256'].items():
        verify_sha(source/name,expected,'original 2048 '+name)
    verify_sha(root/'private/install_test_runtime/trefoil_install_test.txt',lock['immutable_shared_seed_sha256'],'shared seed')
    for cid,expected in lock['source_2048_pass_final_sha256'].items():
        verify_sha(source/'results'/cid/'final.txt',expected,'original 2048 final '+cid)
    runlog=load(source/'runlog.json')
    conditions=runlog.get('conditions',[])
    if len(conditions)!=lock['registered_conditions'] or len({c['condition_id'] for c in conditions})!=len(conditions):
        raise RuntimeError('source condition population is not complete/unique')
    counts=Counter(r['status'] for r in conditions)
    if {k:counts.get(k,0) for k in lock['source_status_counts']}!=lock['source_status_counts'] or set(counts).difference(lock['source_status_counts']):
        raise RuntimeError(f'condition status drift: {dict(counts)}')
    if any(x['iterations']!=2048 or x['checkpoints']!=[32,128,512,2048] or
           not x.get('parameter_state_verified') or not x.get('safe_final_verified') or
           not x.get('iteration_counter_verified') for x in conditions if x['status']=='PASS'):
        raise RuntimeError('2048 qualified condition lost provenance/iteration/safety checks')
    if any(x['condition_id'] in lock['selected_ids'] and x['status']!='PASS' for x in conditions):
        raise RuntimeError('selected case is not qualified PASS')
    runtime=load(source/'runtime.json')
    if runtime.get('source_executable_sha256')!=lock['knotplot_executable_sha256']:
        raise RuntimeError('source KnotPlot executable identity mismatch in 2048')
    exe=Path(runtime.get('source_executable',''))
    verify_sha(exe,lock['knotplot_executable_sha256'],'live KnotPlot executable')
    # Import the existing, not reimplemented, deterministic selector. No reveal data used.
    sys.path.insert(0,str(root))
    from tools.run_budget import heavy_selection,loadj
    computed_cases,computed=heavy_selection(loadj(root/'campaign/manifest_pilot.json'),source)
    expected=load(HERE/'SELECTION_ENGINE_EXPECTED.json')
    if canonical_json_bytes(computed)!=canonical_json_bytes(expected):
        raise RuntimeError('native selector recomputation differs from pinned 2048 decision')
    ids=[x['condition_id'] for x in computed_cases]
    if ids!=lock['selected_ids'] or len(ids)!=lock['selected_count']:
        raise RuntimeError('selected IDs/order differ from locked set')
    if set(ids)!=set(x['condition_id'] for x in lock['selection_rows']):
        raise RuntimeError('lock rows and selected IDs disagree')
    if (root/'campaign/runs/32768').is_dir():
        raise RuntimeError('32768 output directory already exists; use VERIFY or preserve/rename it explicitly')
    print(f'CHECK PASS: {len(ids)} precommitted BLIND conditions, complete 2048 provenance, source executable and seed intact.')
    print('SELECTION-LOCK SHA256:',line)
    print('SELECTED:', ' '.join(ids))
    print('TOTAL MAX go iterations:',len(ids)*32768)
    return lock

def verify_after(root):
    root=Path(root).resolve()
    lock=load(HERE/'HEAVY_SELECTION_LOCK.json')
    line=(HERE/'HEAVY_SELECTION_LOCK.sha256').read_text(encoding='ascii').strip().split()[0]
    verify_sha(HERE/'HEAVY_SELECTION_LOCK.json',line,'self-commitment')
    p=root/'campaign/runs/32768'
    sel=load(p/'selection.json')
    exp=load(HERE/'SELECTION_ENGINE_EXPECTED.json')
    if canonical_json_bytes(sel)!=canonical_json_bytes(exp):
        raise RuntimeError('actual saved heavy selection differs from sealed decision')
    runs=load(p/'runlog.json')
    count=Counter(c['status'] for c in runs.get('conditions',[]))
    actual_ids=[c['condition_id'] for c in runs.get('conditions',[])]
    if actual_ids!=lock['selected_ids']:
        raise RuntimeError('executed run ID order differs from precommitment')
    artifact={
      'schema':'A058-DETACHED-HEAVY-VERIFICATION-1',
      'decision_sha256':line,
      'selected_ids':actual_ids,
      'runlog_sha256':hash_file(p/'runlog.json'),
      'saved_selection_sha256':hash_file(p/'selection.json'),
      'run_status_counts':dict(count),
      'result':'SELECTION_MATCH',
      'science_gate_claim':'NO; consult G0-G9 BLIND report and individual runtime records',
    }
    dst=HERE/'HEAVY_RUN_MATCH_AUDIT.json'
    dst.write_bytes(canonical_json_bytes(artifact))
    print('VERIFY PASS: exact original BLIND selection was executed; conditions=',len(actual_ids))
    print('HEAVY status:',dict(count))
    print('Audit:',dst)

def main():
    if len(sys.argv)!=3 or sys.argv[1].upper() not in ('CHECK','VERIFY'):
        raise RuntimeError('Usage: locked_heavy.py CHECK|VERIFY <path-to-A058-v0.2.10>')
    mode=sys.argv[1].upper()
    if mode=='CHECK':verify_precondition(sys.argv[2])
    else:verify_after(sys.argv[2])

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('LOCKED HEAVY ERROR:',type(exc).__name__+':',exc,file=sys.stderr)
        raise SystemExit(2)
