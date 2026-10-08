from pathlib import Path
import argparse,json,sys
FRAMEWORK=Path(__file__).resolve().parents[1]
if str(FRAMEWORK) not in sys.path: sys.path.insert(0,str(FRAMEWORK))
from sst_falsifier.sycl_worker import build_worker,probe_worker
p=argparse.ArgumentParser();p.add_argument("instance_root");p.add_argument("--force",action="store_true");a=p.parse_args();b=build_worker(Path(a.instance_root),force=a.force);print(json.dumps(b,indent=2));
if b.get("success"): print(json.dumps(probe_worker(Path(a.instance_root)),indent=2))
raise SystemExit(0 if b.get("success") else 1)
