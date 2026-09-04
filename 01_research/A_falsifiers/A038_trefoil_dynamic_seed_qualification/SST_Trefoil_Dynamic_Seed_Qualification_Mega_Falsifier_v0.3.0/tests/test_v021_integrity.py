import numpy as np
import pytest

from sst_seed_falsifier.blind import sealed_private_dir
from sst_seed_falsifier.candidates import analytic_trefoil, generate
from sst_seed_falsifier.evidence import validate_frozen_evidence
from sst_seed_falsifier.io import dump_json, load_json, discover_sources
from sst_seed_falsifier.workflow import reveal, _trajectory_shape_distance


def config(kind='workflow_smoke'):
    return {'run_kind':kind,'source_regex':r'trefoil_.*','extensions':['.txt'],
            'candidate_n':32,'max_sources':8,'variants_per_source':2,'max_candidates':16,
            'min_initial_gap_over_ds':.1,'contact_skip':3,'candidate_seed':7,
            'source_dedup_rms_tol':1e-7}


def atlas(tmp_path, families=None):
    data=tmp_path/'private_atlas'; data.mkdir(); declarations=[]
    for i,z in enumerate((.75,1.0,1.35)):
        x=analytic_trefoil(64); x[:,2]*=z; name=f'trefoil_secret{i}.txt'
        np.savetxt(data/name,x)
        declarations.append({'path':name,'family_id':families[i] if families else f'family{i}',
                             'provenance':'test fixture only','topology':'3_1','components':1,'held_out':True})
    if families is not None: dump_json(data/'source_families.json',{'sources':declarations})
    return data


@pytest.fixture
def blind_run(tmp_path):
    data=atlas(tmp_path); out=tmp_path/'public'; cfg=config()
    generate(data,out,cfg)
    return out,cfg


def test_public_evidence_contains_no_source_names(blind_run):
    out,cfg=blind_run
    for path in out.rglob('*.json'):
        text=path.read_text()
        assert 'trefoil_secret' not in text and 'private_atlas' not in text
    evidence=load_json(out/'EVIDENCE_MANIFEST.json')
    assert evidence['dataset_file_count']==3 and evidence['source_identities_hidden']
    assert (sealed_private_dir(out)/'EVIDENCE_MANIFEST_PRIVATE.json').exists()
    validate_frozen_evidence(out,cfg)


@pytest.mark.parametrize('target,expected',[
    ('identity_map.json','IDENTITY_MAP_COMMITMENT_MISMATCH'),
    ('source_generation_audit.json','SOURCE_AUDIT_COMMITMENT_MISMATCH'),
    ('EVIDENCE_MANIFEST_PRIVATE.json','EVIDENCE_COMMITMENT_MISMATCH'),
])
def test_reveal_rejects_tampered_private_maps(blind_run,target,expected):
    out,_=blind_run; path=sealed_private_dir(out)/target; obj=load_json(path)
    obj['tampered']=True; dump_json(path,obj)
    with pytest.raises(ValueError,match=expected): reveal(out)
    assert not (out/'REVEAL_SUMMARY.json').exists()


