from pathlib import Path
import os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'bin/sst_sycl_worker.exe' if os.name=='nt' else ROOT/'bin/sst_sycl_worker'; out.parent.mkdir(exist_ok=True)
compiler=shutil.which('icpx') or shutil.which('icx')
if not compiler: print('SKIP: oneAPI icpx/icx not found'); raise SystemExit(0)
cmd=[compiler,'-fsycl','-fsycl-device-code-split=per_kernel',str(ROOT/'cpp/sycl_worker.cpp'),'-O2','-o',str(out)]
print(' '.join(cmd)); raise SystemExit(subprocess.call(cmd))
