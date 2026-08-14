from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from native_ext import backend_info,polyline_stats,interaction_energy,interaction_force_gradient
from sst_maxwell_falsifier.geometry import load_centerline,resample_closed,center_components,characteristic_diameter

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--knots-dir',type=Path,required=True);ap.add_argument('--file',default='knot_3.1_final.txt');ap.add_argument('--threads',type=int,default=0);ap.add_argument('--require-native',action='store_true');a=ap.parse_args()
 info=backend_info(force_build=True)
 if a.require_native and not info['native_available']:raise SystemExit('native backend unavailable')
 p=a.knots_dir/a.file; comps=load_centerline(p); c=resample_closed(comps[0],64); c,_=center_components([c]);c=c[0];D=characteristic_diameter([c]);b=c+np.array([2.5*D,0,0]);core=.05*D
 vals={}
 for py in [False,True]:
  tag='python' if py else info['backend'];vals[tag]={'stats':dict(polyline_stats(c,force_python=py)),'E':interaction_energy(c,b,core,a.threads,force_python=py),'F':interaction_force_gradient(c,b,core,a.threads,force_python=py).tolist()}
 E0=vals['python']['E'];F0=np.array(vals['python']['F']);E1=vals[info['backend']]['E'];F1=np.array(vals[info['backend']]['F'])
 vals['relative_error']={'E':abs(E1-E0)/max(abs(E0),1e-30),'F':float(np.linalg.norm(F1-F0)/max(np.linalg.norm(F0),1e-30))}
 print(json.dumps(vals,indent=2));return 0 if vals['relative_error']['E']<1e-10 and vals['relative_error']['F']<1e-10 else 2
if __name__=='__main__':raise SystemExit(main())
