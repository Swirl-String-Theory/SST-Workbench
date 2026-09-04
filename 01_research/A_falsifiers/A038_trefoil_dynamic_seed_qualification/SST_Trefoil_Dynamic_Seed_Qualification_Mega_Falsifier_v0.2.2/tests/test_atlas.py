from pathlib import Path
import numpy as np
import pytest
from sst_seed_falsifier import atlas
from sst_seed_falsifier.candidates import analytic_trefoil,generate
from sst_seed_falsifier.io import load_json,dump_json
from sst_seed_falsifier.evidence import object_sha256
from sst_seed_falsifier.workflow import stage_mechanism


def test_atlas_seed_freeze_no_redraw_and_no_reserve_materialization(tmp_path,monkeypatch):
    package=Path(__file__).resolve().parents[1]
    monkeypatch.setattr(atlas,'dependencies',lambda repo:[])
    x=analytic_trefoil(128)
    monkeypatch.setattr(atlas,'load_parents',lambda repo:{'one':x,'two':x*[1,1,.7],'three':x*[1.15,.85,1.2]})
    out=tmp_path/'atlas'; config=package/'config/prospective_atlas.json'; protocol=package/'config/phase_b.json'
    frozen=atlas.freeze(tmp_path,out,config,protocol)
    assert not frozen['parent_level_held_out']
    seeds=load_json(out/'sealed/seeds.json')
    assert object_sha256(seeds['reserve'])==frozen['reserve_seed_sha256']
    result=atlas.generate_test(tmp_path,out)
    assert result['test_count']==6 and result['family_count']==3
    assert result['status']=='QUALIFIED_PROSPECTIVE_REALIZATION_ATLAS'
    assert not (out/'reserve').exists()
    cfg=load_json(config)
    generate(out/'test_atlas',tmp_path/'blind',cfg,config_path=config)
    prepared=load_json(tmp_path/'blind/prepare_summary.json')
    assert prepared['n_source_groups_with_candidates']==3 and prepared['n_candidates']==6
    with pytest.raises(FileExistsError): atlas.generate_test(tmp_path,out)
    with pytest.raises(FileExistsError): atlas.freeze(tmp_path,out,config,protocol)
    frozen['design']['normal_amplitude']=.9
    dump_json(out/'PREREGISTRATION.json',frozen)
    with pytest.raises(ValueError,match='COMMITMENT_MISMATCH'): atlas.verify_freeze(tmp_path,out)


def test_no_core_and_no_mesh_cannot_claim_mesh_certification(tmp_path):
    dump_json(tmp_path/'prepare_summary.json',{'source_diversity_status':'PASS_SOURCE_DIVERSITY'})
    dump_json(tmp_path/'stage20_early/summary.json',{'n':6})
    dump_json(tmp_path/'stage35_core_robustness/summary.json',{'n_qualified':0})
    dump_json(tmp_path/'stage37_mesh_gauge/summary.json',{'n_qualified':0})
    dump_json(tmp_path/'stage40_long/summary.json',{'verdict':'INDETERMINATE_RPO_WINDOW_NUMERICAL_COVERAGE'})
    dump_json(tmp_path/'stage50_rpo_floquet/results.json',[])
    stage_mechanism(tmp_path,{'run_kind':'blind_scientific','mechanism_top_k':2})
    assert load_json(tmp_path/'BLIND_CHAIN_SUMMARY.json')['verdict']=='CHAIN_EARLY_SCREEN_ONLY'
