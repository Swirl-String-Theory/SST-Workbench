from pathlib import Path
import os,subprocess,json
ROOT=Path(__file__).resolve().parents[1]; exe=ROOT/('bin/sst_sycl_worker.exe' if os.name=='nt' else 'bin/sst_sycl_worker')
if not exe.exists(): print(json.dumps({'status':'SKIP','reason':'worker not built'})); raise SystemExit(0)
env=os.environ.copy(); env.setdefault('ONEAPI_DEVICE_SELECTOR','level_zero:gpu'); env.setdefault('SYCL_CACHE_PERSISTENT','0')
r=subprocess.run([str(exe)],env=env,text=True,capture_output=True); print(r.stdout.strip() or r.stderr.strip()); raise SystemExit(r.returncode)
