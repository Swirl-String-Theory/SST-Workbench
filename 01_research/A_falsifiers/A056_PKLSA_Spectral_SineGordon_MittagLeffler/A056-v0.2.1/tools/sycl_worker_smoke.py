from __future__ import annotations
from pathlib import Path
import argparse,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--require',action='store_true'); p.add_argument('--probe-only',action='store_true'); a=p.parse_args()
manifest=ROOT/'build/SYCL_WORKER_BUILD.json'
if not manifest.exists():
    obj={'status':'FAIL' if a.require else 'SKIP','reason':'worker build manifest missing'}; print(json.dumps(obj)); raise SystemExit(2 if a.require else 0)
m=json.loads(manifest.read_text(encoding='utf-8')); exe=Path(m['worker'])
if not exe.exists():
    obj={'status':'FAIL' if a.require else 'SKIP','reason':'worker binary missing','worker':str(exe)}; print(json.dumps(obj)); raise SystemExit(2 if a.require else 0)
env=os.environ.copy(); env.setdefault('ONEAPI_DEVICE_SELECTOR','level_zero:gpu'); env.setdefault('SYCL_CACHE_PERSISTENT','0')
args=[str(exe)] + ([] if a.probe_only else ['--dd32-selftest'])
r=subprocess.run(args,env=env,text=True,capture_output=True)
raw=(r.stdout.strip() or r.stderr.strip()); print(raw)
try: obj=json.loads(raw.splitlines()[-1])
except Exception: obj={'status':'FAIL','raw':raw}
out=ROOT/'build/DD32_BACKEND_SELFTEST.json'; out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if obj.get('status')!='PASS': raise SystemExit(2 if a.require else (r.returncode or 0))
raise SystemExit(0)
