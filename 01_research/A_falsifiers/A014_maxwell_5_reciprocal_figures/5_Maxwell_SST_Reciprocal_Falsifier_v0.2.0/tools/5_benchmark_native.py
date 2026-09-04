from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'python'))
from sst_reciprocal.io import load_xyz,flatten_components
from maxwell5_native import analyze_geometry

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--knots-dir',required=True); ap.add_argument('--threads',type=int,default=8); args=ap.parse_args(); root=Path(args.knots_dir); p=root/'knot_3.1_final.txt'; m=json.loads((root/'knot_3.1_final.metrics.json').read_text(encoding='utf-8')); comps=load_xyz(p,m['vertices_per_component']); P=flatten_components(comps); C=np.asarray(m['vertices_per_component'],np.int64); radius=float(m['thickness'])
    # warm build/import
    analyze_geometry(P,C,radius=radius,contact_tol=1e-4,threads=args.threads,require_native=True)
    t0=time.perf_counter(); rn=analyze_geometry(P,C,radius=radius,contact_tol=1e-4,threads=args.threads,require_native=True); tn=time.perf_counter()-t0
    t0=time.perf_counter(); rp=analyze_geometry(P,C,radius=radius,contact_tol=1e-4,threads=1,force_python=True); tp=time.perf_counter()-t0
    print(json.dumps({'case':'knot_3.1_final','vertices':len(P),'threads':args.threads,'cpp_seconds':tn,'python_seconds':tp,'speedup_python_over_cpp':tp/max(tn,1e-12),'cpp_contacts':rn['metrics']['active_strut_count'],'python_contacts':rp['metrics']['active_strut_count']},indent=2))
if __name__=='__main__': main()
