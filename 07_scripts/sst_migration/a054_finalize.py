"""Publish only the validated A054 software successor and atomic queue checkpoint."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tomllib
import zipfile

sys.dont_write_bytecode=True
from preflight import ROOT,read,sha,atomic,locked,now
from a054_prepare import OUT,TARGET,FAMILY
from phase3_prepare import create_json
sys.path.insert(0,str(ROOT/'07_scripts'))
import build_catalog_index as bci
import build_family_hierarchy as bh


def snapshot_file(path):
    target=OUT/'before_registration'/path.relative_to(ROOT)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(path.read_bytes())
    assert target.read_bytes()==path.read_bytes()


def main():
    validation=read(OUT/'gate_overview.json')
    assert validation['status']=='PASS_BOUNDED_MIGRATION'
    latest=read(TARGET/'LATEST_RUN.json')
    files=[p for p in sorted(TARGET.rglob('*')) if p.is_file() and p.name not in {'LATEST_RUN.json','PUBLICATIONS.jsonl','SOURCE_MANIFEST_v0.6.0.json'}
      and not any('_outputs' in x or x in {'__pycache__','.pytest_cache'} for x in p.relative_to(TARGET).parts)]
    source={'schema':'A054-SOURCE-MANIFEST-1','version':'v0.6.0','parent':'v0.5.1',
            'scope':'Controlled software migration and admission smoke only; science NOT_RUN',
            'files':[{'path':p.relative_to(TARGET).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]}
    create_json(TARGET/'SOURCE_MANIFEST_v0.6.0.json',source)
    archive=FAMILY/'A054-v0.6.0_SOURCE.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in files+[TARGET/'SOURCE_MANIFEST_v0.6.0.json']:z.write(p,'A054-v0.6.0/'+p.relative_to(TARGET).as_posix())
    with archive.with_suffix('.zip.sha256').open('x',encoding='ascii') as f:f.write(sha(archive)+'  '+archive.name+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        import hashlib
        for row in source['files']:assert hashlib.sha256(z.read('A054-v0.6.0/'+row['path'])).hexdigest()==row['sha256']
    hp=ROOT/'10_docs/registry/family_hierarchy.json';cp=ROOT/'10_docs/registry/catalog_index.json';fy=FAMILY/'FAMILY.yaml'
    for p in [hp,cp,fy]:snapshot_file(p)
    h,c=read(hp),read(cp);oldh,oldc=deepcopy(h),deepcopy(c)
    text=fy.read_text(encoding='utf-8')
    assert text.count('latest: v0.5.1')==1
    text=text.replace('latest: v0.5.1','latest: v0.6.0',1)
    text+='\n  - id: v0.6.0\n    directory: "A054-v0.6.0"\n    output_prefix: "'+latest['output_prefix']+'"\n    qualification: SOFTWARE_ADMISSION_SMOKE_ONLY\n'
    fy.write_text(text,encoding='utf-8')
    meta=bci.parse_family(fy)
    c['by_domain']['01_research']['A054'].update({'latest':'v0.6.0','versions':meta['versions'],'output_prefix':latest['output_prefix']})
    node=h['hierarchy']['01_research']['A_falsifiers']['A054']
    node.update({'latest':'v0.6.0','declared_versions':meta['versions'],'output_prefix':latest['output_prefix']})
    node['versions_on_disk']['v0.6.0']={'directory':'A054-v0.6.0','path':TARGET.relative_to(ROOT).as_posix(),'declared':True,
      'expected_outputs_zip':Path(latest['archive']['zip']).name,'expected_zip_present':True,**bh.collect_version_artifacts(TARGET),
      'publication_manifest':'LATEST_RUN.json','scientific_qualification':'NOT_RUN','reporting_gate':'PASS','packaging_gate':'PASS','global_e013_enabled':False}
    flat=h['by_catalog_id'].get('A054',{})
    if flat.get('path')==meta['path']:
        flat['latest']='v0.6.0';flat['version_dirs'].append('A054-v0.6.0');flat['output_prefix']=latest['output_prefix']
    c['versions']+=1;h['version_count_declared']+=1;h['version_count_on_disk']+=1;h['generated_at']=now()
    for domain,letters in oldh['hierarchy'].items():
        for letter,nodes in letters.items():
            for cid,n in nodes.items():
                if (domain,letter,cid)!=('01_research','A_falsifiers','A054'):assert h['hierarchy'][domain][letter][cid]==n
    for domain,nodes in oldc['by_domain'].items():
        for cid,n in nodes.items():
            if (domain,cid)!=('01_research','A054'):assert c['by_domain'][domain][cid]==n
    atomic(hp,h);atomic(cp,c)
    state=ROOT/'10_docs/migration_v110/pilot_20261026'
    control=ROOT/'10_docs/migration_v110/scheduled_control'
    run_id='20261026T221117Z-30ccdbf1'
    run_dir=control/'runs'/run_id
    run_dir.mkdir(parents=True,exist_ok=False)
    result={'schema':'SST-A054-CONTROLLED-MIGRATION-1','falsifier':'A054','version':'v0.6.0','scope':'ADMISSION_SMOKE',
       'status':'PASS_BOUNDED_MIGRATION','gate_axes':latest['gate_axes'],'latest':latest,
       'source_archive':str(archive),'source_archive_sha256':sha(archive),'source_files':len(source['files']),
       'validation':str((OUT/'gate_overview.json').relative_to(ROOT)),
       'technical_report':str(run_dir/'A054_Controlled_Migration_Status.pdf'),'scheduled_status':'ACTIVE',
       'scientific_status_promoted':False,'full_campaign_released':False,'registered_utc':now(),
       'remaining':validation['remaining'],'manual_user_triggered':True}
    create_json(OUT/'RESULT.json',result)
    create_json(run_dir/'result.json',result)
    with locked(state):
        qp=state/'queue.json';snapshot_file(qp);q=read(qp);jobs=deepcopy(q['jobs'])
        job=next(j for j in q['jobs'] if j['id']=='A054')
        assert job['scientific_gate']=='NOT_RUN'
        job.update({'completed_version':'A054-v0.6.0','run_id':latest['run_id'],'status':'CONTROLLED_ADMISSION_SMOKE_MIGRATED_WAITING_SCIENCE_RELEASE',
          'migration_gate':latest['gate_axes']['migration_gate'],'execution_gate':latest['gate_axes']['execution_gate'],
          'reporting_gate':'PASS','packaging_gate':'PASS','latest_result':str((TARGET/'LATEST_RUN.json').relative_to(ROOT)),
          'blockers':['CROSS_PROVIDER_SCIENCE_NOT_CLOSED','STATIONARITY_HESSIAN_RINGDOWN_NOT_EXECUTED','NATIVE_PARITY_NOT_EXECUTED','FULL_CAMPAIGN_NOT_RELEASED'],
          'controlled_migration':{'result':str((OUT/'RESULT.json').relative_to(ROOT)),'source_admission':str((OUT/'SOURCE_ADMISSION.json').relative_to(ROOT)),
              'global_e013_enabled':False,'next_action':'Review a separately bounded scientific execution budget and native parity; independent provider coverage remains required for scientific closure'}})
        for old,new in zip(jobs,q['jobs']):
            if old['id']!='A054':assert old==new
        q['scheduling_enabled']=False;q['scheduled_control']['status']='ACTIVE'
        q['scheduled_control']['latest_manual_run']=str((run_dir/'result.json').relative_to(ROOT))
        atomic(qp,q)
    with (control/'execution_log.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps({'run_id':run_id,'falsifier':'A054','result':str((run_dir/'result.json').relative_to(ROOT)),'manual_user_triggered':True,'scientific_gate':'NOT_RUN'})+'\n')
    config=Path.home()/'.codex/automations/sst-workbench-dagelijkse-migratiecontrole/automation.toml'
    assert tomllib.loads(config.read_text(encoding='utf-8'))['status']=='ACTIVE'
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
