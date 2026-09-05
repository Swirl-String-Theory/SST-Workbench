from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"balance_design.json").read_text())
assert D["version"]=="0.2.3"
assert len(D["settings"])==20
assert D["continuation"]["additional_checkpoints"]==[120000,140000,160000,180000,200000]
assert D["analysis"]["boundary_margin_t"]==0.005
assert D["planning_forecast"]["panel_t_max"]==1.32
print("DESIGN SELFTEST PASS")
