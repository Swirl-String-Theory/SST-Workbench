"""Scheduled A054 integrity check only: no scientific evaluator or migration run."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import tomllib
import traceback
import zipfile

sys.dont_write_bytecode=True
ROOT=Path(r'C:\workspace\projects\SST-Workbench')
OUT=Path(__file__).resolve().parent
TARGET=ROOT/'01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.6.0'
TOKEN='87ce858342ab462eae781f13543a06a1'
START='2026-10-27T03:03:28.287424+00:00'
hashes={}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def checked(path,expected=None):
    path=Path(path)
    actual=sha(path)
    assert expected is None or actual==expected,'INTEGRITY_MISMATCH: '+str(path)
    hashes[str(path)]={'path':str(path),'sha256':actual,'bytes':path.stat().st_size,'expected_sha256':expected}
    return path


def read(path):
    return json.loads(checked(path).read_text(encoding='utf-8-sig'))


def create(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2);f.write('\n')


def main():
    checks=[];errors=[];geometry=[];axes={}
    queue_path=ROOT/'10_docs/migration_v110/pilot_20261026/queue.json'
    before_bytes=checked(queue_path).read_bytes()
    with (OUT/'queue.before.json').open('xb') as f:f.write(before_bytes)
    assert (OUT/'queue.before.json').read_bytes()==before_bytes
    queue=json.loads(before_bytes)
    job=next(j for j in queue['jobs'] if j['id']=='A054')
    try:
        assert read(ROOT/'10_docs/migration_v110/scheduled_control/run.lock')['token']==TOKEN
        policy=queue['source_admission_policy']
        checked(ROOT/policy['path'],policy['sha256'])
        assert read(ROOT/policy['path'])['per_source_confirmation_required'] is False
        h=read(ROOT/'10_docs/registry/family_hierarchy.json')
        c=read(ROOT/'10_docs/registry/catalog_index.json')
        family=checked(TARGET.parent/'FAMILY.yaml').read_text(encoding='utf-8')
        assert h['hierarchy']['01_research']['A_falsifiers']['A054']['latest']=='v0.6.0'
        assert c['by_domain']['01_research']['A054']['latest']=='v0.6.0' and 'latest: v0.6.0' in family
        assert job['completed_version']=='A054-v0.6.0'
        assert not queue['pilot_validated'] and not queue['scheduling_enabled']
        checks.append({'check':'queue_registry_and_authorization','status':'PASS','scope':'Existing A054 checkpoint; preparatory controls only'})
        source=read(TARGET/'SOURCE_MANIFEST_v0.6.0.json')
        for row in source['files']:checked(TARGET/row['path'],row['sha256'])
        checks.append({'check':'a054_source_inventory','status':'PASS','files':len(source['files'])})
        fwq=read(ROOT/'10_docs/migration_v110/phase3_20261026/framework_source_qualification.json')
        pin=read(TARGET/'FRAMEWORK_SOURCE_PIN.json')
        assert fwq['selected_source']==pin['selected_source']
        assert fwq['distribution_sha256']==pin['distribution_sha256']
        assert len(pin['verification'])==112
        fw=ROOT/pin['selected_source']
        for row in pin['verification']:checked(fw/row['path'],row['sha256'])
        checks.append({'check':'qualified_framework','status':'PASS','manifest_entries':112,'source':pin['selected_source']})
        contract=read(ROOT/'10_docs/migration_v110/phase2_20261026/A054_DATASET_ADMISSION.json')
        patches=read(ROOT/'10_docs/migration_v110/phase2_20261026/required_patches.json')
        assert any(p['id']=='P04' for p in patches['patches'])
        checked(ROOT/'10_docs/migration_v110/phase2_20261026/geometry_hashes.jsonl',contract['geometry_audit_sha256'])
        read(ROOT/'10_docs/migration_v110/a054_controlled_20261026/gate_overview.json')
        result=read(ROOT/'10_docs/migration_v110/a054_controlled_20261026/RESULT.json')
        intake=read(ROOT/'10_docs/migration_v110/a054_controlled_20261026/SOURCE_ADMISSION.json')
        checked(Path(intake['source_archive']),intake['archive_sha256'])
        sys.path.insert(0,str(TARGET))
        from a054_state import admission,pklsa,migration
        migration.qualified_framework(TARGET)
        migration.verify_protocol(TARGET)
        pins=read(TARGET/'admission/RUNTIME_PINS.json')
        admitted=admission.validate_manifest(TARGET/'admission/CROSS_CARRIER_MANIFEST.json',ROOT,pins)
        for field in ['e011_index','e011_anchors','e010_release']:
            checked(ROOT/pins[field]['path'],pins[field]['sha256'])
        for rel,expected in pins['e010_loader_files'].items():checked(ROOT/pins['e010_root']/rel,expected)
        for row in admitted['manifest']['carriers']:
            comps,path,gh=pklsa._load_manifest_geometry(row,admitted['loader'],ROOT)
            checked(path,row['raw_sha256'])
            geometry.append({'topology_id':row['topology_id'],'carrier_id':row['carrier_id'],'static_seed_id':row['static_seed_id'],
                'provider_group':row['provider_group'],'raw_sha256':row['raw_sha256'],'geometry_sha256':gh,
                'expected_geometry_sha256':row['geometry_sha256'],'source_points':sum(len(c) for c in comps),'status':'PASS'})
        assert len(geometry)==5 and all(r['geometry_sha256']==r['expected_geometry_sha256'] for r in geometry)
        checks.append({'check':'pklsa_e011_e013_admission_and_geometry','status':'PASS','carriers':5,
            'loader_files':len(pins['e010_loader_files']),'provider_counts':admitted['provider_counts'],'scientific_provider_coverage':admitted['cross_provider_science_ready']})
        member=read(TARGET/'cross_falsifier_contract.json')
        assert member['enabled'] is False and member['stage']==30
        latest=read(TARGET/'LATEST_RUN.json')
        assert latest==result['latest']
        for p,expected in [(Path(latest['report_pdf']),latest['report_sha256']),
                           (Path(latest['archive']['zip']),latest['archive']['sha256']),
                           (Path(result['source_archive']),result['source_archive_sha256'])]:
            checked(p,expected)
        archive=Path(latest['archive']['zip'])
        assert checked(archive.with_suffix('.zip.sha256')).read_text().split()[0]==latest['archive']['sha256']
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for row in json.loads(z.read('OUTPUT_MANIFEST.json'))['files']:
                assert hashlib.sha256(z.read(row['relpath'])).hexdigest()==row['sha256']
        from sst_falsifier.outputs import verify_output_manifest,verify_science_evidence_manifest
        current_out=Path(latest['output_root'])
        assert verify_output_manifest(current_out,current_out/'OUTPUT_MANIFEST.json')[0]
        assert verify_science_evidence_manifest(current_out,current_out/'SCIENCE_EVIDENCE_MANIFEST.json')[0]
        data=read(current_out/'REPORT_DATA.json');ledger=read(current_out/'GATE_LEDGER.json')
        assert data['gates']==ledger['records']
        axes=latest['gate_axes']
        assert axes==read(current_out/'GATE_AXES.json')
        assert all(job[k]==axes[k] for k in ['migration_gate','execution_gate','scientific_gate'])
        assert axes['scientific_gate']=='NOT_RUN' and axes['scientific_status_promoted'] is False
        checks.append({'check':'prior_publications_manifests_and_gate_consistency','status':'PASS','run_id':latest['run_id']})
        cfg=Path.home()/'.codex/automations/sst-workbench-dagelijkse-migratiecontrole/automation.toml'
        automation=tomllib.loads(cfg.read_text(encoding='utf-8'))
        assert automation['status']=='ACTIVE' and automation['target_thread_id']=='01a1792b-9483-7721-ba03-8f7b244c837f'
        assert automation['rrule']=='FREQ=DAILY;BYHOUR=4;BYMINUTE=0;BYSECOND=0'
        import numpy as np
        environment={'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'cwd':str(ROOT),'automation_status':'ACTIVE','native_executed':False,'gpu_executed':False}
    except BaseException as error:
        errors.append({'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
        environment={'python':sys.version,'platform':platform.platform(),'cwd':str(ROOT),'native_executed':False,'gpu_executed':False}
    for path,row in hashes.items():
        if path!=str(queue_path) and not path.endswith('run.lock'):
            if sha(path)!=row['sha256']:errors.append({'type':'ConcurrentInputDrift','message':path})
    create('INPUT_HASHES.json',list(hashes.values()))
    create('GEOMETRY_VERIFICATION.json',geometry)
    create('CHECKS.json',{'schema':'SST-SCHEDULED-CONTROL-1','run_id':OUT.name,'automation_id':'sst-workbench-dagelijkse-migratiecontrole',
        'trigger_utc':'2026-10-27T03:03:19.612Z','started_utc':START,'checks_finished_utc':datetime.now(timezone.utc).isoformat(),
        'timezone':'Europe/Amsterdam','falsifier':'A054','version':'v0.6.0','falsifiers_processed':1,
        'status':'STOP_INTEGRITY_FAILURE' if errors else 'UNCHANGED_BLOCKED_WAITING_SCIENCE_RELEASE',
        'prior_status':job['status'],'gate_axes':axes or {k:job[k] for k in ['migration_gate','execution_gate','scientific_gate']},
        'checks':checks,'errors':errors,'environment':environment,'blockers':job['blockers'],
        'next_action':job['controlled_migration']['next_action'],
        'source_admission':'Standing user authorization; missing publisher signature is a recorded limit, not a new permission blocker',
        'new_version_created':False,'scientific_evaluators_executed':False,'scientific_status_promoted':False,
        'reveal_performed':False,'queue_before_sha256':hashlib.sha256(before_bytes).hexdigest()})
    print(json.dumps({'status':'FAIL' if errors else 'PASS_UNCHANGED','checks':len(checks),'carriers':len(geometry),'hashed_files':len(hashes),'errors':errors},indent=2))


if __name__=='__main__':main()
