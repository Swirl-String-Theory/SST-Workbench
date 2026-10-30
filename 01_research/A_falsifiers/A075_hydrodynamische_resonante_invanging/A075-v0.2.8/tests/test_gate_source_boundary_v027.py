"""Development contract qualification for A075-v0.2.8.
No source file mutations and no fake GPU/native execution claims.
"""
from pathlib import Path
import json, os, sys, tomllib
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework,resolve_framework_root
from experiment.qualification import inspect_sources,parity_screen,domain_gate,topology_inputs
from experiment.domain import parse_domains


def test_framework_runtime_stays_pinned_exactly():
    info=json.loads((ROOT/'_sst_runtime/RUNTIME_SNAPSHOT_MANIFEST.json').read_text())
    import hashlib
    assert info['version']=='1.1.0'
    assert all(hashlib.sha256((ROOT/'_sst_runtime'/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in info['files'])


def test_default_mode_does_not_enable_domain_study():
    from experiment.science import _resolve
    x=_resolve('BASIC',{'threads':12})
    assert not x['domain_study'] and not x['domain_study_only']
    assert x['backend']=='cpu-scipy-fft'


def test_all_three_gate_categories_are_enabled_and_independent_from_retention():
    cfg=tomllib.loads((ROOT/'falsifier.toml').read_text())
    assert cfg['backends']['cpp']['enabled']
    assert cfg['backends']['sycl']['enabled']
    assert cfg['sources']['multilibrary_required']
    g={r['gate_id']:r for r in json.loads((ROOT/'gate_plan.json').read_text())['gates']}
    for gid in ('G5','G6','G7','G10','G11'):
        assert g[gid]['enabled'] and 'G4' not in g[gid]['requires']
        assert set(g[gid]['requires'])=={'G1'}
    load_framework()
    from sst_falsifier.gates import validate_gate_plan
    assert validate_gate_plan(ROOT/'gate_plan.json')==[]


def test_sources_resolve_relative_to_actual_workbench(monkeypatch):
    # A075 must remain portable when the Workbench is relocated as a unit.
    monkeypatch.setenv('SST_WORKBENCH_ROOT',str(ROOT.parents[3]))
    result=inspect_sources(ROOT)
    assert result['passed']
    assert {r['source_id'] for r in result['sources']}=={'A021','A032','LOCAL_CODE','RUBAN_SEED','RUBAN_MANIFEST','RUBAN_FILAMENT_CONFIG'}
    assert all(r['hash_match'] and r['exists'] for r in result['sources'])
    assert all('v0.2.8' in r['path'] for r in result['sources'])


def test_bad_source_root_fails_closed(monkeypatch,tmp_path):
    monkeypatch.setenv('SST_WORKBENCH_ROOT',str(tmp_path))
    result=inspect_sources(ROOT)
    assert not result['passed']
    assert not any(r['exists'] for r in result['sources'])


def test_source_mismatch_fails_closed(monkeypatch,tmp_path):
    # A source path that exists with mutated bytes must fail the SHA check.
    monkeypatch.setenv('SST_WORKBENCH_ROOT',str(tmp_path))
    c=json.loads((ROOT/'source_contract.json').read_text())
    for item in c['sources']:
        t=tmp_path/item['relative_path'];t.parent.mkdir(parents=True,exist_ok=True)
        t.write_bytes(b'MODIFIED')
    result=inspect_sources(ROOT)
    assert not result['passed']
    assert all(r['exists'] and not r['hash_match'] for r in result['sources'])


def test_true_fixed_dx_domain_ladder_and_no_boundary_certification():
    levels=parse_domains('10:80,15:120,20:160',80)
    assert [z['dx'] for z in levels]==[0.125]*3
    assert domain_gate(None)['status']=='UNRESOLVED'
    d={'knots':{'0_1':{'execution':'EXECUTED','last_pair_difference':0.2}},
       'fixed_physical_dx':0.125,'fixed_core_sigma':0.5}
    z=domain_gate(d)
    assert z['status']=='PASS' and not z['metrics']['physical_free_space_pass']
    assert z['metrics']['periodic_images_present']


def test_real_operator_parity_has_no_fake_fallback():
    # When no real module/device is installed, status must be UNRESOLVED.
    for kind in ('cpp','gpu'):
        r=parity_screen(ROOT,kind)
        assert r['status'] in {'PASS','FAIL','UNRESOLVED'}
        assert r['qualification']=='NUMERICAL_OPERATOR_DIAGNOSTIC_ONLY'
        if r['status']=='PASS':
            assert len(r['cases'])==2
            assert all(c['pass'] and c['finite'] for c in r['cases'])


def test_knot_availability_does_not_substitute_fake_geometry():
    result=topology_inputs(ROOT)
    assert result['status']=='UNRESOLVED'
    assert len(result['files'])==2
    assert all(not z['independent_topology_certified'] for z in result['files'])


def test_report_and_contract_are_freeze_valid():
    load_framework()
    from sst_falsifier.report import validate_report
    from sst_falsifier.science_contract import validate_science_contract
    assert validate_report(ROOT/'report/FALSIFIER_REPORT.tex',require_complete=True)==[]
    assert validate_science_contract(json.loads((ROOT/'science_contract.json').read_text()))==[]
