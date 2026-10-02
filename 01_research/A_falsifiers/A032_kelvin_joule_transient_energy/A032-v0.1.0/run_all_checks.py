#!/usr/bin/env python3
import argparse,json
from native_ext.core import run_smoke
p=argparse.ArgumentParser();p.add_argument("--backend",default="auto",choices=["auto","sycl","openmp","python"]);p.add_argument("--allow-sycl-cpu",action="store_true");p.add_argument("--force-build",action="store_true")
a=p.parse_args();r=run_smoke(a.backend,a.allow_sycl_cpu,a.force_build);print(json.dumps(r,indent=2,default=str));raise SystemExit(0 if r["ok"] else 1)
