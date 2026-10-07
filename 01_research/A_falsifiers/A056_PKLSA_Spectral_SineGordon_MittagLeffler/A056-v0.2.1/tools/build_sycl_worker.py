from __future__ import annotations
from pathlib import Path
import json, os, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.provenance import compiler_probe, build_fingerprint, sha256_file

source=ROOT/'cpp/sycl_worker.cpp'; build=ROOT/'build'; build.mkdir(exist_ok=True)
probe=compiler_probe('sycl')
if not probe.get('available'):
    print(json.dumps({'status':'SKIP','reason':'oneAPI icpx/icx/dpcpp not found'},indent=2)); raise SystemExit(0)
compiler=probe['executable']
flags=['-fsycl','-fsycl-device-code-split=per_kernel','-O3','-fp-model=precise']
fp=build_fingerprint(compiler=probe,source_files=[source],flags=flags,
                     python_abi={'role':'standalone-sycl-worker'},compile_time_identity={'precision_modes':['fp32','dd32'],'dd32_is_ieee_fp64':False})
key=fp['fingerprint'][:16]
ext='.exe' if os.name=='nt' else ''
out=build/f'sst_sycl_worker_{key}{ext}'
manifest=build/'SYCL_WORKER_BUILD.json'
if out.exists():
    obj={'schema':'SST-SYCL-WORKER-BUILD-2','status':'PASS','reused':True,'worker':str(out),'worker_sha256':sha256_file(out),'build_fingerprint':fp}
    manifest.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(obj,indent=2)); raise SystemExit(0)

tmp=build/f'.sst_sycl_worker_{key}_{os.getpid()}.tmp{ext}'
cmd=[compiler,*flags,str(source),'-o',str(tmp)]
print(' '.join(cmd))
r=subprocess.run(cmd)
if r.returncode!=0:
    raise SystemExit(r.returncode)
os.replace(tmp,out)
obj={'schema':'SST-SYCL-WORKER-BUILD-2','status':'PASS','reused':False,'worker':str(out),'worker_sha256':sha256_file(out),'command':cmd,'build_fingerprint':fp}
manifest.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(obj,indent=2))
