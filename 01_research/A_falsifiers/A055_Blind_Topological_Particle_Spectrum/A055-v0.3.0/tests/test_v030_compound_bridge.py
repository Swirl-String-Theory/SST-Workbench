import json,hashlib
from pathlib import Path
from a055_spectrum.a054_bridge import _pair_metric,derive_blind_compound_features
from a055_spectrum.util import sha256_file

def test_counterpropagating_pair_metric():
    x=_pair_metric([{"re":0,"im":2},{"re":0,"im":-2.1},{"re":-1,"im":0}])
    assert x["pair_available"]
    assert x["best_relative_frequency_asymmetry"] < 0.1
    y=_pair_metric([{"re":0,"im":2},{"re":0,"im":1}])
    assert not y["pair_available"]

def _write(p,obj):
    p.write_text(json.dumps(obj,indent=2)+"\n")
def test_a054_bridge_fixture(tmp_path):
    c=tmp_path/"full_20261007_000000"; (c/"_private").mkdir(parents=True)
    manifest={"preset":"full","private_mapping_sha256":None}
    cfg={"n_ladder":[56,72,88]}
    bq={"qualified":True,"backend":"cpp"}
    results={"results":[
      {"anonymous_id":"CAND_X","sector":"Q0","N":88,"status":"NOT_CERTIFIED_DYNAMICAL",
       "spectrum":{"eigenvalues":[{"re":0,"im":1},{"re":0,"im":-1}],
                   "kelvin_restricted":{"eigenvalues":[{"re":0,"im":1},{"re":0,"im":-1}],"normalized_max_real":0},
                   "oscillatory_fraction":1.0,"normalized_max_real":0},
       "rpo":{"accepted":False},"floquet":{"evaluated":False}},
      {"anonymous_id":"CAND_X","sector":"Q1","N":88,"status":"CERTIFIED_RESTORING_KELVIN_RINGDOWN_BRANCH",
       "spectrum":{"eigenvalues":[{"re":0,"im":2},{"re":0,"im":-2.1}],
                   "kelvin_restricted":{"eigenvalues":[{"re":0,"im":2},{"re":0,"im":-2.1}],"normalized_max_real":0},
                   "oscillatory_fraction":1.0,"normalized_max_real":0},
       "rpo":{"accepted":False},"floquet":{"evaluated":False}},
    ]}
    analysis={"summaries":{"CAND_X":{"sectors":{
      "Q0":{"status":"NOT_CERTIFIED_DYNAMICAL","spatial_converged":True},
      "Q1":{"status":"CERTIFIED_RESTORING_KELVIN_RINGDOWN_BRANCH","spatial_converged":True}
    }}}}
    report="blind report\n"; private={"mapping":{"CAND_X":{"architecture_code":"G"}}}
    _write(c/"CERT_CONFIG.json",cfg); _write(c/"BACKEND_QUALIFICATION.json",bq)
    _write(c/"CERT_RESULTS_BLIND.json",results); _write(c/"CERT_ANALYSIS_BLIND.json",analysis)
    (c/"CERT_REPORT_BLIND.md").write_text(report)
    _write(c/"_private"/"PRIVATE_MAPPING.json",private)
    manifest["private_mapping_sha256"]=sha256_file(c/"_private"/"PRIVATE_MAPPING.json"); _write(c/"BLIND_MANIFEST.json",manifest)
    seal={
      "manifest_sha256":sha256_file(c/"BLIND_MANIFEST.json"),
      "results_sha256":sha256_file(c/"CERT_RESULTS_BLIND.json"),
      "analysis_sha256":sha256_file(c/"CERT_ANALYSIS_BLIND.json"),
      "report_sha256":sha256_file(c/"CERT_REPORT_BLIND.md"),
      "config_sha256":sha256_file(c/"CERT_CONFIG.json"),
      "backend_qualification_sha256":sha256_file(c/"BACKEND_QUALIFICATION.json"),
      "private_mapping_commitment":sha256_file(c/"_private"/"PRIVATE_MAPPING.json")
    }; _write(c/"CERT_BLIND_SEAL.json",seal)
    z=derive_blind_compound_features(c)
    assert len(z["rows"])==2
    q1=next(r for r in z["rows"] if r["sector"]=="Q1")
    assert q1["counterpropagating_pair_symmetric"]
