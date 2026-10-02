from __future__ import annotations
import argparse,json,numpy as np
from sst_thread_falsifier.geometry import radius_gyration,kabsch_rms
from sst_thread_falsifier.threads import make_local_thread_bundle,closure_diagnostics
from sst_thread_falsifier.native_ext import fallback
from sst_thread_falsifier.native_ext.core import filament_velocity,evolve_frozen_background,backend_name


def trefoil(n=80):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[np.sin(t)+2*np.sin(2*t),np.cos(t)-2*np.cos(2*t),-np.sin(3*t)].astype(float)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--require-native",action="store_true"); ap.add_argument("--tol",type=float,default=5e-10)
    a=ap.parse_args(); P=trefoil(); O=np.array([0,len(P)],np.int64); rg=radius_gyration(P); c=P.mean(0)
    gamma=1.0; u0=1/(4*np.pi*rg); dt=.004*rg/u0; kc=.05*rg; tc=.08*rg
    b=make_local_thread_bundle(c,[0.3,-0.2,0.932],rg,rings=1,bundle_radius_rg=1.5,local_half_length_rg=4,
        return_distance_rg=18,local_leg_points=40,remote_leg_points=20,arc_points=20,gamma_per_thread=.01)
    pyv=fallback.filament_velocity(P,b["points"],b["offsets"],b["gammas"],tc)
    cv=filament_velocity(P,b["points"],b["offsets"],b["gammas"],tc,skip_build=True)
    rel=float(np.linalg.norm(cv-pyv)/max(float(np.linalg.norm(pyv)),1e-15)); be=backend_name()
    pyx=fallback.evolve_frozen_background(P,O,gamma,kc,b["points"],b["offsets"],b["gammas"],tc,dt,2,np.zeros(3))
    cx=evolve_frozen_background(P,O,gamma,kc,b["points"],b["offsets"],b["gammas"],tc,dt,2,np.zeros(3),skip_build=True)
    evol_rel=float(np.linalg.norm(cx-pyx)/max(float(np.linalg.norm(pyx)),1e-15))
    U=.4*u0*np.array([0.21,-0.37,0.905]); U=U/np.linalg.norm(U)*(.4*u0)
    xb=evolve_frozen_background(P,O,gamma,kc,b["points"],b["offsets"],b["gammas"],tc,dt,2,U,skip_build=True)
    boost_rms=kabsch_rms(cx,xb)/rg; cl=closure_diagnostics(b["points"],b["offsets"])
    ok=(rel<=a.tol and evol_rel<=a.tol and boost_rms<=a.tol and cl["endpoint_count"]==0 and cl["closing_edge_over_neighbor_max"]<1.25 and (be=="cpp" or not a.require_native))
    print(json.dumps({"backend":be,"native_vs_python_field_relative_l2":rel,"native_vs_python_evolution_relative_l2":evol_rel,
        "common_boost_shape_rms_over_rg":boost_rms,"thread_closure":cl,"tol":a.tol,"status":"PASS" if ok else "FAIL"},indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=="__main__": main()
