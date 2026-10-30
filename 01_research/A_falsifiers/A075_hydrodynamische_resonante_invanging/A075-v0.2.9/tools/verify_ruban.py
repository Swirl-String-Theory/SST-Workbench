"""Reproducible Ruban seed check; no framework mutation."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiment.ruban import verify_geometry,PRIMARY,resolution_gate
if __name__=='__main__':
    z=verify_geometry(ROOT/'inputs/ruban_t23'/PRIMARY)
    print(json.dumps({'seed_fidelity':z,'default_resolution_N80':resolution_gate(10,80,.5)},indent=2))
    raise SystemExit(0 if z['geometric_fidelity_pass'] else 2)
