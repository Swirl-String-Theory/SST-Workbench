import numpy as np
from src.euler_pilot import run_pilot

def test_euler_pilot_is_smooth_and_knots_remain():
 t=np.linspace(0,2*np.pi,90,endpoint=False)
 circle=np.array([np.cos(t),np.sin(t),np.zeros_like(t)]).T
 r,data=run_pilot(circle,grid=12,steps=2)
 assert r['status']=='EXPLORATORY_PERIODIC_EULER_NOT_CERTIFIED'
 assert np.isfinite(r['energy_relative_drift'])
 assert abs(r['energy_relative_drift'])<0.05
 assert r['initial_knot']['alexander_det_at_minus_one']==1
 assert r['final_knot']['alexander_det_at_minus_one']==1
 assert data['filaments'].shape==(3,1,len(t),3)
