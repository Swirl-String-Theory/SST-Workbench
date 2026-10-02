#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from sst_hopf_native import backend_info
import subprocess, sys

print(json.dumps(backend_info(), indent=2))
cmd=[sys.executable,'02_analytische_hopf_benchmark.py','--output','results/example','--resolutions','24','48','64']
raise SystemExit(subprocess.run(cmd,cwd=Path(__file__).resolve().parent).returncode)
