from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fermat_ext.hole_bundle import HoleBundleParameters,bundle_beta_and_jacobian,clock_chain

def main():
 b=HoleBundleParameters(1.0,3.0,0.5); pts=np.array([[0.,0.,0.],[.5,0,0],[1.5,0,0],[4,0,0]])
 beta,j=bundle_beta_and_jacobian(pts,b); assert beta.shape==(4,3) and j.shape==(4,3,3); assert np.all(np.isfinite(beta)) and np.all(np.isfinite(j)); assert np.linalg.norm(beta[-1])<1e-15
 h=1e-6; p=np.array([[.5,.2,0.]]); bb,jj=bundle_beta_and_jacobian(p,b); num=np.zeros((3,3))
 for k in range(3):
  pp=p.copy(); pm=p.copy(); pp[0,k]+=h; pm[0,k]-=h; bp,_=bundle_beta_and_jacobian(pp,b); bm,_=bundle_beta_and_jacobian(pm,b); num[:,k]=(bp[0]-bm[0])/(2*h)
 assert np.max(np.abs(num-jj[0]))<1e-7
 c=clock_chain(b); assert c['Omega_clock_over_c_per_rc']==.5*c['mean_vorticity_over_c_per_rc']
 print('v0.6.1 tests: ok'); return 0
if __name__=='__main__': raise SystemExit(main())
