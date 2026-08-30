from __future__ import annotations
import tempfile
from pathlib import Path
import numpy as np
from .geometry import normalize_curve,resample_closed,parity_mirror_physical,time_reverse_filament,frames
from .physics import require_native,tube_helicity_xi,build_operator,initial_packet,evolve_packet
from native_ext import velocity_at_points,writhe


def trefoil(n=96):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    # Standard smooth (2,3)-torus trefoil.
    x=(2+0.65*np.cos(3*t))*np.cos(2*t)
    y=(2+0.65*np.cos(3*t))*np.sin(2*t)
    z=0.65*np.sin(3*t)
    q=np.column_stack([x,y,z]); q,_=normalize_curve(q); return q

def run():
    require_native()
    x=trefoil(72); y=parity_mirror_physical(x)
    wrx=float(writhe(x,1e-10)); wry=float(writhe(y,1e-10))
    if abs(wrx+wry)>0.05*max(abs(wrx)+abs(wry),1e-12):
        raise AssertionError(f"writhe parity failed: {wrx}, {wry}")
    a=0.05
    hx=tube_helicity_xi(x,a,2,6); hy=tube_helicity_xi(y,a,2,6)
    hres=abs(hx+hy)/max(abs(hx)+abs(hy),1e-12)
    if hres>0.25:
        raise AssertionError(f"helicity parity failed: {hx}, {hy}, residual={hres}")
    # Direct velocity parity check at parity-related off-filament probes.
    p=np.array([[0.13,0.02,0.01],[-0.08,0.03,0.04]],float)
    R=np.diag([-1.0,1.0,1.0])
    pm=p@R.T
    vx=np.asarray(velocity_at_points(x,p,a,1.0)); vy=np.asarray(velocity_at_points(y,pm,a,1.0))
    rel=np.linalg.norm(vy-vx@R.T)/max(np.linalg.norm(vx),1e-12)
    if rel>2e-10: raise AssertionError(f"velocity parity failed: rel={rel}")
    # Transport parity smoke test on a smaller pair.  Symmetric packet centers are
    # required because parity maps s -> 1-s.
    xs=resample_closed(x,48); xs,_=normalize_curve(xs); ys=parity_mirror_physical(xs); ts=time_reverse_filament(xs)
    Jx,mx=build_operator(xs,a,2e-5); Jy,my=build_operator(ys,a,2e-5); Jt,mt=build_operator(ts,a,2e-5)
    pix=[]; piy=[]; pit=[]
    for center in (0.25,0.75):
        ux=initial_packet(len(xs),center,0.08,3)
        uy=initial_packet(len(ys),center,0.08,3)
        ut=initial_packet(len(ts),center,0.08,3)
        dx=evolve_packet(Jx,ux,0.4,16,0.08,mx["normalized_inf_rate"])
        dy=evolve_packet(Jy,uy,0.4,16,0.08,my["normalized_inf_rate"])
        dt=evolve_packet(Jt,ut,0.4,16,0.08,mt["normalized_inf_rate"])
        pix.append(dx["pi_mean_late"]); piy.append(dy["pi_mean_late"]); pit.append(dt["pi_mean_late"])
    px=float(np.mean(pix)); py=float(np.mean(piy)); pt=float(np.mean(pit))
    pres=abs(px+py)/max(abs(px)+abs(py),1e-12)
    tres=abs(px-pt)/max(abs(px)+abs(pt),1e-12)
    ht=tube_helicity_xi(ts,a,2,6)
    hte=abs(hx-ht)/max(abs(hx)+abs(ht),1e-12)
    if pres>0.03:
        raise AssertionError(f"transport parity failed: Pi={px},{py}, residual={pres}")
    if tres>0.03 or hte>0.03:
        raise AssertionError(f"time-reversal evenness failed: Pi residual={tres}, XiH residual={hte}")
    print({"selftest":"PASS","writhe_pair":[wrx,wry],"xiH_pair":[hx,hy],"helicity_odd_residual":hres,
           "velocity_parity_relative_error":rel,"transport_pair":[px,py],"transport_odd_residual":pres,
           "time_reversal_xiH":ht,"time_reversal_helicity_even_residual":hte,
           "time_reversal_transport_pi":pt,"time_reversal_transport_even_residual":tres})
if __name__=="__main__": run()
