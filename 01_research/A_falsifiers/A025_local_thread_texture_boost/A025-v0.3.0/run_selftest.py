from __future__ import annotations
import argparse,json,numpy as np
from sst_thread_falsifier.geometry import radius_gyration,kabsch_rms
from sst_thread_falsifier.threads import make_local_thread_bundle,make_radial_source_thread_bundle,closure_diagnostics
from sst_thread_falsifier.diagnostics import background_field_relative_difference,segment_uniformity
from sst_thread_falsifier.native_ext import fallback
from sst_thread_falsifier.native_ext.core import filament_velocity,evolve_frozen_background,reparameterize_closed,backend_name


def trefoil(n=48):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[np.sin(t)+2*np.sin(2*t),np.cos(t)-2*np.cos(2*t),-np.sin(3*t)].astype(float)


def segment_quadrature_reference(x,p0,p1,a,n=20000):
    s=(np.arange(n)+0.5)/n; d=p1-p0; q=p0[None,:]+s[:,None]*d[None,:]; r=x[None,:]-q
    den=(np.sum(r*r,axis=1)+a*a)**1.5
    return np.sum(np.cross(np.broadcast_to(d,(n,3)),r)/den[:,None],axis=0)/n


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--require-native",action="store_true"); ap.add_argument("--tol",type=float,default=5e-9)
    a=ap.parse_args(); P=trefoil(); O=np.array([0,len(P)],np.int64); rg=radius_gyration(P); c=P.mean(0); gamma=1.0
    u0=1/(4*np.pi*rg); dt=.003*rg/u0; kc=.05*rg; tc=.08*rg
    b=make_local_thread_bundle(c,[0.3,-0.2,0.932],rg,rings=1,bundle_radius_rg=1.5,local_half_length_rg=3,return_distance_rg=10,
        local_leg_points=18,remote_leg_points=12,arc_points=12,gamma_per_thread=.01)

    # Exact finite-segment formula vs dense midpoint quadrature on one arbitrary segment.
    x=np.array([0.7,-0.3,1.1]); p0=np.array([-0.2,0.1,-0.5]); p1=np.array([0.8,0.6,0.2]); aa=.17
    exact=fallback._segment_velocity_exact(x,p0,p1,aa); ref=segment_quadrature_reference(x,p0,p1,aa)
    segment_rel=float(np.linalg.norm(exact-ref)/max(float(np.linalg.norm(ref)),1e-15))

    pyv=fallback.filament_velocity(P,b["points"],b["offsets"],b["gammas"],tc)
    cv=filament_velocity(P,b["points"],b["offsets"],b["gammas"],tc,skip_build=True); be=backend_name()
    rel=float(np.linalg.norm(cv-pyv)/max(float(np.linalg.norm(pyv)),1e-15))

    pyx=fallback.evolve_frozen_background(P,O,gamma,kc,b["points"],b["offsets"],b["gammas"],tc,dt,1,np.zeros(3),1)
    cx=evolve_frozen_background(P,O,gamma,kc,b["points"],b["offsets"],b["gammas"],tc,dt,1,np.zeros(3),1,skip_build=True)
    evol_rel=float(np.linalg.norm(cx-pyx)/max(float(np.linalg.norm(pyx)),1e-15))
    U=.35*u0*np.array([0.21,-0.37,0.905]); U=U/np.linalg.norm(U)*(.35*u0)
    xb=evolve_frozen_background(P,O,gamma,kc,b["points"],b["offsets"],b["gammas"],tc,dt,1,U,1,skip_build=True)
    boost_rms=kabsch_rms(cx,xb)/rg

    # Reparameterization must improve a deliberately nonuniform sampling without gross shape displacement.
    u=np.linspace(0.0,1.0,len(P),endpoint=False)**1.7; tt=2*np.pi*u
    Pbad=np.c_[np.sin(tt)+2*np.sin(2*tt),np.cos(tt)-2*np.cos(2*tt),-np.sin(3*tt)]
    Prep=reparameterize_closed(Pbad,O,skip_build=True); uni0=segment_uniformity(Pbad,O); uni1=segment_uniformity(Prep,O)
    reparam_improves=uni1["segment_cv_max"]<uni0["segment_cv_max"]

    cl=closure_diagnostics(b["points"],b["offsets"])
    errs=[]
    for D in (8.0,16.0,32.0):
        rb=make_radial_source_thread_bundle(c,[0.3,-0.2,0.932],rg,D,rings=1,bundle_radius_rg=1.5,local_half_length_rg=3,return_distance_rg=10,
            local_leg_points=18,remote_leg_points=12,arc_points=12,gamma_per_thread=.01)
        errs.append(background_field_relative_difference(P,b,rb,tc,force_python=True,skip_build=True))
    source_monotonic=bool(errs[1]<=errs[0] and errs[2]<=errs[1])

    ok=(segment_rel<=2e-8 and rel<=a.tol and evol_rel<=a.tol and boost_rms<=a.tol and cl["endpoint_count"]==0 and
        cl["closing_edge_over_neighbor_max"]<1.35 and reparam_improves and source_monotonic and (be=="cpp" or not a.require_native))
    print(json.dumps({"backend":be,"exact_segment_vs_dense_quadrature_relative_l2":segment_rel,
        "native_vs_python_field_relative_l2":rel,"native_vs_python_evolution_relative_l2":evol_rel,
        "common_boost_shape_rms_over_rg":boost_rms,"reparameterization_before":uni0,"reparameterization_after":uni1,
        "source_curvature_field_errors_8_16_32_rg":errs,"thread_closure":cl,"tol":a.tol,"status":"PASS" if ok else "FAIL"},indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=="__main__": main()
