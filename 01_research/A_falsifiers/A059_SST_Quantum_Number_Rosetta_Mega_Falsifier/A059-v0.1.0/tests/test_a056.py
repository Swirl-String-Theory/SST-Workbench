from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mega.common import verify_source_archive,provider_aggregates

def test_source_archive_sha(): assert verify_source_archive(ROOT)["pass"]
def test_provider_aggregates_nonempty(): assert len(provider_aggregates(ROOT))>=30
def test_science_gates_nonblocking_after_source():
    g=json.loads((ROOT/"gate_plan.json").read_text())["gates"]; d={x["gate_id"]:x for x in g}
    for k in ["G2","G3","G8"]: assert d[k]["requires"]==["G1"]
    for k in ["G4","G5","G6","G7"]: assert d[k]["enabled"] is False
