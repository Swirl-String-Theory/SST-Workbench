from __future__ import annotations
import argparse, json, sys
from a054_ntaf.physics import qualify_backend

p=argparse.ArgumentParser()
p.add_argument('--policy', default='require_openmp', choices=['allow_numpy','prefer_native','require_native','require_openmp'])
a=p.parse_args()
r=qualify_backend(a.policy)
print(json.dumps({'python_executable':sys.executable,'python_version':sys.version,'qualification':r}, indent=2))
raise SystemExit(0 if r.get('qualified') else 3)
