from pathlib import Path
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
D=json.loads((ROOT/"balance_design.json").read_text())
assert D["version"]=="0.2.2"
assert len(D["settings"])==20
assert D["continuation"]["additional_checkpoints"]==[70000,80000,90000,100000]
assert D["analysis"]["zero_track_slope_abs_t_per_10000_tolerance"]==1e-3
assert D["analysis"]["zero_track_last3_spread_tolerance"]==2.5e-3
print("DESIGN SELFTEST PASS")
