"""Publish this scheduled checkpoint only after PDF render and visual review."""
from datetime import datetime,timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(r'C:\workspace\projects\SST-Workbench')
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'07_scripts/sst_migration'))
from preflight import read,sha,atomic,locked


def create(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2);stream.write('\n')


def main():
    from pypdf import PdfReader
    check=read(OUT/'CHECKS.json')
    pdf=OUT/'A054_Scheduled_Status.pdf'
    reader=PdfReader(pdf)
    assert len(reader.pages)==3
    text='\n'.join(p.extract_text() for p in reader.pages)
    for expected in ['A054-v0.6.0','233','112','70','NOT_RUN','L2a1']:
        assert expected in text,expected
    late_errors=[]
    for row in read(OUT/'INPUT_HASHES.json'):
        if row['path'].endswith('run.lock') or row['path'].endswith('pilot_20261026\\queue.json'):continue
        if sha(row['path'])!=row['sha256']:late_errors.append({'type':'ConcurrentInputDrift','message':row['path']})
    if late_errors:
        create(OUT/'LATE_INTEGRITY_ERRORS.json',late_errors)
    failure=bool(check['errors'] or late_errors)
    result={'schema':'SST-SCHEDULED-RESULT-1','run_id':OUT.name,'automation_id':check['automation_id'],
       'trigger_utc':check['trigger_utc'],'started_utc':check['started_utc'],'finished_utc':datetime.now(timezone.utc).isoformat(),
       'timezone':'Europe/Amsterdam','falsifier':'A054','version':'v0.6.0','falsifiers_processed':1,
       'status':'STOP_INTEGRITY_FAILURE' if failure else check['status'],'gate_axes':check['gate_axes'],
       'checks_file':str((OUT/'CHECKS.json').relative_to(ROOT)),'checks_sha256':sha(OUT/'CHECKS.json'),
       'hash_inventory_sha256':sha(OUT/'INPUT_HASHES.json'),'geometry_verification_sha256':sha(OUT/'GEOMETRY_VERIFICATION.json'),
       'pdf':str(pdf.relative_to(ROOT)),'pdf_sha256':sha(pdf),'pdf_pages':3,'pdf_render_exit_code':0,'pdf_visually_inspected':True,
       'render_note':'Poppler reported unused system font configuration warnings; all three rendered pages were visually verified.',
       'source_framework_entries_verified':112,'a054_source_inventory_files_verified':70,'admitted_geometries_verified':5,
       'blockers':check['blockers'],'next_action':check['next_action'],'new_version_created':False,
       'scientific_status_promoted':False,'scientific_evaluators_executed':False,'reveal_performed':False,
       'errors':check['errors']+late_errors,'notification_decision':'NOTIFY' if failure else 'DONT_NOTIFY',
       'notification_reason':'Unexpected integrity failure requires attention' if failure else 'Integrity healthy; previously reported scientific release and provider-coverage limitations unchanged'}
    # Record the completed, create-only status before exposing its queue pointer.
    create(OUT/'result.json',result)
    state=ROOT/'10_docs/migration_v110/pilot_20261026'
    with locked(state):
        qp=state/'queue.json'
        assert sha(qp)==check['queue_before_sha256'],'Concurrent queue change; do not overwrite'
        q=read(qp);old=deepcopy(q)
        assert q['scheduling_enabled'] is False and q['pilot_validated'] is False
        selected=next(j for j in q['jobs'] if j['id']=='A054')
        old_axes={k:selected[k] for k in ['migration_gate','execution_gate','scientific_gate']}
        selected['last_scheduled_check']={'run_id':OUT.name,'status':result['status'],
            'result':str((OUT/'result.json').relative_to(ROOT)),'checked_utc':result['finished_utc'],
            'integrity':'FAIL' if failure else 'PASS','scientific_status_promoted':False}
        assert all(selected[k]==v for k,v in old_axes.items())
        q['scheduled_control']['latest_scheduled_run']=str((OUT/'result.json').relative_to(ROOT))
        for before,after in zip(old['jobs'],q['jobs']):
            if before['id']!='A054':assert before==after
        atomic(qp,q)
        assert read(qp)==q
    with (ROOT/'10_docs/migration_v110/scheduled_control/execution_log.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'run_id':OUT.name,'falsifier':'A054','status':result['status'],'result':str((OUT/'result.json').relative_to(ROOT)),
            'scientific_gate':check['gate_axes']['scientific_gate'],'notification_decision':result['notification_decision'],'manual_user_triggered':False})+'\n')
    create(OUT/'QUEUE_UPDATE.json',{'status':'PASS','queue_before_sha256':check['queue_before_sha256'],
       'queue_after_sha256':sha(state/'queue.json'),'other_falsifier_jobs_unchanged':True,'scientific_gate_axes_unchanged':True,
       'pilot_validated':False,'campaign_release_enabled':False})
    rows=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file()]
    create(OUT/'ARTIFACT_SHA256.json',{'schema':'SST-SCHEDULED-ARTIFACT-HASHES-1','files':rows})
    print(json.dumps({'run_id':OUT.name,'status':result['status'],'pdf_pages':3,'notification_decision':result['notification_decision']}))


if __name__=='__main__':main()
