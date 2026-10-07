from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.blindness import scan_tree
from a056_falsifier.util import read_json
cfg=read_json(ROOT/'configs/framework_smoke.json'); hits=scan_tree(ROOT/'a056_falsifier',cfg['blindness']['forbidden_terms']) + scan_tree(ROOT/'sst_falsifier_framework',cfg['blindness']['forbidden_terms'])
# The forbidden strings are allowed in PRIVATE only, which scan_tree excludes.
print(json.dumps({"status":"PASS" if not hits else "FAIL","hits":hits},indent=2)); raise SystemExit(0 if not hits else 2)
