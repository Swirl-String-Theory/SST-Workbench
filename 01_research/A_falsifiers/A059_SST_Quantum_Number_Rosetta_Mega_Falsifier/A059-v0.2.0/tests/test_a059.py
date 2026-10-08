from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mega.common import verify_source_archive,provider_aggregates
from mega.phases import PHASES
from mega.dynamics import canonical_knot, FAMILY_A, FAMILY_B, three_core_container, winding_about_z

def test_source_archive_sha(): assert verify_source_archive(ROOT)["pass"]
def test_provider_aggregates_nonempty(): assert len(provider_aggregates(ROOT))>=30
def test_science_gates_nonblocking_after_source():
    g=json.loads((ROOT/"gate_plan.json").read_text())["gates"]; d={x["gate_id"]:x for x in g}
    for k in ["G2","G3","G8"]: assert d[k]["requires"]==["G1"]
    for k in ["G4","G5","G6","G7"]: assert d[k]["enabled"] is False
def test_phase_registry_v020():
    assert list(PHASES)==[f"P{i:02d}" for i in range(10)]
    reg=json.loads((ROOT/"PHASE_REGISTRY.json").read_text())
    p2=next(x for x in reg["phases"] if x["id"]=="P02")
    p6=next(x for x in reg["phases"] if x["id"]=="P06")
    assert p2["slug"]=="FAMILY_DYNAMICS"
    assert p6["slug"]=="BORROMEAN_THREE_CORE"
def test_canonical_probe_single_components():
    for tid in FAMILY_A+FAMILY_B:
        P=canonical_knot(tid,96); assert P.shape==(96,3)
def test_three_core_winding_same_sign():
    C=three_core_container('CANDIDATE',60)
    w=[winding_about_z(p) for p in C]
    assert len(C)==3 and all(x>0.8 for x in w)
