from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"balance_design.json").read_text())
assert len(D["settings"])==10
assert len(D["variants"])==2
assert D["n_runs"]==20
assert {v["id"] for v in D["variants"]}=={"K31","T23"}
assert D["variants"][1]["construction"]==["torus 2 3 300"]
assert all(k not in D["frozen_non_qhp_baseline"] for k in ("charge","hooke","power"))
print("DESIGN SELFTEST PASS: 10 settings x 2 variants = 20 runs")
