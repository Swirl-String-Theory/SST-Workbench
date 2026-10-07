from __future__ import annotations
from pathlib import Path
import argparse, json, subprocess, sys

p = argparse.ArgumentParser()
p.add_argument('--campaign', required=True)
p.add_argument('--require-openmp', action='store_true')
a = p.parse_args()
dst = Path(a.campaign) / 'blind_runner'
code = (
    "import sys,json; " + f"sys.path.insert(0,{str(dst)!r}); " +
    "import a054_blind._native as n; "
    "print(json.dumps({'file':n.__file__,'openmp':bool(getattr(n,'openmp_enabled',False))}))"
)
r = subprocess.run([sys.executable, '-c', code], text=True, capture_output=True)
if r.returncode:
    print(r.stderr or r.stdout)
    raise SystemExit(3)
obj = json.loads(r.stdout.strip().splitlines()[-1])
print(json.dumps(obj, indent=2))
if a.require_openmp and not obj['openmp']:
    raise SystemExit(4)
