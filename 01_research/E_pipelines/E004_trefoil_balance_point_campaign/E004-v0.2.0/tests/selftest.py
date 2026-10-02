from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"balance_design.json").read_text())
assert D["geometry"]["construction"]==["load 3.1"]
assert D["n_settings"]==20 and D["n_runs"]==20
assert len(D["lanes"]["full_balance_ray_extended"]["t_values"])==12
assert len(D["lanes"]["hooke_dominant_bracket"]["hooke_values"])==8
assert len({s["id"] for s in D["settings"]})==20
assert all(s["scan_value"]>1.0 for s in D["settings"] if s["lane"]=="full_balance_ray_extended")
assert all(s["hooke"]>1.30 for s in D["settings"] if s["lane"]=="hooke_dominant_bracket")
print("DESIGN SELFTEST PASS: K31 only, 20 new settings, 12+8 frozen lanes")
