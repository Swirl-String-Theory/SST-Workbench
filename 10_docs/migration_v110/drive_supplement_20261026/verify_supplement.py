"""Verify additional Drive evidence without changing historical artifacts."""
import difflib
import hashlib
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old_path = OUT/'queue.capture.drive.bin'
    old = read(old_path)
    current_path = ROOT/'10_docs/migration_v110/pilot_20261026/queue.json'
    current = read(current_path)
    schedule = read(ROOT/'10_docs/migration_v110/scheduled_control/SCHEDULE_REGISTRATION.json')
    assert sha(old_path) == schedule['queue_sha256_after']
    assert sha(OUT/'queue.current.drive.json') == sha(current_path)
    assert len(old['jobs']) == len(current['jobs'])
    changed_jobs = []
    for before, after in zip(old['jobs'], current['jobs']):
        assert before['id'] == after['id']
        if before['id'] != 'A011':
            assert before == after
        else:
            for axis in ['migration_gate', 'execution_gate', 'scientific_gate']:
                assert before[axis] == after[axis]
            allowed = {'run_id','status','report_output_restoration','reporting_gate','packaging_gate','latest_result','completed_version'}
            changed = sorted(k for k in set(before)|set(after) if before.get(k) != after.get(k))
            assert set(changed) == allowed
            changed_jobs.append({'id':before['id'],'changed_fields':changed})
    top_changes = sorted(k for k in set(old)|set(current) if old.get(k) != current.get(k))
    assert top_changes == ['jobs','report_output_contract','scheduled_control']
    assert not current['scheduling_enabled'] and not current['pilot_validated']
    assert current['scheduled_control']['status'] == 'PAUSED'
    automation_path = Path.home()/'.codex/automations/sst-workbench-dagelijkse-migratiecontrole/automation.toml'
    automation = tomllib.loads(automation_path.read_text(encoding='utf-8'))
    assert automation['status'] == 'PAUSED'
    pin = read(ROOT/'01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.4.1/FRAMEWORK_SOURCE_PIN.json')
    qualified = ROOT/pin['selected_source']
    metadata = []
    for name in ['CANONICAL_FREEZE','PACKAGE_MANIFEST','SOURCE_PROVENANCE','RELEASE_INFO']:
        drive = OUT/('framework.'+name+'.drive.json')
        local = qualified/(name+'.json')
        assert drive.read_bytes() == local.read_bytes()
        metadata.append({'file':name+'.json','sha256':sha(drive),'byte_identical_to_qualified_source':True})
    assert len(pin['verification']) == 112
    for row in pin['verification']:
        assert sha(qualified/row['path']) == row['sha256']
    dd = OUT/'framework.DD32_FP32X2.working.drive.md'
    sealed = qualified/'docs/DD32_FP32X2.md'
    working = ROOT/'06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10/docs/DD32_FP32X2.md'
    assert dd.read_bytes() == working.read_bytes() and dd.read_bytes() != sealed.read_bytes()
    diff = ''.join(difflib.unified_diff(sealed.read_text(encoding='utf-8').splitlines(True),dd.read_text(encoding='utf-8').splitlines(True),fromfile='qualified/docs/DD32_FP32X2.md',tofile='drive_working/docs/DD32_FP32X2.md'))
    with (OUT/'DD32_qualified_to_drive_working.diff').open('x',encoding='utf-8') as stream:
        stream.write(diff)
    original_capture = ROOT/'10_docs/migration_v110/report_contract_restoration_20261026/before_registration/10_docs/migration_v110/pilot_20261026/queue.json'
    assert sha(original_capture) == 'b231a06dc1cdc4e35c83a536d0271dc40ed0483d52c52b4b58d384d83e2d44a0'
    result = {'schema':'SST-DRIVE-SUPPLEMENT-VALIDATION-1',
              'status':'PASS_AUDIT_GAP_RESOLVED_WITH_RECOVERED_BASELINE',
              'recovered_baseline':{'path':old_path.name,'bytes':old_path.stat().st_size,'sha256':sha(old_path),'matches_previously_recorded_hash':True},
              'original_invalid_capture_preserved':True,'original_capture_sha256':sha(original_capture),
              'current_queue_sha256':sha(current_path),'current_queue_matches_drive_bytes':True,
              'changed_top_level_fields':top_changes,'changed_jobs':changed_jobs,
              'other_queue_jobs_unchanged':True,'scientific_axes_unchanged':True,
              'framework_metadata':metadata,'qualified_framework_files_verified':112,
              'drive_working_document':{'status':'KNOWN_VARIANT_NOT_ADMITTED','sha256':sha(dd),'bytes':dd.stat().st_size,'qualified_sha256':sha(sealed),'matches_preserved_local_working_variant':True},
              'scheduled_status':automation['status'],'scientific_status_promoted':False,
              'historical_artifacts_replaced':False,'drive_files_modified':False}
    with (OUT/'SUPPLEMENT_GATE_OVERVIEW.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
