from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.geodesic import compute_reduced_monodromy,integrate_ray,shoot_closed_orbit
from fermat_ext.knot_catalog import sample_ideal_knot
from fermat_ext.multistart import collect_seed_family

def constant_clock(point): return 1.0,np.zeros(3),{'backend':{'backend':'analytic-test'},'beta':np.zeros(3),'S':1.0}
def main():
 straight=integrate_ray([0,0,0],[1,0,0],path_length=2,step_count=32,clock_evaluator=constant_clock,record_stride=32); assert straight['status']=='COMPLETED'
 atlas,seeds=collect_seed_family('0_1',epsilon=.0019,centerline_points=2048,stations=1,angles=3,period_multipliers=(1,2),force_python=True,auto_build=False); assert seeds and {s['identity']['direction_sign'] for s in seeds}=={-1,1}
 r=[x for x in atlas['roots'] if x['classification']=='RESOLVED_LOCAL_MINIMUM'][0]; seed={**r,'directions':[r['azimuthal_seed_direction']]}; curve=sample_ideal_knot('0_1',2048)
 shot=shoot_closed_orbit(curve,seed,epsilon=.0019,step_count=24,max_iterations=0,force_python=True,auto_build=False)
 m=compute_reduced_monodromy(curve,shot,epsilon=.0019,force_python=True,auto_build=False); assert m['status']=='SKIPPED_GLOBAL_ORBIT_NOT_CERTIFIED' and m['matrix'] is None
 print('v0.5.1 tests: ok'); return 0
if __name__=='__main__': raise SystemExit(main())
