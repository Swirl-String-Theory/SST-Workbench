from __future__ import annotations
import numpy as np
from .geometry import normalize_geometry,resample_geometry,parity_mirror_physical,time_reverse_geometry,pack_components
from .physics import require_native,centerline_helicity_xi,gauss_helicity_xi,relative_equilibrium_metrics,candidate_metrics
from native_ext import velocity_at_points_multi


def trefoil(n=64):
    t=np.linspace(0,2*np.pi,n,endpoint=False); q=np.column_stack([(2+0.65*np.cos(3*t))*np.cos(2*t),(2+0.65*np.cos(3*t))*np.sin(2*t),0.65*np.sin(3*t)])
    return normalize_geometry([q])[0]

def ring(n=48,plane=0,shift=(0,0,0)):
    t=np.linspace(0,2*np.pi,n,endpoint=False); q=np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])
    if plane==1: q=q[:,[0,2,1]]
    q=q+np.asarray(shift,float); return q


def run():
    require_native(); a=0.04
    # Multi-component superposition test: no artificial connector may exist.
    multi,_=normalize_geometry([ring(32,0,(-0.8,0,0)),ring(32,1,(0.8,0,0))]); packed,offs=pack_components(multi)
    probes=np.array([[0.1,0.2,0.3],[-0.2,0.1,0.05]],float)
    vm=np.asarray(velocity_at_points_multi(packed,offs,probes,a,1.0),float); vs=np.zeros_like(vm)
    for c in multi:
        p,o=pack_components([c]); vs+=np.asarray(velocity_at_points_multi(p,o,probes,a,1.0),float)
    super_err=np.linalg.norm(vm-vs)/max(np.linalg.norm(vm),1e-30)
    if super_err>2e-12: raise AssertionError(f"multi-component superposition failed: {super_err}")

    x=trefoil(56); y=parity_mirror_physical(x); tr=time_reverse_geometry(x)
    hx=centerline_helicity_xi(x,a); hy=centerline_helicity_xi(y,a); ht=centerline_helicity_xi(tr,a)
    hodd=abs(hx+hy)/max(abs(hx)+abs(hy),1e-30); heven=abs(hx-ht)/max(abs(hx)+abs(ht),1e-30)
    gx=gauss_helicity_xi(x); gy=gauss_helicity_xi(y); godd=abs(gx+gy)/max(abs(gx)+abs(gy),1e-30)
    if hodd>2e-10 or heven>2e-10 or godd>2e-10: raise AssertionError(f"helicity symmetry failed: {hodd=} {heven=} {godd=}")
    # Direct parity vector transformation on off-filament probes.
    R=np.diag([-1.,1.,1.]); px,ox=pack_components(x); py,oy=pack_components(y); pm=probes@R.T
    vx=np.asarray(velocity_at_points_multi(px,ox,probes,a,1.0)); vy=np.asarray(velocity_at_points_multi(py,oy,pm,a,1.0)); verr=np.linalg.norm(vy-vx@R.T)/max(np.linalg.norm(vx),1e-30)
    if verr>2e-10: raise AssertionError(f"velocity parity failed: {verr}")
    rex=relative_equilibrium_metrics(x,a)["relative_residual"]; rey=relative_equilibrium_metrics(y,a)["relative_residual"]; rerr=abs(rex-rey)/max(rex+rey,1e-30)
    if rerr>2e-10: raise AssertionError(f"RE parity failed: {rerr}")

    cfg={"core_fraction":a,"trajectory_time":0.04,"trajectory_cfl":0.20,"min_trajectory_steps":10,"max_trajectory_steps":36,"trajectory_samples":8,
         "jvp_eps_fraction":3e-5,"packet_width":0.09,"excitation_centers":[0.25,0.75],"carrier_modes":[2],"max_excited_components":1,"excite_all_components":False,
         "compute_tube_helicity":False,"compute_frozen_spectrum":False,"transport_dead_zone":0.02}
    mx=candidate_metrics(x,cfg); my=candidate_metrics(y,cfg)
    pabs=abs(mx["transport_pi"]+my["transport_pi"]); pscale=max(abs(mx["transport_pi"])+abs(my["transport_pi"]),1e-8)
    if pabs>1e-5+0.03*pscale: raise AssertionError(f"trajectory transport parity failed: {mx['transport_pi']}, {my['transport_pi']}")
    print({"selftest":"PASS","multi_superposition_relative_error":super_err,"centerline_helicity_pair":[hx,hy],"helicity_odd_residual":hodd,
           "time_reverse_helicity":ht,"helicity_time_even_residual":heven,"gauss_odd_residual":godd,"velocity_parity_relative_error":verr,
           "relative_equilibrium_pair":[rex,rey],"relative_equilibrium_parity_residual":rerr,"trajectory_transport_pair":[mx["transport_pi"],my["transport_pi"]]})

if __name__=="__main__": run()
