"""Fail-closed analytic bridge. Never changes Workbench registered scientific status."""
import argparse,csv,datetime,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
from sttc import checks
from e011_audit import audit as audit_e011_zip

ROOT=Path(__file__).resolve().parent
NAME='SST_FrozenIn_Reconnection_Bridge_v0.1.0'
OUT=ROOT/(NAME+'-outputs')

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def audit_e011(path):
    if not path:
        return {'status':'NOT_RUN_SOURCE','note':'No E011 STATIC_READY atlas supplied; physical provider tests not performed.'}
    root=Path(path).resolve()
    names=['RUN_SUMMARY.json','SEED_CONTRACT_SCHEMA.json','PARENT_RELEASE.json',
           'STATIC_READY_PROVIDER_ANCHORS.jsonl','STATIC_READY_PRIMARY_SEEDS.jsonl']
    missing=[f for f in names if not (root/f).is_file()]
    if missing:return {'status':'BLOCKED_SOURCE','missing':missing,'path':str(root)}
    try:
        run=json.loads((root/names[0]).read_text(encoding='utf-8'))
        seed=json.loads((root/names[1]).read_text(encoding='utf-8'))
    except (ValueError,OSError) as e:return {'status':'BLOCKED_SOURCE','reason':str(e)}
    ok=(run.get('schema')=='E011-SKLSA-STATIC-READY-ATLAS-1'
        and run.get('execution_gate')=='PASS' and run.get('operational_error_count')==0
        and seed.get('schema')=='E011-STATIC-SEED-CONTRACT-1'
        and seed.get('dynamics_ready') is False)
    return {'status':'METADATA_PRECHECK_ONLY' if ok else 'BLOCKED_SOURCE',
            'note':'Full SHA256 carrier identity, provenance and science admission not certified here.',
            'metadata_hashes':{p:sha256(root/p) for p in names},'metadata_conditions_passed':ok}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',nargs='?',default='BASIC',choices=['SELFTEST','BASIC','FULL'])
    parser.add_argument('--e011',type=str,default=None)
    parser.add_argument('--e011-zip',type=str,default=None)
    parser.add_argument('--e011-sha256',type=str,default=None)
    args=parser.parse_args()
    if args.mode=='SELFTEST':
        ret=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
        return ret.returncode
    OUT.mkdir(parents=True,exist_ok=True)
    rows,diag=checks(args.mode)
    source=audit_e011_zip(args.e011_zip,args.e011_sha256) if args.e011_zip else audit_e011(args.e011)
    report={
        'schema':'SST-STTC-CONCEPT-1','version':'v0.1.0',
        'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'mode':args.mode,
        'scope':'Independent manufactured analytic controls, not run against user Euler finite-core trajectories',
        'status':('BLOCKED_SOURCE' if source.get('status')=='BLOCKED_SOURCE' else ('PASS_ANALYTIC_CONTROL_ONLY' if all(x['status']=='PASS_ANALYTIC_CONTROL' for x in rows) else 'FAIL_ANALYTIC_CONTROL')),
        'science':{'euler_knot_stability':'NOT_EVALUATED','reconnection_in_physical_SST':'NOT_EVALUATED',
                  'gravity_emergence':'NOT_EVALUATED','topology_convergence':'NOT_EVALUATED',
                  'e010_dynamic_seed_qualification':'NOT_EVALUATED'},
        'upstream':source,'tests':rows,'diagnostics':diag}
    # Always record the source status, including NOT_RUN, to prevent stale upstream evidence.
    (OUT/'DATASET_E011_READONLY.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'GATE_LEDGER.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'NUMERIC_CHECKS.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['check','value','tolerance','rule','status']);w.writeheader();w.writerows(rows)
    brief=['# STTC v0.1.0 - Evidence summary','','**'+report['status']+'**','',
           'This is an analytic manufactured-solution validation, NOT an SST physical confirmation.',
           'No native C++ Euler finite-core simulation, E010/E011 geometry campaign, or framework v1.0.10 promotion was run.','',
           '## Gate matrix','', '| Check | Metric | Threshold | Result |','|---|---:|---:|---|']
    for r in rows:brief.append(f"| {r['check']} | {r['value']:.6g} | {r['rule']} {r['tolerance']} | {r['status']} |")
    brief +=['','## Negative control','',
       f"Viscous Beltrami helicity: H0={diag['ABC_H0']:.12g}, H(t)={diag['ABC_Ht']:.12g}, t={diag['ABC_time']}, nu={diag['ABC_viscosity']}.",
       'Helicity decays while the direction field is unchanged: NOT reconnection.', '',
       '## Outstanding','', 'E011: '+source['status'],
       'Physical Euler trefoil / background interaction: NOT_EVALUATED.',
       'Full spatial/temporal/finite-core convergence: NOT_EVALUATED.',
       'Provider independent source hashes and blind evidence: NOT_EVALUATED.']
    (OUT/'RESULTS.md').write_text('\n'.join(brief)+'\n',encoding='utf-8')
    manifest={p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'outputs' not in str(p) and '__pycache__' not in str(p)}
    (OUT/'SOURCE_SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    zipfile_path=ROOT.parent/(NAME+'-outputs.zip')
    with zipfile.ZipFile(zipfile_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file(): z.write(p,arcname=p.relative_to(ROOT).as_posix())
    (ROOT.parent/(zipfile_path.name+'.sha256')).write_text(sha256(zipfile_path)+'  '+zipfile_path.name+'\n',encoding='utf-8')
    print('status:',report['status'],'tests:',len(rows),'e011:',source['status'])
    print('output:',OUT)
    print('archive:',zipfile_path)
    return 0 if report['status'].startswith('PASS') else 2

if __name__=='__main__':raise SystemExit(main())
