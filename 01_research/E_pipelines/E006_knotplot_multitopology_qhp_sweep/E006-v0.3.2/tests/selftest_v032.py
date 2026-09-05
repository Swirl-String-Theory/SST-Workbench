from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from qhp_sweep.runner import fmt_duration
P=json.loads((ROOT/"stage_panels.json").read_text())
assert "0.1" in P["stage1_science"]["knots"]
assert "0.2.1" in P["stage1_science"]["links"] and "0.3.1" in P["stage1_science"]["links"]
assert P["stage3_twist"]["knots"]==["3.1","4.1","5.2","6.1","7.2","8.1","9.2","10.1"]
assert fmt_duration(3661)=="01:01:01"
print("v0.3.2 STAGE/TIMER SELFTEST PASS")
for n,p in P.items():print(n,len(p["knots"])+len(p["links"])+len(p["torus"]),"topologies")
