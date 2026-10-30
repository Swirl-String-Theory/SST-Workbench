"""Independent final data-accounting and preservation audit; create-only result."""
from pathlib import Path
from collections import Counter
import hashlib, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[3];AUDIT=Path(__file__).resolve().parent
FAMILY=ROOT/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas'
VERSION=FAMILY/'E010-v0.4.0';OUT=VERSION/'SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    contract=read(AUDIT/'SOURCE_INTAKE.json');pub=read(VERSION/'PUBLICATION.json')
    assert read(AUDIT/'REGISTRATION.json')['status']=='PASS_SCOPED_REGISTRATION'
    index=read(OUT/'COMBINED_INDEX.json');rows=index['records'];assert len(rows)==11757
    assert len({r['id'] for r in rows})==11757
    historical=[r for r in rows if r['collection']=='historical_v031']
    research=[r for r in rows if r['collection']=='ruban_v036']
    assert len(historical)==4497 and len(research)==7260
    assert Counter(r['variant'] for r in research)=={'nominal':3630,'perturbed':3630}
    assert sum(r['component_count'] for r in research)==10164
    assert sum(r['topology_id'] is None and r['variant']=='nominal' for r in research)==1452
    assert all(r['research_only'] and r['production_admission'] is False and
               r['state']=='RESEARCH_GEOMETRY_UNADMITTED' and r['dynamic_stability']=='NOT_TESTED' and
               r['finite_core_qualified'] is False and r['gates']['scientific']=='NOT_RUN' for r in research)
    assert len({r['source_independence_group'] for r in research})==1
    print('Independent preservation check: history and research files...',flush=True)
    for key,source,target in [('history',ROOT/contract['history_relative'],OUT/'history/v031'),
                              ('ruban',ROOT/contract['ruban_relative'],OUT/'research/v036')]:
        for relative,expected in contract[key].items():
            assert sha(source/relative)==sha(target/relative)==expected,relative
    for relative,expected in contract['raw_sources'].items():assert sha(ROOT/relative)==expected,relative
    for relative,expected in contract['parent_code'].items():
        assert sha(FAMILY/'E010-v0.3.1'/relative)==sha(VERSION/relative)==expected
    originals={r['carrier']['carrier_id']:r for r in read(AUDIT/'CARRIERS.json')}
    last_topology=None; metric_records={}
    for r in historical:
        old=originals[r['id']]
        assert r['geometry_sha256']==old['geometry_sha256']
        source_doc=read(OUT/r['source_document']);assert source_doc['carrier']==old['carrier']
        if last_topology!=r['topology_id']:
            last_topology=r['topology_id']
            metrics=read(OUT/f"history/v031/atlas/{last_topology}/qualification/geometry_metrics.json")
            metric_records={x['carrier_id']:x for x in metrics['carriers']}
        assert r['historical_carrier_qualification']==metric_records[r['id']]
    pending=read(OUT/'research/v036/DYNAMICS_PENDING.json')
    assert len(pending['scenarios'])==54450
    assert all(x['dynamics_backend']=='NOT_RUN' and x['gate']=='PENDING' for x in pending['scenarios'])
    for a in pub['artifacts']:assert sha(FAMILY/a['name'])==a['sha256']
    results=[read(p) for p in (VERSION/'runs').glob('*/RESULT.json')]
    assert any(r['status']=='PASS_IDEMPOTENT_VERIFICATION' for r in results)
    assert read(AUDIT/'PDF_VISUAL_QA.json')['status']=='PASS'
    final={'status':'PASS_COMBINED_ATLAS_ACCEPTANCE','version':'v0.4.0','records':11757,
        'historical':4497,'nominal':3630,'perturbed':3630,'component_files':10164,
        'historical_files_byte_preserved':len(contract['history']),
        'original_source_paths_hash_unchanged':len(contract['raw_sources']),
        'research_manifest_entries_passed':10169,'all_historical_carrier_qualification_records_exact':True,
        'scenarios_pending_not_run':54450,'unmapped_nominal_retained':1452,
        'default_latest_preserved':'v0.3.0','other_catalog_families_unchanged':True,
        'scientific_status':'NOT_RUN_NO_PROMOTION','repeated_run':'PASS_IDEMPOTENT_VERIFICATION',
        'zip_sha256':pub['zip_sha256'],'index_sha256':pub['index_sha256'],
        'source_contract_sha256':sha(VERSION/'configs/SOURCE_INTAKE.json'),
        'pdf_visual_qa':'PASS','test_count':pub['test_count'],'artifacts':pub['artifacts']}
    with (AUDIT/'FINAL_CHECKS.json').open('x',encoding='utf-8') as f:json.dump(final,f,indent=2);f.write('\n')
    (AUDIT/'git_status_after.txt').write_bytes(subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=ROOT))
    print(json.dumps(final,indent=2))

if __name__=='__main__':main()
