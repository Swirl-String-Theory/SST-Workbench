from pathlib import Path
import json, inspect
ROOT=Path(__file__).resolve().parents[1]

def test_registered_seed_transform_does_not_override_dynamics():
    cfg=json.loads((ROOT/'configs/default.json').read_text())
    prep=cfg['seed_preparation'];assert prep['target_over_close_default']==1.05
    assert prep['shared_export_count']==1 and prep['allow_close_or_force_default_overrides'] is False

def test_install_one_export_reload_and_post_step_safety():
    text=(ROOT/'tools/install_test_export.py').read_text()
    assert 'fitto mindist' in text
    assert "f'load {geom.resolve().as_posix()}'" in text
    assert "'A058_RELOADED_SAFE_BEGIN'" in text
    assert "'A058_AFTER_GO_SAFE_BEGIN'" in text
    assert "exports!=[geom]" in text
    assert "'go 1'" in text
    assert "'shared_seed_sha256':seed_record['sha256']" in text
    for bad in ('close =','max-dr =','timeincr =','stusplit ='):
        assert bad not in text

def test_campaign_loads_only_shared_hash_verified_seed():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert "trefoil_install_test.txt" in s
    assert "_sha256(seed)!=seedinfo.get('sha256')" in s
    assert "f'load {seed.resolve().as_posix()}'" in s
    assert 'refine nbeads' not in s and 'fitto mindist' not in s
    assert "'shared_seed_sha256':seedinfo.get('sha256')" in s

def test_science_contract_includes_scale_conditioning():
    j=json.loads((ROOT/'science_contract.json').read_text())
    assert any(e['id']=='E9' for e in j['equations'])
    assert any('single' in a.lower() and 'seed' in a.lower() for a in j['assumptions'])


def test_gate_provenance_requires_matching_seed_hash():
    pipeline=(ROOT/'experiment/pipeline.py').read_text()
    analyze=(ROOT/'experiment/analysis.py').read_text()
    assert "bool(a.get('shared_seed_provenance_verified'))" in pipeline
    assert "'shared_seed_provenance_verified':bool(" in analyze
