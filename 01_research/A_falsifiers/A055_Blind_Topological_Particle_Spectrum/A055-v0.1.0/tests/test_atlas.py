from pathlib import Path
from a054_spectrum.atlas import load_atlas,validate_pd,component_cycles
ROOT=Path(__file__).resolve().parents[1]
def test_counts():
    a=load_atlas(ROOT); assert len(a)==82
    assert sum(x["kind"]=="knot" for x in a)==35
    assert sum(x["kind"]=="link" for x in a)==47
def test_pd_and_components():
    a={x["id"]:x for x in load_atlas(ROOT)}
    for x in a.values(): validate_pd(x)
    assert len(component_cycles(a["3_1"]))==1
    assert len(component_cycles(a["L2a1"]))==2
    assert len(component_cycles(a["L6a4"]))==3
    assert len(component_cycles(a["L8n8"]))==4
