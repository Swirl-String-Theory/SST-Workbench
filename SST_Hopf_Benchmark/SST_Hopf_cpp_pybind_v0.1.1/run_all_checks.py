#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for cmd in ([sys.executable,'-m','sst_hopf_native.build_ext_if_needed','--strict'],[sys.executable,'run_native_selfcheck.py'],[sys.executable,'run_all.py','--tier','standard','--out-root','results/full_checks']):
    rc=subprocess.run(cmd,cwd=ROOT).returncode
    if rc: raise SystemExit(rc)
raise SystemExit(0)
