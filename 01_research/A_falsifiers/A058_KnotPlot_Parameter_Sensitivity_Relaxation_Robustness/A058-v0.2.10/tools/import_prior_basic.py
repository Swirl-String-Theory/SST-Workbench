"""Read-only source audit and local copy for a historical BASIC acquisition.

Never updates the historical frozen BLIND run, its ledger, or its runlog.
A separate, provenance-bound overlay describes six-decimal display consistency.
"""
from __future__ import annotations
from pathlib import Path
import sys,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.budget_acquisition import loadj,savej
from tools.run_knotplot_campaign import _state_ok,_sha256
from experiment.metrics import read_xyz

def audit_prior(source_root:Path):
    src=source_root/'campaign/runs/BASIC'
    if not (source_root/'falsifier.toml').is_file() or 'v0.2.9' not in (source_root/'falsifier.toml').read_text(encoding='utf-8'):
        raise RuntimeError('source must be the intact historical A058 v0.2.9 instance root')
    priv=loadj(ROOT/'private/axis_map.json')
    cal=loadj(source_root/'private/install_test_runtime/defaults.json')
    runs=loadj(src/'runlog.json');man=loadj(src/'manifest.json');runtime=loadj(src/'runtime.json')
    source_seed=(source_root/'private/install_test_runtime/trefoil_install_test.txt')
    if _sha256(source_seed)!=runtime['shared_seed_sha256'] or runtime['shared_seed_sha256']!=cal['shared_seed_sha256']:
        raise RuntimeError('historical acquisition seed provenance mismatch')
    byid={c['condition_id']:c for c in man['conditions']}
    if len(byid)!=271 or len(runs['conditions'])!=271 or runtime.get('iterations_per_condition')!=512:
        raise RuntimeError('source is not the complete registered 271-condition BASIC campaign')
    evidence={};qualified=0;rounded_recovered=0
    for row in runs['conditions']:
        cid=row['condition_id'];c=byid[cid]
        fail={'qualified':False,'original_status':row['status'],'evidence':'NOT_QUALIFIED'}
        evidence[cid]=fail
        if row['status'] not in ('PASS','FAIL'):continue
        if not (row.get('returncode')==0 and row.get('iterations')==512 and
                row.get('iteration_counter_verified') is True and
                row.get('safe_start_verified') is True and row.get('safe_final_verified') is True and
                row.get('shared_seed_sha256')==runtime['shared_seed_sha256'] and
                row.get('checkpoints')==[32,128,512]):continue
        folder=src/'results'/cid;fin=folder/'final.txt';log=source_root/'private/campaign_logs/BASIC'/f'{cid}.log'
        if not fin.is_file() or not log.is_file() or _sha256(fin)!=row.get('final_sha256'):
            continue
        if any(not (folder/f'checkpoint_{t:06d}.txt').is_file() for t in (32,128,512)):continue
        try:
            if len(read_xyz(fin))!=300:continue
            txt=log.read_text(encoding='utf-8',errors='replace')
            if 'unknown command' in txt.casefold() or 'freeglut error' in txt.casefold():continue
            a,sa=_state_ok(txt,c,priv,cal,'A058_PARAMETER_STATE_BEGIN','A058_PARAMETER_STATE_END')
            b,sb=_state_ok(txt,c,priv,cal,'A058_FINAL_STATE_BEGIN','A058_FINAL_STATE_END')
            if not a or not b:continue
            deltas=[v['abs_error'] for d in (sa,sb) for v in d['getter_evidence'].values() if v['abs_error'] is not None]
            max_delta=max(deltas,default=0.0)
        except Exception:
            continue
        qualified+=1;rounded_recovered+=row['status']=='FAIL'
        evidence[cid]={'qualified':True,'original_status':row['status'],
            'evidence':'ROUNDED_GETTER_6_DECIMALS_NOT_INTERNAL_FP64',
            'max_getter_abs_delta':max_delta,
            'final_sha256':_sha256(fin),'private_log_sha256':_sha256(log),
            'checkpoints':[32,128,512], 'iterations':512,'safe_verified':True}
    overlay={'schema':'A058-HISTORICAL-BASIC-AUDIT-OVERLAY-1',
        'original_release':'v0.2.9','qualifying_release':'v0.2.10',
        'original_runlog_sha256':_sha256(src/'runlog.json'),
        'original_manifest_sha256':_sha256(src/'manifest.json'),
        'original_runtime_sha256':_sha256(src/'runtime.json'),
        'original_seed_sha256':_sha256(source_seed),
        'population':271,'qualified_count':qualified,'recovered_from_original_fail':rounded_recovered,
        'conditions':evidence,
        'limits':['Historical frozen reports/gates unchanged',
            'Getter comparison proves displayed consistency only, not internal FP64 identity',
            'Unsupported runtime lane remains ineligible']}
    if qualified==0:raise RuntimeError('No historical conditions passed raw-evidence requalification')
    return src,overlay

def main():
    if len(sys.argv)!=2:raise SystemExit('Usage: run_all.cmd IMPORT_BASIC "C:\\path\\to\\A058-v0.2.9"')
    source=Path(sys.argv[1]).expanduser().resolve()
    src,overlay=audit_prior(source)
    dest=ROOT/'campaign/runs/BASIC'
    if dest.exists():raise RuntimeError('Target BASIC already exists. Preserve it; do not overwrite or merge.')
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(src,dest)
    # Bind copied bytes again; originals must never be rewritten.
    if _sha256(dest/'runlog.json')!=overlay['original_runlog_sha256'] or _sha256(dest/'manifest.json')!=overlay['original_manifest_sha256']:
        shutil.rmtree(dest);raise RuntimeError('Copied historical manifest/runlog differs from the qualified source')
    savej(dest/'qualification_overlay.json',overlay)
    print(f'IMPORTED historical BASIC: {overlay["qualified_count"]}/271 display-consistent; '+
        f'{overlay["recovered_from_original_fail"]} original FAIL rows recovered in separate overlay.')
    print('Original v0.2.9 instance, runlog and frozen BLIND artifacts were not modified.')
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        print('A058 IMPORT FAIL:',type(e).__name__,str(e),file=sys.stderr)
        raise SystemExit(2)
