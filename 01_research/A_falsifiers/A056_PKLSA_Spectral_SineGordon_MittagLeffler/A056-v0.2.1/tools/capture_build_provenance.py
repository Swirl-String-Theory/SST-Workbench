from __future__ import annotations
from pathlib import Path
import argparse, json, sys, platform, glob, os
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.provenance import compiler_probe, build_fingerprint, sha256_file

p=argparse.ArgumentParser()
p.add_argument('--output',default=str(ROOT/'build/COMPILER_PROVENANCE.json'))
a=p.parse_args()
flags=['/O2','/std:c++17','/openmp'] if os.name=='nt' and os.environ.get('SST_NO_OPENMP','0')!='1' else (
      ['/O2','/std:c++17'] if os.name=='nt' else ['-O3','-std=c++17']+([] if os.environ.get('SST_NO_OPENMP','0')=='1' else ['-fopenmp']))
probe=compiler_probe('host')
compile_time=None
try:
    import _a056_native as n
    compile_time=dict(n.build_info())
except Exception as e:
    compile_time={'import_error':repr(e)}
fp=build_fingerprint(compiler=probe,source_files=[ROOT/'cpp/native.cpp'],flags=flags,
                     python_abi={'version':platform.python_version(),'implementation':platform.python_implementation(),'soabi':getattr(sys,'abiflags','')},
                     compile_time_identity=compile_time)
arts=[]
for pattern in ('_a056_native*.pyd','_a056_native*.so','_a056_native*.dylib'):
    for f in ROOT.glob(pattern):
        arts.append({'path':f.name,'bytes':f.stat().st_size,'sha256':sha256_file(f)})
obj={'schema':'SST-COMPILER-PROVENANCE-2','status':'PASS' if arts and 'import_error' not in compile_time else 'UNRESOLVED',
     'build_fingerprint':fp,'artifacts':arts}
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(obj,indent=2)); raise SystemExit(0 if obj['status']=='PASS' else 2)
