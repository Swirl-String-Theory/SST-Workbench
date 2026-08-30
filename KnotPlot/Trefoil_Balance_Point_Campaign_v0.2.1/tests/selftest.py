from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];D=json.loads((ROOT/"balance_design.json").read_text())
assert D["geometry"]["construction"]==["load 3.1"]
assert D["n_settings"]==20
assert D["standard"]["max_iteration"]==30000
assert D["extended"]["max_iteration"]==60000
assert len(D["qhp_ray"]["t_values"])==20
assert sum(s["is_prior_anchor"] for s in D["settings"])==1
print("DESIGN SELFTEST PASS: 20 K31 q/h/p points, 30k standard, 60k all-state extension")
