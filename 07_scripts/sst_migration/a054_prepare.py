"""Admit the explicitly authorized A054 source and create an isolated successor."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tomllib
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha, atomic, locked, now
from phase3_prepare import snapshot, create_json

OUT = ROOT/'10_docs/migration_v110/a054_controlled_20261026'
FAMILY = ROOT/'01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier'
TARGET = FAMILY/'A054-v0.6.0'
E010 = ROOT/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
E011 = ROOT/'01_research/E_pipelines/E011_sklsa_selected_knot_link_seed_atlas/E011-v0.3.0/E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs'
E013 = ROOT/'01_research/E_pipelines/E013_PKLSA_Cross_Falsifier_Campaign/E013-v0.1.1'


def main():
    OUT.mkdir(exist_ok=False)
    state = ROOT/'10_docs/migration_v110/pilot_20261026'
    original = state/'queue.json'
    before = read(original)
    create_json(OUT/'queue.before.json', before)
    assert read(OUT/'queue.before.json') == before
    create_json(OUT/'PRESERVATION_BEFORE.json', {
        'A054-v0.5.1':snapshot(FAMILY/'A054-v0.5.1'),
        'family_sha256':sha(FAMILY/'FAMILY.yaml'),
        'A011_latest_sha256':sha(ROOT/'01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.4.1/LATEST_RUN.json'),
        'A065_family_sha256':sha(ROOT/'01_research/A_falsifiers/A065_Triadic_Casimir_Blind/FAMILY.yaml')})
    archive = Path(r'C:\Users\oscar\Downloads\A054_E013_State_Selection_Provider_Convergence_Falsifier_v0.5.1.zip')
    expected = next(x for x in read(ROOT/'10_docs/migration_v110/phase2_20261026/pilot_source_archive_comparisons.json') if x['pilot']=='A054')
    assert sha(archive) == expected['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest_name = next(n for n in z.namelist() if n.endswith('/PACKAGE_MANIFEST.json'))
        prefix = manifest_name[:-len('PACKAGE_MANIFEST.json')]
        manifest = json.loads(z.read(manifest_name))
        assert len(manifest['files']) == 59
        for row in manifest['files']:
            assert hashlib.sha256(z.read(prefix+row['path'])).hexdigest() == row['sha256']
        admission = {'schema':'A054-SOURCE-ADMISSION-1','status':'PASS_EXPLICIT_USER_ADMISSION',
                     'source_archive':str(archive),'archive_sha256':sha(archive),'manifest_entries_verified':59,
                     'authorization':'User explicitly selected: Bron toelaten voor begrensde softwaremigratie',
                     'provenance_limit':expected['provenance_limit'],
                     'scope':'Bounded software migration only; no physical certification, reveal or full campaign',
                     'private_source_entries':'Hash verification only; never interpreted or copied into the successor',
                     'admitted_utc':now()}
        create_json(OUT/'SOURCE_ADMISSION.json',admission)
        # A new version is created only after source admission passes.
        TARGET.mkdir(exist_ok=False)
        (TARGET/'provenance').mkdir()
        (TARGET/'provenance/PARENT_PACKAGE_MANIFEST.json').write_bytes(z.read(manifest_name))
        for row in manifest['files']:
            rel = Path(row['path'])
            assert not rel.is_absolute() and '..' not in rel.parts
            if rel.parts[0] in {'private','preregistration'}:continue
            p = TARGET/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(z.read(prefix+row['path']))
    create_json(TARGET/'provenance/SOURCE_ADMISSION.json',admission)
    pin = read(ROOT/'01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.4.1/FRAMEWORK_SOURCE_PIN.json')
    qualified = ROOT/pin['selected_source']
    for row in pin['verification']:assert sha(qualified/row['path']) == row['sha256']
    create_json(TARGET/'FRAMEWORK_SOURCE_PIN.json',pin)
    (TARGET/'.sst_framework_root').write_text(str(qualified)+'\n',encoding='utf-8')
    for p in TARGET.rglob('*'):
        if not p.is_file() or 'provenance' in p.parts:continue
        if p.suffix not in {'.py','.md','.json','.toml','.tex','.cmd'}:continue
        text = p.read_text(encoding='utf-8')
        p.write_text(text.replace('v0.5.1','v0.6.0').replace('Framework v1.0.6','Framework v1.0.10').replace('framework_version = "1.0.6"','framework_version = "1.0.10"'),encoding='utf-8')
    member = read(TARGET/'cross_falsifier_contract.json')
    member['enabled'] = False  # Historical enabled v0.5.1 is preserved; explicit local binding only.
    member['fresh_output_contract']['framework_output_name']='A054_E013_State_Selection_Provider_Convergence_Falsifier_v0.6.0_outputs'
    atomic(TARGET/'cross_falsifier_contract.json',member)
    # Reuse E013's actual selector, without launching its campaign orchestrator.
    tool = E013/'tools/run_cross_falsifier.py'
    spec = importlib.util.spec_from_file_location('a054_e013_selector',tool)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    configs = sorted((E013/'config').glob('*.json'))
    campaign = next(p for p in configs if 'campaign_version' in read(p))
    topologies = next(p for p in configs if 'topologies' in read(p))
    (TARGET/'admission').mkdir()
    manifest_path = TARGET/'admission/CROSS_CARRIER_MANIFEST.json'
    fresh, _ = module.build_manifest(E011,read(campaign),read(topologies),'BASIC',manifest_path)
    assert fresh['selected_carrier_count'] == 5
    contract = read(ROOT/'10_docs/migration_v110/phase2_20261026/A054_DATASET_ADMISSION.json')
    assert sha(E011/'STATIC_READY_INDEX.json') == contract['dataset_pins']['STATIC_READY_INDEX.json']
    assert sha(E011/'STATIC_READY_PROVIDER_ANCHORS.jsonl') == contract['dataset_pins']['STATIC_READY_PROVIDER_ANCHORS.jsonl']
    pins = {'schema':'A054-RUNTIME-ADMISSION-PINS-1','expected_manifest_sha256':sha(manifest_path),
            'e011_index':{'path':str((E011/'STATIC_READY_INDEX.json').relative_to(ROOT)),'sha256':sha(E011/'STATIC_READY_INDEX.json')},
            'e011_anchors':{'path':str((E011/'STATIC_READY_PROVIDER_ANCHORS.jsonl').relative_to(ROOT)),'sha256':sha(E011/'STATIC_READY_PROVIDER_ANCHORS.jsonl')},
            'e010_root':str(E010.relative_to(ROOT)),
            'e010_loader_files':{str(p.relative_to(E010)):sha(p) for p in sorted((E010/'pklsa_builder').glob('*.py'))},
            'e010_production':str((E010/'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs').relative_to(ROOT)),
            'scientific_provider_minimum':contract['predicate']['independent_provider_groups_min']}
    create_json(TARGET/'admission/RUNTIME_PINS.json',pins)
    create_json(TARGET/'admission/MEMBER_BINDING.json',{'schema':'A054-FRESH-MEMBER-BINDING-1','catalog_id':'A054','version':'v0.6.0','stage':30,
        'enabled_for_global_discovery':False,'mode':'ADMISSION_SMOKE','selected_carriers':5,
        'manifest_sha256':sha(manifest_path),'member_contract_sha256':sha(TARGET/'cross_falsifier_contract.json'),
        'selector_sha256':sha(tool),'campaign_config_sha256':sha(campaign),'topology_config_sha256':sha(topologies),
        'freshly_generated_from_current_e011':True,'historical_results_used':False})
    config_path = Path.home()/'.codex/automations/sst-workbench-dagelijkse-migratiecontrole/automation.toml'
    automation = tomllib.loads(config_path.read_text(encoding='utf-8'))
    assert automation['status'] == 'ACTIVE'
    with locked(state):
        q = read(original)
        assert q == before
        q['scheduled_control']['status']='ACTIVE'
        q['scheduled_control'].pop('pause_reason',None)
        q['scheduled_control']['resumed_utc']=now()
        q['scheduled_control']['schedule_current']='Daily 04:00 Europe/Amsterdam'
        j = next(j for j in q['jobs'] if j['id']=='A054')
        j['status']='CONTROLLED_MIGRATION_IN_PROGRESS'
        j['controlled_authorization']={'scope':'One A054 bounded software migration; no full campaign or reveal','source_admission':str((OUT/'SOURCE_ADMISSION.json').relative_to(ROOT)),'status':'EXPLICIT_USER_AUTHORIZATION'}
        q['scheduling_enabled']=False
        atomic(original,q)
    create_json(OUT/'SCHEDULE_RESUMED.json',{'automation_id':automation['id'],'status':'ACTIVE','kind':automation['kind'],
        'target_thread_id':automation['target_thread_id'],'rrule':automation['rrule'],'timezone':'Europe/Amsterdam',
        'configuration_sha256':sha(config_path),'campaign_release_enabled':False})
    print(json.dumps({'source_gate':'PASS_59_FILES','target':str(TARGET),'framework_files':112,'fresh_manifest_carriers':5,'schedule':'ACTIVE'}))


if __name__ == '__main__':main()
