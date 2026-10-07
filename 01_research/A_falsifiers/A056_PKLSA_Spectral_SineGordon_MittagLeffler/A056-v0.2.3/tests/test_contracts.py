from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from a056_science.provider_contract import validate_dynamic_metadata,SCHEMA

def test_framework_pin():
    p=json.loads((ROOT/'FRAMEWORK_PIN.json').read_text()); assert p['version']=='1.0.4' and p['status']=='CANONICAL_FROZEN'

def test_physical_provider_requires_independence_metadata():
    m={'schema':SCHEMA,'opaque_id':'x','source_group':'g','boundary':'open','phase_definition_id':'provider_declared_phase_v1','perturbation_id':'p','solver_id':'s','provider_version':'v','evidence_class':'independent_source'}
    r=validate_dynamic_metadata(m,False); assert not r['pass'] and 'independence_unit' in r['missing'] and 'provenance_family' in r['missing']

def test_synthetic_control_contract():
    m={'schema':SCHEMA,'opaque_id':'x','source_group':'g','boundary':'open','phase_definition_id':'provider_declared_phase_v1','perturbation_id':'p','solver_id':'s','provider_version':'v','evidence_class':'synthetic_control'}
    assert validate_dynamic_metadata(m,True)['pass']
