"""Read-only A011/E010 compatibility review. No frozen source or dataset edits."""
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT=Path(r'C:\workspace\projects\SST-Workbench')
OUT=Path(__file__).resolve().parent
A011=ROOT/'01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.4.1'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def create(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')


def main():
    latest=read(A011/'LATEST_RUN.json')
    assert sha(latest['report_pdf'])==latest['report_sha256']
    assert sha(latest['archive']['zip'])==latest['archive']['sha256']
    sys.path.insert(0,str(A011/'src'))
    from maxwell_sst_falsifier import framework_v110 as adapter
    adapter.qualified_framework(A011);adapter.verify_protocol(A011)
    contract,plan,accepted=adapter.verify_admission(A011)
    summary=read(Path(latest['output_root'])/'RUN_SUMMARY.json')
    ledger=read(Path(latest['output_root'])/'GATE_LEDGER.json')
    parity=read(Path(latest['output_root'])/'PARITY_RESULTS.json')
    source=read(A011/'SOURCE_MANIFEST_v0.4.1.json')
    for row in source['files']:assert sha(A011/row['path'])==row['sha256']
    with zipfile.ZipFile(OUT/'E010_v036_core.zip') as z:
        assert z.testzip() is None
        expected=(OUT/'RELEASE_ARCHIVES.sha256').read_text().split()[0]
        assert sha(OUT/'E010_v036_core.zip')==expected
        members=set(z.namelist())
        prefix=next(n for n in members if n.endswith('/BUILD_SUMMARY.json')).rsplit('/',1)[0]+'/'
        files=['BUILD_SUMMARY.json','FAMILY_INDEX.json','DYNAMICS_PENDING.json','GEOMETRY_VS_SURVIVAL.csv','RELEASE_STATUS.md']
        sums={line.split(None,1)[1].strip():line.split(None,1)[0] for line in z.read(prefix+'MANIFEST_SHA256.txt').decode().splitlines()}
        for name in files:
            assert hashlib.sha256(z.read(prefix+name)).hexdigest()==sums[name]
        build=json.loads(z.read(prefix+'BUILD_SUMMARY.json'))
        index=json.loads(z.read(prefix+'FAMILY_INDEX.json'))
        pending=json.loads(z.read(prefix+'DYNAMICS_PENDING.json'))
        overlay=json.loads(z.read('E010-v0.3.6/configs/family_registry_overlay.json'))
        assert len(index['seeds'])==3630 and len(pending['scenarios'])==54450
        status_counts=Counter(r['gate'] for r in pending['scenarios'])
        backend_counts=Counter(r['dynamics_backend'] for r in pending['scenarios'])
        assert status_counts=={'PENDING':54450} and backend_counts=={'NOT_RUN':54450}
        assert build['independent_source_groups']==1 and index['production_admission'] is False
        with zipfile.ZipFile(OUT/'E010_v036_source.zip') as original:
            assert original.testzip() is None
            source_members=[n for n in original.namelist() if not original.getinfo(n).is_dir()]
            differences=[n for n in source_members if n not in members or original.read(n)!=z.read(n)]
            assert differences==['E010-v0.3.6/README.md']
            known_differences=read(OUT/'SOURCE_CORE_DIFFERENCES.json')
            assert len(known_differences)==1 and known_differences[0]['path']==differences[0]
            # The preserved diff changes only the packaging/download paragraph.
        candidates=[]
        shard=OUT/'E010_v036_KNOTS_01.zip'
        assert sha(shard)=='20db6defecb0e21820fb8d861bdf09766c398412ba3aaf1522c9323f6bee4546'
        from pklsa_builder.hashing import geometry_sha256
        with zipfile.ZipFile(shard) as coordinates:
            assert coordinates.testzip() is None
            for B0 in [0.02,0.10,0.32]:
                seed=next(s for s in index['seeds'] if s['parametric_embedding']=='T_2_3' and abs(s['B0']-B0)<1e-12)
                comp=seed['components'][0]
                rel=comp['xyz_path']
                filename=next(n for n in coordinates.namelist() if n.endswith('/'+rel))
                raw=coordinates.read(filename)
                digest=hashlib.sha256(raw).hexdigest()
                assert digest==comp['sha256']==sums[rel]
                points=np.loadtxt(io.StringIO(raw.decode('utf-8')))
                assert points.shape==(1024,3) and np.isfinite(points).all()
                candidates.append({'seed_id':seed['seed_id'],'B0':B0,'embedding':'T_2_3','points':len(points),
                    'raw_sha256':digest,'parsed_geometry_sha256_v031':geometry_sha256([points]),
                    'source_status':'RAW_HASH_AND_FINITE_COORDINATES_PASS',
                    'active_atlas_qualification':comp['geometry_metrics']['qualified_for_active_atlas'],
                    'finite_core_qualified':seed['finite_core_qualified'],'dynamic_stability':seed['dynamic_stability']})
        counts={'family_count':build['family_count'],'knot_families':build['knot_family_count'],'link_families':build['link_family_count'],
                'nominal_geometries':build['geometry_count'],'perturbed_geometries':build['geometry_count'],
                'coordinate_files':build['coordinate_files_nominal']+build['coordinate_files_perturbed'],
                'point_count_per_component':build['point_count_per_component'],'pending_scenarios':len(pending['scenarios']),
                'dynamics_status_counts':dict(backend_counts),'scenario_gate_counts':dict(status_counts)}
        metadata={'build_status':build['scientific_status'],'research_only':index['research_only'],
                  'production_admission':index['production_admission'],'independent_source_groups':build['independent_source_groups'],
                  'all_seed_components_not_active_qualified':all(not c['geometry_metrics']['qualified_for_active_atlas'] for s in index['seeds'] for c in s['components']),
                  'all_seed_finite_core_unqualified':all(s['finite_core_qualified'] is False for s in index['seeds']),
                  'overlay_release':overlay['release'],'overlay_index_reference':overlay['index_reference_from_version_folder'],
                  'overlay_still_points_to_v035':'v0.3.5' in overlay['index_reference_from_version_folder'],
                  'output_manifest_entries':len(sums),'core_output_metadata_hashes_verified':len(files),'source_core_common_files_identical':len(source_members)-len(differences),
                  'source_core_documentation_difference':'README distribution paragraph only; exact diff and both archive hashes retained'}
    result={'schema':'A011-E010-V036-REVIEW-1','review_date':'2026-10-27','selftest':read(OUT/'A011_SELFTEST_CURRENT.json'),
        'last_scientific_adapter_run':{'run_id':latest['run_id'],'gate_axes':latest['gate_axes'],'errors':summary['errors'],'warnings':summary['warnings'],
             'maximum_native_velocity_abs_delta':max(x['velocity_max_abs_delta'] for x in parity),'all_native_parity_comparisons_pass':all(x['pass'] for x in parity),
             'gate_summary':[{'gate_id':r['gate_id'],'status':r['status'],'execution_status':r['execution_status'],'qualification':r['qualification']} for r in ledger['records']]},
        'a011_frozen_pilot':{'topologies':[r['topology_id'] for r in plan['seeds']],'resolution_ladder':plan['resolution_ladder'],
             'admission_lane':contract['permitted_lane'],'admitted_sources_reverified':len(accepted),'missing_evidence':summary['missing_scientific_evidence'],
             'physical_gate_evaluators':'G3/G4/G7/G8 explicitly bound to unavailable() in this geometry-only adapter'},
        'e010_v036':{'counts':counts,'metadata':metadata,'sample_geometry_checks':candidates,
             'download_scope':'Core and source ZIP plus KNOTS_01 only; not all seven coordinate shards',
             'local_canonical_v036_folders_were_empty':True,'source_admission':'Standing local/Drive authorization; no extra permission required'},
        'decision':{'current_physical_blockers_resolved':False,'useful_for_geometry_stress_controls':True,
             'automatic_replacement_in_frozen_a011_allowed':False,'new_dataset_and_adapter_contract_required':True,
             'topology_mapping_and_overlay_review_required':True,'all_existing_versions_results_and_queue_unchanged':True}}
    create('REVIEW.json',result)
    create('SOURCE_HASHES.json',[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file()])
    print(json.dumps({'selftest_exit':result['selftest']['exit_code'],'old_run_errors':summary['errors'],'e010_counts':counts,'e010_metadata':metadata,'sample_seeds':candidates,'decision':result['decision']},indent=2))


if __name__=='__main__':main()