def test_reveal_rejects_tampered_key(blind_run):
    out,_=blind_run; (sealed_private_dir(out)/'blind_key.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='BLIND_KEY_COMMITMENT_MISMATCH'): reveal(out)


def test_reveal_rejects_tampered_geometry(blind_run):
    out,_=blind_run; path=next((out/'geometries').glob('*.npy')); x=np.load(path); x[0,0]+=.01; np.save(path,x)
    with pytest.raises(ValueError,match='CANDIDATE_GEOMETRY_OR_IDENTITY_MISMATCH'): reveal(out)


def test_frozen_config_cannot_be_changed_after_prepare(blind_run):
    out,cfg=blind_run
    with pytest.raises(ValueError,match='FROZEN_CONFIG_MISMATCH'): validate_frozen_evidence(out,{**cfg,'candidate_seed':8})


def test_changed_code_blocks_scoring(blind_run,monkeypatch):
    import sst_seed_falsifier.evidence as evidence
    out,cfg=blind_run; monkeypatch.setattr(evidence,'code_manifest',lambda root:[])
    with pytest.raises(ValueError,match='FROZEN_CODE_MISMATCH'): validate_frozen_evidence(out,cfg)


def test_refinement_map_tampering_blocks_reveal(blind_run):
    from sst_seed_falsifier.evidence import object_sha256
    out,_=blind_run
    dump_json(out/'stage25_refine'/'public_manifest.json',{'private_refine_commitment_sha256':object_sha256({}),'candidates':[]})
    dump_json(sealed_private_dir(out)/'stage25_refine'/'private_refine_map.json',{'changed':True})
    with pytest.raises(ValueError,match='REFINEMENT_COMMITMENT_MISMATCH'): reveal(out)


def test_prepare_refuses_overwriting_existing_evidence(blind_run,tmp_path):
    out,cfg=blind_run
    with pytest.raises(FileExistsError,match='REFUSING_TO_OVERWRITE_EXISTING_EVIDENCE'): generate(tmp_path/'private_atlas',out,cfg)


def test_scientific_s37_threshold_cannot_be_relaxed(tmp_path):
    with pytest.raises(ValueError,match='FROZEN_S37_THRESHOLD_MUST_NOT_EXCEED_0.035'):
        generate(tmp_path/'unused',tmp_path/'out',{**config('blind_scientific'),'mesh_gauge_max_final_shape_distance':.04})


def test_three_files_from_one_declared_family_do_not_pass(tmp_path):
    data=atlas(tmp_path,['same_family']*3); out=tmp_path/'out'
    with pytest.raises(RuntimeError,match='INDETERMINATE_INSUFFICIENT_SOURCE_DIVERSITY'):
        generate(data,out,{**config('blind_scientific'),'min_scientific_source_groups':1})
    summary=load_json(out/'prepare_summary.json')
    assert summary['n_source_groups_with_candidates']==1 and summary['minimum_scientific_source_groups']==3


def test_three_undeclared_files_do_not_prove_independence(tmp_path):
    with pytest.raises(RuntimeError,match='INDETERMINATE_SOURCE_PROVENANCE_UNVERIFIED'):
        generate(atlas(tmp_path),tmp_path/'out',config('blind_scientific'))


def test_deduplication_rejects_cyclic_rotated_reversed_aliases(tmp_path):
    data=tmp_path/'data'; data.mkdir(); x=analytic_trefoil(64)
    rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    for i,y in enumerate((x,np.roll(x,17,axis=0)@rotation+3,x[::-1])): np.savetxt(data/f'trefoil_{i}.txt',y)
    out=tmp_path/'out'; generate(data,out,config()); summary=load_json(out/'prepare_summary.json')
    assert summary['n_unique_sources']==1 and summary['n_source_alias_duplicates']==2


def test_open_or_nonfinite_sources_are_rejected(tmp_path):
    x=analytic_trefoil(64); np.savetxt(tmp_path/'trefoil_open.txt',x[:40])
    x[3,0]=np.nan; np.savetxt(tmp_path/'trefoil_nan.txt',x)
    assert discover_sources(tmp_path,r'trefoil_.*',['.txt'])==[]


def test_spatial_trajectories_are_compared_at_equal_times():
    x=analytic_trefoil(32)
    def trajectory(times,extra=0):
        shapes=[]
        for t in times:
            y=x.copy(); y[:,2]*=1+t+extra*t; shapes.append(y)
        return {'t':np.asarray(times),'x':np.asarray(shapes)}
    a=trajectory([0,.2,.6,1]); b=trajectory([0,.5,.8,1])
    assert _trajectory_shape_distance(a,b)['max']<1e-12
    assert _trajectory_shape_distance(a,trajectory([0,.5,.8,1],.5))['max']>.01


def test_return_search_ignores_better_but_too_early_return(monkeypatch):
    import sst_seed_falsifier.metrics as metrics
    times=np.array([0,.5,1.,1.5,2.]); distances=np.array([0,.001,.2,.05,.1])
    monkeypatch.setattr(metrics,'aligned_series',lambda *args:(None,distances,None))
    tr={'t':times,'stop_reason':'COMPLETED','ds_cv':np.array([0,0,0,.2,.8]),
        'gap_over_ds':np.array([3,3,3,2,1]),'mesh_ratio':np.array([0,0,0,.1,.9])}
    result=metrics.recurrence_metrics(tr,None,{'return_min_time':.5,'rpo_min_observation_time':1.2})
    assert result['best_return_time']==1.5 and result['mesh_ratio_at_best_return']==.1


def test_floquet_perturbations_reuse_exact_s40_time_grid(monkeypatch):
    import sst_seed_falsifier.floquet as floquet
    calls=[]
    def fake_simulate(x,cfg,T,**kwargs):
        calls.append(kwargs)
        return {'x':np.asarray([x,x]),'stop_reason':'COMPLETED'}
    monkeypatch.setattr(floquet,'simulate',fake_simulate)
    result=floquet.projected_floquet(analytic_trefoil(32),.01,{'core_fraction':.08,'require_native':False,'floquet_dim':2},replay={'dt':.001,'guard_stride':3})
    assert result['quality_completed'] and len(calls)==5
    assert all(c['integration_plan']==(10,.001) and c['guard_stride_override']==3 for c in calls)


def test_empty_s40_is_indeterminate_not_physics_failure(tmp_path):
    from sst_seed_falsifier.workflow import stage_long
    dump_json(tmp_path/'public_manifest.json',{'candidates':[]})
    dump_json(tmp_path/'stage37_mesh_gauge'/'results.json',[])
    cfg={'run_kind':'blind_scientific','long_top_k':2,'long_n':32,'rpo_top_k':1,'core_fraction':.08}
    assert stage_long(tmp_path,cfg)==[]
    summary=load_json(tmp_path/'stage40_long'/'summary.json')
    assert summary['verdict']=='INDETERMINATE_RPO_WINDOW_NUMERICAL_COVERAGE'
    assert summary['physics_verdict']=='INDETERMINATE' and not summary['hard_fail_coverage_satisfied']


def test_invalid_convergence_ladders_fail_closed(tmp_path):
    from sst_seed_falsifier.workflow import stage_resolution,stage_temporal
    with pytest.raises(ValueError,match='SPATIAL_LADDER_REQUIRES_INCREASING_RESOLUTIONS'):
        stage_resolution(tmp_path,{'resolution_n':[32]})
    dump_json(tmp_path/'public_manifest.json',{'candidates':[]})
    dump_json(tmp_path/'stage30_resolution'/'results.json',[])
    with pytest.raises(ValueError,match='TEMPORAL_LADDER_MUST_HALVE_TIMESTEP'):
        stage_temporal(tmp_path,{'temporal_dt_factor_multipliers':[1,.75,.5]})
