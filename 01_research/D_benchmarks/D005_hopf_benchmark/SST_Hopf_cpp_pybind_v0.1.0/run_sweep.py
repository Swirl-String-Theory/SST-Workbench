#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--resolutions',nargs='+',type=int,default=[24,32,48,64,80]);p.add_argument('--output',default='results/resolution_sweep');a=p.parse_args()
cmd=[sys.executable,'02_analytische_hopf_benchmark.py','--output',a.output,'--resolutions',*map(str,a.resolutions)]
raise SystemExit(subprocess.run(cmd,cwd=Path(__file__).resolve().parent).returncode)
