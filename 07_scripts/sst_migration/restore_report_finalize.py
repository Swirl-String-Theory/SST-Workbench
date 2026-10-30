"""Register the packaging-only successor and preserve all historical artifacts."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha, atomic, locked, now
from phase3_prepare import create_json
from restore_report_prepare import OUT, FAMILY
sys.path.insert(0, str(ROOT/'07_scripts'))
import build_catalog_index as bci
import build_family_hierarchy as bh


def before(path):
    dest=OUT/'before_registration'/path.relative_to(ROOT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as stream: stream.write(path.read_bytes())


def main():
    gates=read(OUT/'REPORT_PACKAGING_GATES_FINAL.json')
    assert all(gates[k]=='PASS' for k in ['reporting_gate','packaging_gate','standalone_run_all_gate','repeat_run_retention_gate'])
    root=FAMILY/'A011-v0.4.1'
    latest=read(root/'LATEST_RUN.json')
    # The released source inventory excludes mutable output directories/pointers.
    files=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if any('_outputs' in x or x in {'__pycache__','.pytest_cache','build'} for x in rel.parts):continue
        if p.is_file() and p.name not in {'PUBLICATIONS.jsonl','LATEST_RUN.json','SOURCE_MANIFEST_v0.4.1.json'}:files.append(p)
    rows=[{'path':p.relative_to(root).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
    binding=ROOT/'07_scripts/sst_migration/report_output_contract.py'
    manifest={'schema':'A011-SOURCE-MANIFEST-1','version':'v0.4.1','files':rows,
              'external_bindings':[{'path':binding.relative_to(ROOT).as_posix(),'sha256':sha(binding)}],
              'scientific_change':False,'parent':'A011-v0.4.0','source_tree_sha256':hashlib.sha256(json.dumps({r['path']:r['sha256'] for r in rows},sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    create_json(root/'SOURCE_MANIFEST_v0.4.1.json',manifest)
    archive=FAMILY/'A011-v0.4.1_SOURCE.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in files+[root/'SOURCE_MANIFEST_v0.4.1.json']:z.write(p,'A011-v0.4.1/'+p.relative_to(root).as_posix())
        z.write(binding,'external_bindings/report_output_contract.py')
    with archive.with_suffix('.zip.sha256').open('x',encoding='ascii') as stream:stream.write(sha(archive)+'  '+archive.name+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for row in rows:assert hashlib.sha256(z.read('A011-v0.4.1/'+row['path'])).hexdigest()==row['sha256']
    contract={'schema':'SST-MIGRATION-REPORT-OUTPUT-CONTRACT-1','required_for_future_migrations':True,
              'scientific_renderer':'Existing qualified sst_falsifier.report.write_auto_science_tex/write_auto_results_tex/publish_instance_report',
              'binding_path':binding.relative_to(ROOT).as_posix(),'binding_sha256':sha(binding),
              'output_prefix_policy':'Stable catalog ID + family name, version handled separately',
              'output_folder':'./<output_prefix>_<version>_outputs/', 'publications':'../<output_prefix>_<version>__<run_id>_FALSIFIER_REPORT.pdf and ../<output_prefix>_<version>_outputs__<run_id>.zip plus SHA256',
              'historical_retention':'Existing framework run-ID reservation retains old output trees; immutable per-run parent PDF/ZIP; append-only publication journal and mutable latest pointer',
              'technical_reports':'Separate from scientific FALSIFIER_REPORT.pdf; never replace scientific explanation with a migration status report',
              'validated_on':'A011-v0.4.1','report_gate':'PASS','packaging_gate':'PASS','repeat_run_gate':'PASS',
              'evidence':(OUT/'REPORT_PACKAGING_GATES_FINAL.json').relative_to(ROOT).as_posix(),
              'scientific_status_promoted':False}
    common=ROOT/'10_docs/migration_v110/REPORT_OUTPUT_CONTRACT.json'
    create_json(common,contract)
    hp=ROOT/'10_docs/registry/family_hierarchy.json';cp=ROOT/'10_docs/registry/catalog_index.json';fy=FAMILY/'FAMILY.yaml'
    for p in [hp,cp,fy]:before(p)
    h,c=read(hp),read(cp);oldh,oldc=deepcopy(h),deepcopy(c)
    text=fy.read_text(encoding='utf-8');oldprefix='1_Maxwell_SST_Kinetic_Falsifier';newprefix='A011_Maxwell_SST_Kinetic_Falsifier'
    text=text.replace('latest: v0.4.0','latest: v0.4.1',1).replace('output_prefix: "'+oldprefix+'"','output_prefix: "'+newprefix+'"\nlegacy_output_prefix: "'+oldprefix+'"',1)
    needle='    qualification: GEOMETRY_ADAPTER_ONLY'
    assert text.count(needle)==1
    text=text.replace(needle,needle+'\n  - id: v0.4.1\n    directory: "A011-v0.4.1"\n    qualification: GEOMETRY_ONLY_REPORT_CONTRACT_RESTORED',1)
    # Preserve each historical version's actual output namespace explicitly.
    lines=text.splitlines();result=[]
    for line in lines:
        result.append(line)
        if line.strip().startswith('directory: "A011-v') and 'v0.4.1"' not in line:
            result.append('    output_prefix: "'+oldprefix+'"')
    fy.write_text('\n'.join(result)+'\n',encoding='utf-8')
    meta=bci.parse_family(fy)
    c['by_domain']['01_research']['A011'].update({'latest':'v0.4.1','versions':meta['versions'],'output_prefix':newprefix,'legacy_output_prefix':oldprefix})
    node=h['hierarchy']['01_research']['A_falsifiers']['A011'];node.update({'latest':'v0.4.1','declared_versions':meta['versions'],'output_prefix':newprefix,'legacy_output_prefix':oldprefix})
    node['versions_on_disk']['v0.4.1']={'directory':'A011-v0.4.1','path':root.relative_to(ROOT).as_posix(),'declared':True,
                                      'expected_outputs_zip':Path(latest['archive']['zip']).name,'expected_zip_present':True,
                                      **bh.collect_version_artifacts(root),'publication_manifest':'LATEST_RUN.json','reporting_gate':'PASS','packaging_gate':'PASS','scientific_qualification':'UNRESOLVED'}
    if h['by_catalog_id'].get('A011',{}).get('path')==meta['path']:
        flat=h['by_catalog_id']['A011'];flat['latest']='v0.4.1';flat['output_prefix']=newprefix;flat['version_dirs'].append('A011-v0.4.1')
    c['versions']+=1;h['version_count_declared']+=1;h['version_count_on_disk']+=1;h['generated_at']=now()
    for domain,letters in oldh['hierarchy'].items():
        for letter,nodes in letters.items():
            for cid,n in nodes.items():
                if (domain,letter,cid)!=('01_research','A_falsifiers','A011'):assert h['hierarchy'][domain][letter][cid]==n
    for domain,nodes in oldc['by_domain'].items():
        for cid,n in nodes.items():
            if (domain,cid)!=('01_research','A011'):assert c['by_domain'][domain][cid]==n
    atomic(hp,h);atomic(cp,c)
    state=ROOT/'10_docs/migration_v110/pilot_20261026'
    with locked(state):
        qp=state/'queue.json';before(qp);q=read(qp);oldjobs=deepcopy(q['jobs']);job=next(j for j in q['jobs'] if j['id']=='A011')
        job.update({'completed_version':'A011-v0.4.1','run_id':latest['run_id'],'status':'CONTROLLED_GEOMETRY_REPORT_CONTRACT_RESTORED',
                    'reporting_gate':'PASS','packaging_gate':'PASS','latest_result':str((root/'LATEST_RUN.json').relative_to(ROOT)),
                    'report_output_restoration':{'source_version':'A011-v0.4.0','corrected_version':'A011-v0.4.1','evidence':contract['evidence'],'latest_publication':latest}})
        for old,new in zip(oldjobs,q['jobs']):
            if old['id']!='A011':assert old==new
        q['report_output_contract']=contract
        q['scheduling_enabled']=False
        if 'scheduled_control' in q:q['scheduled_control']['status']='PAUSED';q['scheduled_control']['pause_reason']='Report/output correction; no automatic reactivation'
        atomic(qp,q)
    result={'report_gate':'PASS','packaging_gate':'PASS','standalone_run_all_gate':'PASS','repeat_run_gate':'PASS',
            'scientific_gate':'UNRESOLVED_MISSING_PHYSICAL_INPUTS','scheduled_status':'PAUSED','historical_versions_unchanged':True,
            'latest':latest,'source_archive':str(archive),'source_archive_sha256':sha(archive),'source_tree_sha256':manifest['source_tree_sha256'],
            'common_contract':common.relative_to(ROOT).as_posix(),'queue_sha256':sha(state/'queue.json')}
    create_json(OUT/'RESTORATION_RESULT.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
