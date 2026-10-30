"""Acceptance audit for a real E010 A999 FULL run.
Never turns a numerical integration control into a physical validation.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sst_falsifier.outputs import verify_output_manifest,verify_science_evidence_manifest
from sst_falsifier.auto_backend_matrix import assess_numeric_control
from sst_falsifier.config import load_instance_config
from sst_falsifier.runner import instance_output_root
from sst_falsifier.output_policy import read_run_id

def audit(instance):
    instance=Path(instance).expanduser().resolve();cfg=load_instance_config(instance)
    output=instance_output_root(instance,cfg)
    failures=[]
    def check(name, condition,detail=''):
        if not condition:failures.append(name+(': '+detail if detail else ''))
    def load(name):
        path=output/name
        try:return json.loads(path.read_text(encoding='utf8'))
        except Exception as exc:failures.append('missing/unreadable '+name+': '+str(exc));return {}
    matrix=load('AUTO_BACKEND_MATRIX.json'); ledger=load('GATE_LEDGER.json');render=load('REPORT_RENDER_BLIND.json')
    summary=load('RUN_SUMMARY.json');source=load('SOURCE_MANIFEST.json')
    check('execution status',matrix.get('status')=='EXECUTION_CONTRACT_PASS')
    check('python reference executed',matrix.get('scientific',{}).get('py',{}).get('scientific_execution') is True)
    check('2of3 counted',matrix.get('counted_backend_categories',0)>=2)
    check('shared input/time',matrix.get('same_input_and_time') is True)
    verdict=assess_numeric_control(matrix,cfg.get('auto_backends',{}))
    check('independent numeric parity',verdict['status']=='PASS',verdict['reason'])
    records={r['gate_id']:r for r in ledger.get('records',[])}
    check('G0/G1/G2/G10 measured PASS',all(records.get(g,{}).get('status')=='PASS' for g in ('G0','G1','G2','G10')))
    check('G10 evidence qualified',records.get('G10',{}).get('qualification')=='QUALIFIED')
    check('PDF normal LaTeX render',render.get('success') is True and render.get('status')=='PASS')
    check('source manifest tracks E010',any(s.get('catalog_id')=='E010' and s.get('exists') for s in source.get('sources',[])))
    # RC2 admission must include actual phase checkpoints, not merely live heartbeat.
    journal=output/'RUN_PROGRESS.jsonl'
    try:
        events=[json.loads(line) for line in journal.read_text(encoding='utf8').splitlines()]
    except Exception as ex:
        failures.append('RC2 progress journal missing/unreadable: '+str(ex))
        events=[]
    check('RC2 progress journal format',len(events)>0 and all(e.get('schema')=='SST-RUN-PROGRESS-1' for e in events))
    check('RC2 science checkpoint',any(e.get('phase')=='SCIENCE_PIPELINE' and e.get('state')=='DONE' for e in events))
    done_backends={e.get('backend') for e in events if e.get('phase')=='BACKEND' and e.get('state')=='DONE'}
    counted=set(matrix.get('executed_backend_categories',[]))
    check('RC2 per-backend progress coverage',counted.issubset(done_backends),f'expected {sorted(counted)}, got {sorted(done_backends)}')
    try:
        ok,why=verify_output_manifest(output,output/'OUTPUT_MANIFEST.json');check('output manifest',ok,str(why))
        ok,why=verify_science_evidence_manifest(output,output/'SCIENCE_EVIDENCE_MANIFEST.json');check('immutable science manifest',ok,str(why))
    except Exception as ex:failures.append('manifest verification error: '+str(ex))
    report=Path(render.get('destination',''))
    check('published PDF exists',report.is_file() and report.read_bytes()[:5]==b'%PDF-')
    try:
        runid=read_run_id(output)
        zip_candidates=list(instance.parent.glob('*'+runid+'*_BLIND.zip'))
        check('unique blind ZIP publication',len(zip_candidates)==1)
        if len(zip_candidates)==1:
            z=zip_candidates[0];side=Path(str(z)+'.sha256')
            import zipfile
            with zipfile.ZipFile(z) as archive:
                check('RC2 progress journal archived',any(path.endswith('RUN_PROGRESS.jsonl') for path in archive.namelist()))
            check('ZIP hash sidecar',side.is_file() and side.read_text().split()[0]==hashlib.sha256(z.read_bytes()).hexdigest())
    except Exception as ex:failures.append('run-id/archive verification error: '+str(ex))
    return {'schema':'SST-A999-E010-RELEASE-ACCEPTANCE-1',
            'instance':str(instance),'output':str(output),'status':'PASS_TECHNICAL_INTEGRATION_ONLY' if not failures else 'NOT_CERTIFIED',
            'numerical_verdict':verdict,'executed_backend_categories':matrix.get('executed_backend_categories',[]),
            'progress_events':len(events),'progress_done_backends':sorted(done_backends),
            'report_pdf':str(report) if report.is_file() else None,
            'failures':failures,'physical_certification':'NOT_EVALUATED',
            'note':'This verifies an A999 E010 numerical software integration, not an SST physical falsifier.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--instance',required=True);p.add_argument('--output')
    a=p.parse_args();result=audit(a.instance)
    dump=json.dumps(result,indent=2,sort_keys=True)+'\n';print(dump,end='')
    if a.output:
        out=Path(a.output).expanduser().resolve()
        if out.exists():raise FileExistsError('Create-only output must not exist: '+str(out))
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(dump,encoding='utf8')
    raise SystemExit(0 if result['status']=='PASS_TECHNICAL_INTEGRATION_ONLY' else 3)
