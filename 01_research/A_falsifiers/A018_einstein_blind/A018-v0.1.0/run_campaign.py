from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
from sst_einstein.campaign import run_campaign

p=argparse.ArgumentParser(description="Run Einstein–SST blind falsifier campaign")
p.add_argument("--config",default="configs/standard.json")
p.add_argument("--outdir",default=None)
p.add_argument("--input-root",default=None)
p.add_argument("--allow-python",action="store_true",help="Debug/reference only; normal research runners require native C++")
p.add_argument("--no-zip",action="store_true")
a=p.parse_args()
if a.outdir is None:
    tier=Path(a.config).stem; stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); a.outdir=f"results_{tier}_blind_{stamp}"
summary=run_campaign(a.config,a.outdir,require_native=not a.allow_python,input_root=a.input_root,zip_results=not a.no_zip)
print(summary)
