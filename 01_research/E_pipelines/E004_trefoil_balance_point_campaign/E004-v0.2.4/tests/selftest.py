from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))
assert D["version"]=="0.2.4"
assert D["n_panel"]==16
assert [x["t"] for x in D["panel"]]==[1.3,1.31,1.32,1.325,1.33,1.335,1.34,1.345,1.35,1.355,1.36,1.365,1.37,1.375,1.38,1.4]
assert D["cold_start"]["overlap_ids"]==["E01","E02","E03"]
assert D["continuation"]["checkpoints"]==list(range(220000,400001,20000))
assert D["source"]["all_20_source_i0_identical"] is True
print("DESIGN SELFTEST PASS")
