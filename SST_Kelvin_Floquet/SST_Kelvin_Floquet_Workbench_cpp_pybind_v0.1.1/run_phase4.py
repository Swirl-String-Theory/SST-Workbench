import argparse
from pathlib import Path
from sst_kelvin_workbench.phases import run_phase2, run_phase4
ap=argparse.ArgumentParser(); ap.add_argument('--preset',choices=['quick','full'],default='quick'); ap.add_argument('--out-dir',default='audit_out'); ap.add_argument('--force-python',action='store_true')
a=ap.parse_args(); root=Path(a.out_dir); p2=run_phase2(root/'phase2',preset=a.preset,force_python=a.force_python); s=run_phase4(root/'phase4',p2,preset=a.preset,force_python=a.force_python); print(s['gates'])
