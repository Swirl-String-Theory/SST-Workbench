from pathlib import Path
import hashlib, json
from a056_science.provider_contract import validate_dynamic_metadata, SCHEMA

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def test_framework_pin():
    p=json.loads((ROOT/'FRAMEWORK_PIN.json').read_text())
    assert p['version']=='1.0.6'
    assert p['status']=='CANONICAL_FROZEN'
    assert p['canonical_zip_sha256']=='24629848e3befcde67c02a935fc78347560ac42107043fbc14aaabdf146ee60d'
    assert p['framework_package_manifest_sha256']=='233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be'

def test_registered_provider_and_score_hashes_match_files():
    s=json.loads((ROOT/'science_contract.json').read_text())['provider_preregistration']
    for name, expected in s['provider_config_sha256'].items():
        assert sha(ROOT/'configs'/name)==expected
    for name, expected in s['score_config_sha256'].items():
        assert sha(ROOT/'configs'/name)==expected

def test_physical_provider_requires_independence_metadata():
    m={'schema':SCHEMA,'opaque_id':'x','source_group':'g','boundary':'open','phase_definition_id':'provider_declared_phase_v1','perturbation_id':'p','solver_id':'s','provider_version':'v','ringdown_definition_id':'provider_zero_baseline_observable_v1','evidence_class':'independent_source'}
    r=validate_dynamic_metadata(m,False)
    assert not r['pass'] and 'independence_unit' in r['missing'] and 'provenance_family' in r['missing']

def test_synthetic_control_contract():
    m={'schema':SCHEMA,'opaque_id':'x','source_group':'g','boundary':'open','phase_definition_id':'provider_declared_phase_v1','perturbation_id':'p','solver_id':'s','provider_version':'v','ringdown_definition_id':'provider_zero_baseline_observable_v1','evidence_class':'synthetic_control'}
    assert validate_dynamic_metadata(m,True)['pass']

def test_v030_development_snapshot_is_not_a_runtime_input():
    dev='data/development/A056_v0.3.0_G2_DIAGNOSTICS_READONLY.json'
    for name in ('basic.json','full.json','framework_smoke.json','e010_real_score.json','provider_e010_filament_basic.json','provider_e010_euler_smoke.json','provider_e010_euler_convergence.json'):
        assert dev not in (ROOT/'configs'/name).read_text(encoding='utf-8')
    assert 'data/development' not in (ROOT/'experiment'/'pipeline.py').read_text(encoding='utf-8')
