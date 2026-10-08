from pathlib import Path
from sst_falsifier.report import validate_report
from sst_falsifier.science_contract import validate_science_contract

def test_report_placeholder_rejected():
    text="\n".join(f"% SST-REPORT-SECTION:{m}" for m in ("IDENTIFICATION","QUESTION","HYPOTHESES","ASSUMPTIONS","SYMBOLS","EQUATIONS","ALGORITHM","SOURCES","GATES","NUMERICS","BACKENDS","BLINDNESS","STATISTICS","RESULTS","INTERPRETATION","REPRODUCIBILITY"))+"\n\\SSTTODO{x}"
    p=Path(__import__('tempfile').mkdtemp())/'r.tex';p.write_text(text);assert validate_report(p,require_complete=True)

def test_science_unknown_formula_ref_rejected():
    c={"schema":"x","research_question":"q","objective":"o","null_hypothesis":"0","alternative_hypothesis":"1","assumptions":["a"],"symbols":[],"equations":[],"observables":[],"steps":[{"id":"S","operation":"op","formula_refs":["E99"],"gate":"G0"}],"falsification_criteria":[1]}
    assert any("unknown equation" in e for e in validate_science_contract(c))
