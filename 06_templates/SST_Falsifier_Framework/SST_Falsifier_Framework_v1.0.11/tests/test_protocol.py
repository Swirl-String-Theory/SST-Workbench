from pathlib import Path
import json,pytest
from sst_falsifier.protocol import freeze_protocol,verify_frozen,ProtocolAlreadyFrozenError

def make_instance(tmp_path):
    (tmp_path/"report").mkdir(); (tmp_path/"preregistration").mkdir()
    files={"falsifier.toml":"[project]\nname='x'\n","source_contract.json":json.dumps({"schema":"SST-SOURCE-CONTRACT-2","independent_unit":"analytic","allow_no_external_sources":True,"sources":[]})+"\n","gate_plan.json":json.dumps({"schema":"SST-GATE-PLAN-2","gates":[{"gate_id":"G0","question":"q","requires":[]} ]})+"\n","blind_policy.json":json.dumps({"private_forbidden_terms_path":"private/terms.txt","private_nonce_path":"private/n.bin","commitment_path":"preregistration/BLIND_TERMS_COMMITMENT.json","private_reveal_path":"private/reveal.json","reveal_commitment_path":"preregistration/REVEAL_COMMITMENT.json"})+"\n","preregistration/BLIND_TERMS_COMMITMENT.json":"{}\n","preregistration/REVEAL_COMMITMENT.json":"{}\n"}
    for n,c in files.items():
        q=tmp_path/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(c,encoding="utf-8")
    (tmp_path/"private").mkdir();(tmp_path/"private"/"terms.txt").write_text("");(tmp_path/"private"/"n.bin").write_bytes(b"n"*32);(tmp_path/"private"/"reveal.json").write_text("{}")
    sc={"schema":"SST-SCIENCE-CONTRACT-2","research_question":"q","objective":"o","null_hypothesis":"h0","alternative_hypothesis":"h1","assumptions":["a"],"symbols":[],"equations":[{"id":"E1","purpose":"p","latex":"x=0","inputs":["x"],"outputs":["x"],"dimensional_check":"1=1"}],"observables":[],"steps":[{"id":"S1","operation":"op","formula_refs":["E1"],"gate":"G0"}],"falsification_criteria":[{"id":"F","criterion":"c","conclusion_if_met":"FAIL"}]}
    (tmp_path/"science_contract.json").write_text(json.dumps(sc),encoding="utf-8")
    markers=["IDENTIFICATION","QUESTION","HYPOTHESES","ASSUMPTIONS","SYMBOLS","EQUATIONS","ALGORITHM","SOURCES","GATES","NUMERICS","BACKENDS","BLINDNESS","STATISTICS","RESULTS","INTERPRETATION","REPRODUCIBILITY"]
    (tmp_path/"report"/"FALSIFIER_REPORT.tex").write_text("\n".join(f"% SST-REPORT-SECTION:{m}" for m in markers),encoding="utf-8")

def test_freeze_is_create_once(tmp_path):
    make_instance(tmp_path); f=tmp_path/"preregistration"/"FROZEN_PROTOCOL.json"; a=freeze_protocol(tmp_path,f); b=freeze_protocol(tmp_path,f); assert a["bundle_sha256"]==b["bundle_sha256"]
    (tmp_path/"source_contract.json").write_text('{"changed":true}\n')
    with pytest.raises(ProtocolAlreadyFrozenError): freeze_protocol(tmp_path,f)

def test_verify_detects_postfreeze_edit(tmp_path):
    make_instance(tmp_path); f=tmp_path/"preregistration"/"FROZEN_PROTOCOL.json"; freeze_protocol(tmp_path,f); assert verify_frozen(tmp_path,f)[0]
    (tmp_path/"falsifier.toml").write_text("[project]\nname='y'\n"); assert not verify_frozen(tmp_path,f)[0]
