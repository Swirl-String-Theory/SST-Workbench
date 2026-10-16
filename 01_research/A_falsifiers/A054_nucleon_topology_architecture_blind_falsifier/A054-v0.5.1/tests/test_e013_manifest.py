from pathlib import Path
import json, pytest
from a054_state.pklsa import load_cross_manifest


def valid_manifest():
    return {
      "schema":"E013-COMMON-CARRIER-MANIFEST-1",
      "sklsa_release_id":"E011-v0.3.0",
      "legacy_falsifier_outputs_used_as_evidence":False,
      "carriers":[{
        "topology_id":"3_1","static_seed_id":"SEED_test","carrier_id":"CAR_test",
        "provider_group":"provider_a","geometry_sha256":"a"*64,
        "source_locator":{"source_path":"dummy.vect","representation":"vect","geometry_sha256":"a"*64}
      }]
    }

def test_accepts_e013_schema(tmp_path):
    p=tmp_path/"manifest.json";p.write_text(json.dumps(valid_manifest()))
    d=load_cross_manifest(p);assert d["carriers"][0]["static_seed_id"]=="SEED_test"

def test_rejects_legacy_evidence_flag(tmp_path):
    d=valid_manifest();d["legacy_falsifier_outputs_used_as_evidence"]=True
    p=tmp_path/"manifest.json";p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match="legacy falsifier evidence"):load_cross_manifest(p)

def test_rejects_wrong_sklsa_release(tmp_path):
    d=valid_manifest();d["sklsa_release_id"]="E011-v0.2.0"
    p=tmp_path/"manifest.json";p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match="unexpected SKLSA release"):load_cross_manifest(p)
