"""End-to-end fail-then-continue test using a genuine generated falsifier instance.

This is synthetic software qualification only. No physical SST inference.
"""
from __future__ import annotations
from pathlib import Path
import json
import subprocess
import sys
import tempfile
from sst_falsifier.runner import run_mode, reveal_eligibility
from sst_falsifier.report import REQUIRED_SECTION_MARKERS
from sst_falsifier.gates import GateLedger
from sst_falsifier.outputs import verify_output_manifest

framework=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="sst_non_short_circuit_") as td:
    root=Path(td)/"A777-v0.1.0"
    cp=subprocess.run([sys.executable,str(framework/"tools/new_falsifier.py"),
        "A777","Diagnostics",str(root),"--profile","minimal"],capture_output=True,text=True)
    if cp.returncode: raise RuntimeError(cp.stdout+cp.stderr)
    def clean(x):
        if isinstance(x,str):return x.replace("REPLACE_BEFORE_FREEZE","synthetic software qualification")
        if isinstance(x,list):return [clean(v) for v in x]
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
        return x
    sc=root/"science_contract.json";sc.write_text(json.dumps(clean(json.loads(sc.read_text())),indent=2),encoding="utf-8")
    src=root/"source_contract.json";source=clean(json.loads(src.read_text()));source["sources"]=[];source["allow_no_external_sources"]=True
    src.write_text(json.dumps(source,indent=2),encoding="utf-8")
    tex='\\documentclass{article}\n\\usepackage{longtable,booktabs}\n\\begin{document}\nDiagnostic test only.\n'
    tex+='\n'.join(f'% SST-REPORT-SECTION:{name}\n\\section{{{name.title()}}}\nSynthetic software control with a fixed protocol. No physical inference or accepted backend certification is claimed for this diagnostic control.' for name in REQUIRED_SECTION_MARKERS)
    tex+='\n\\input{AUTO_SCIENCE_CONTRACT.tex}\n\\input{AUTO_RESULTS.tex}\n\\end{document}\n'
    (root/'report/FALSIFIER_REPORT.tex').write_text(tex,encoding='utf-8')
    pipeline=(root/'experiment/pipeline.py')
    pipeline.write_text('''from sst_falsifier.gates import GateInputsUnavailable

def run_scientific_pipeline(root,cfg,ledger,mode):
    calls=[]
    def evaluate(gid):
        def work():
            calls.append(gid)
            return {"status":"FAIL" if gid=="G2" else "PASS","metrics":{"software_probe":gid},"reason":"synthetic execution"}
        return work
    ledger.run_evaluators({f"G{i}":evaluate(f"G{i}") for i in range(9)})
    assert calls==["G0","G1","G2","G3","G8"],calls  # disabled G4-G7, per minimal profile
    return {"schema":"SST-BACKEND-MANIFEST-2","note":"synthetic diagnostic exercise"}
''',encoding='utf-8')
    # Builtin FREEZE and FULL, including protocol / manifest / report / ZIP.
    assert run_mode(root,"FREEZE")==0
    assert run_mode(root,"FULL")==3
    out=root/"Diagnostics_v0.1.0-outputs"
    led=GateLedger.from_dict(json.loads((out/"GATE_LEDGER.json").read_text()))
    assert led.status("G2")=="FAIL" and led.status("G3")=="PASS" and led.status("G8")=="PASS"
    assert led.qualification("G3")["qualification"]=="DIAGNOSTIC_ONLY"
    assert led.qualification("G8")["qualification"]=="DIAGNOSTIC_ONLY"
    assert verify_output_manifest(out,out/"OUTPUT_MANIFEST.json")[0]
    assert (out/"RUN_SUMMARY.json").is_file()
    summary=json.loads((out/"RUN_SUMMARY.json").read_text())
    assert summary["gate_execution"]["executed"]==5,summary["gate_execution"]
    assert summary["gate_execution"]["diagnostic_only"]>=2
    decision=reveal_eligibility(root,{},out,json.loads((root/"preregistration/FROZEN_PROTOCOL.json").read_text()))
    assert decision["eligible"] is False and decision["required_gate_qualification"]=="DIAGNOSTIC_ONLY",decision
    print(json.dumps({"status":"PASS","G2":led.status("G2"),"G3":led.status("G3"),
        "G3_qualification":led.qualification("G3")["qualification"],
        "G8":led.status("G8"),"G8_qualification":led.qualification("G8")["qualification"],
        "executed":summary["gate_execution"]["executed"],"reveal_eligible":decision["eligible"]},indent=2))
