from __future__ import annotations
import argparse,sys
import numpy as np
from native_ext import backend_info,interaction_energy,biot_savart,gauss_linking,min_segment_distance,doubly_critical_distance

def circle(n=96,R=2.0,z=0.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[R*np.cos(t),R*np.sin(t),np.full(n,z)]
def rel(a,b):return float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(np.linalg.norm(np.asarray(b)),1e-300))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--threads',type=int,default=0);ap.add_argument('--require-native',action='store_true');a=ap.parse_args();bi=backend_info(force_build=False)
    if a.require_native and not bi['native_available']:print('native unavailable');return 4
    if not bi['native_available']:print('SKIP parity: Python fallback only');return 0
    A=circle();B=circle(R=1.0,z=0.25);q=circle(40,R=2.3,z=0.1);t=np.linspace(0,2*np.pi,160,endpoint=False);H=np.c_[0.5+np.cos(t),np.zeros_like(t),np.sin(t)];A1=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];tests={}
    tests['energy_rel']=rel(interaction_energy(A,B,.2,a.threads),interaction_energy(A,B,.2,a.threads,force_python=True));tests['velocity_rel']=rel(biot_savart(A,q,.2,'softcore',a.threads),biot_savart(A,q,.2,'softcore',a.threads,force_python=True));tests['linking_abs']=abs(gauss_linking(A1,H,.0,a.threads)-gauss_linking(A1,H,.0,a.threads,force_python=True));tests['distance_rel']=rel(min_segment_distance(A,A,True,4,a.threads),min_segment_distance(A,A,True,4,a.threads,force_python=True));tests['dcrit_rel']=rel(doubly_critical_distance(A,A,True,5,.22,a.threads),doubly_critical_distance(A,A,True,5,.22,a.threads,force_python=True));tol=2e-10;print(bi,tests);return 0 if max(tests.values())<=tol else 2
if __name__=='__main__':raise SystemExit(main())
