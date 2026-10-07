from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from a056_falsifier.blind import scan_tree
# Sentinel values/labels are defined only in this checker and never in the blind scientific config.
forbidden=["1.09384563e6","1.40897017e-15","3.8934358266918687e18","7.0e-7","29.053507","3.02563e43","fine-structure","electron","proton","neutron","5_2","6_1","trefoil"]
hits=scan_tree(ROOT,forbidden)
hits=[h for h in hits if h["path"] != "tools/check_blind.py"]
if hits:
    print(json.dumps(hits,indent=2)); raise SystemExit("BLIND SCAN FAIL")
print("BLIND SCAN PASS")
