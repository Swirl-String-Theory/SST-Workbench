from __future__ import annotations
import sys, time, json, math, argparse, os
from pathlib import Path
_ROOT=Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path: sys.path.insert(0,str(_ROOT))
import numpy as np
from native_ext.sycl_worker import worker_info, biot_savart, shutdown_worker
from native_ext.fallback import biot_savart as host_biot


def _rel(a,b):
    den=max(float(np.linalg.norm(b)),1e-30)
    return float(np.linalg.norm(a-b)/den)

def _case_ring(n=96):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    p=np.c_[np.cos(t),np.sin(t),0.07*np.sin(3*t)]
    return 'warped_ring',p

def _case_trefoil(n=128):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    p=np.c_[
        (2.0+0.55*np.cos(3*t))*np.cos(2*t),
        (2.0+0.55*np.cos(3*t))*np.sin(2*t),
        0.55*np.sin(3*t),
    ]
    p/=np.sqrt(np.mean(np.sum(p*p,axis=1)))
    return 'trefoil_parametric',p

def _case_cancellation(n=120):
    # A nearly planar wavy loop gives substantial cancellation among remote
    # segment contributions and is a better precision stressor than a circle.
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    r=1.0+0.16*np.cos(5*t)+0.06*np.cos(11*t)
    p=np.c_[r*np.cos(t),r*np.sin(t),0.025*np.sin(7*t)]
    return 'cancellation_loop',p

def _velocity_case(name,p,core=0.04):
    t0=time.perf_counter(); ref=host_biot(p,p,1.0,core); tref=time.perf_counter()-t0
    t0=time.perf_counter(); f32,lab32=biot_savart(p,p,gamma=1.0,core=core,numeric_mode='fp32'); tf32=time.perf_counter()-t0
    t0=time.perf_counter(); dd,labdd=biot_savart(p,p,gamma=1.0,core=core,numeric_mode='dd32'); tdd=time.perf_counter()-t0
    e32=_rel(f32,ref); edd=_rel(dd,ref)
    return {
        'case':name,'n':len(p),'fp32_backend':lab32,'dd32_backend':labdd,
        'fp32_relative_l2':e32,'dd32_relative_l2':edd,
        'improvement_factor':float(e32/max(edd,1e-30)),
        'fp32_max_abs':float(np.max(np.abs(f32-ref))),
        'dd32_max_abs':float(np.max(np.abs(dd-ref))),
        'python_fp64_s':tref,'fp32_s':tf32,'dd32_s':tdd,
        'dd32_over_fp32_time':float(tdd/max(tf32,1e-12)),
        'finite':bool(np.all(np.isfinite(dd))),
    }

def _directional_jacobian_case(n=72,eps=2e-5,core=0.05):
    name,p=_case_trefoil(n)
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    d=np.c_[np.cos(5*t),np.sin(4*t),np.cos(3*t)]
    d/=max(float(np.sqrt(np.mean(np.sum(d*d,axis=1)))),1e-30)
    pp=p+eps*d; pm=p-eps*d
    rp=host_biot(pp,pp,1.0,core); rm=host_biot(pm,pm,1.0,core); jref=(rp-rm)/(2*eps)
    fpp,_=biot_savart(pp,pp,gamma=1.0,core=core,numeric_mode='fp32')
    fpm,_=biot_savart(pm,pm,gamma=1.0,core=core,numeric_mode='fp32')
    j32=(fpp-fpm)/(2*eps)
    ddp,_=biot_savart(pp,pp,gamma=1.0,core=core,numeric_mode='dd32')
    ddm,_=biot_savart(pm,pm,gamma=1.0,core=core,numeric_mode='dd32')
    jdd=(ddp-ddm)/(2*eps)
    e32=_rel(j32,jref); edd=_rel(jdd,jref)
    return {
        'case':'directional_jacobian','n':n,'eps':eps,
        'fp32_relative_l2':e32,'dd32_relative_l2':edd,
        'improvement_factor':float(e32/max(edd,1e-30)),
        'fp32_max_abs':float(np.max(np.abs(j32-jref))),
        'dd32_max_abs':float(np.max(np.abs(jdd-jref))),
        'finite':bool(np.all(np.isfinite(jdd))),
    }

def main():
    ap=argparse.ArgumentParser(description='Arc FP32 vs FP32x2/DD32 parity against CPU/Python FP64')
    ap.add_argument('--velocity-rel-max',type=float,default=1e-8)
    ap.add_argument('--jacobian-rel-max',type=float,default=2e-6)
    ap.add_argument('--min-improvement',type=float,default=20.0)
    ap.add_argument('--strict',action='store_true')
    a=ap.parse_args()
    os.environ['SST_SYCL_ALLOW_FP32']='1'
    info=worker_info(start=True)
    cases=[]
    for maker in (_case_ring,_case_trefoil,_case_cancellation):
        name,p=maker(); cases.append(_velocity_case(name,p))
    jac=_directional_jacobian_case(); cases.append(jac)
    velocity=[x for x in cases if x['case']!='directional_jacobian']
    worst_vel=max(x['dd32_relative_l2'] for x in velocity)
    min_imp=min(x['improvement_factor'] for x in cases)
    pass_velocity=all(x['finite'] and x['dd32_relative_l2']<=a.velocity_rel_max for x in velocity)
    pass_jac=jac['finite'] and jac['dd32_relative_l2']<=a.jacobian_rel_max
    pass_improvement=min_imp>=a.min_improvement
    verdict=bool(pass_velocity and pass_jac and pass_improvement)
    out={
        'device':info,
        'numeric_mode':'FP32x2 double-single (experimental; not IEEE FP64)',
        'nominal_significand_bits':48,
        'thresholds':{'velocity_relative_l2_max':a.velocity_rel_max,'directional_jacobian_relative_l2_max':a.jacobian_rel_max,'minimum_improvement_factor':a.min_improvement},
        'cases':cases,
        'summary':{'worst_dd32_velocity_relative_l2':worst_vel,'dd32_directional_jacobian_relative_l2':jac['dd32_relative_l2'],'minimum_improvement_factor':min_imp,'PASS':verdict},
    }
    print(json.dumps(out,indent=2))
    build=_ROOT/'build'; build.mkdir(exist_ok=True)
    (build/'sycl_dd32_smoke.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    shutdown_worker()
    return 0 if (verdict or not a.strict) else 2

if __name__=='__main__': raise SystemExit(main())
