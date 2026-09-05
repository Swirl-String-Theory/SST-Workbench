import argparse
from pathlib import Path
from sst_kelvin_workbench.phases import run_phase1
ap=argparse.ArgumentParser(); ap.add_argument('--preset',choices=['quick','full'],default='quick'); ap.add_argument('--out-dir',default='audit_out/phase1'); ap.add_argument('--force-python',action='store_true')
a=ap.parse_args(); s=run_phase1(Path(a.out_dir),preset=a.preset,force_python=a.force_python); print(s['gates'])
