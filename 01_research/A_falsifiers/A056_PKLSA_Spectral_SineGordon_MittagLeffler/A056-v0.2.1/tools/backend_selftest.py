from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.backend_selftest import run_backend_selftest
p=argparse.ArgumentParser(); p.add_argument('--allow-missing-native',action='store_true'); p.add_argument('--output',default=str(ROOT/'build/BACKEND_SELFTEST.json')); a=p.parse_args()
obj=run_backend_selftest(ROOT,require_native=not a.allow_missing_native)
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(obj,indent=2)); raise SystemExit(0 if obj['status']=='PASS' else 2)
