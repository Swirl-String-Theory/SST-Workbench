#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
import numpy as np
from sst_counterpulley.core import DEFAULT_DATA,prepare_centerline,write_json
from sst_counterpulley.geometry import make_counter_channels
from sst_counterpulley.orbit import search_relative_periodic_orbit
from sst_counterpulley.rpo_solver import newton_krylov_multiple_shooting

def main()->int:
    ap=argparse.ArgumentParser(description='Alpha-blind Newton-Krylov multiple-shooting RPO solver.')
    ap.add_argument('--data',default=str(DEFAULT_DATA)); ap.add_argument('--n',type=int,default=16)
    ap.add_argument('--offset',type=float,default=.30); ap.add_argument('--eps',type=float,default=.10)
    ap.add_argument('--phase',type=float,default=math.pi/2); ap.add_argument('--period',type=float,default=None)
    ap.add_argument('--segments',type=int,default=4); ap.add_argument('--basis-cols',type=int,default=6)
    ap.add_argument('--dt',type=float,default=.008); ap.add_argument('--iterations',type=int,default=5)
    ap.add_argument('--out',default='newton_krylov_rpo.json'); ap.add_argument('--force-python',action='store_true')
    a=ap.parse_args(); c,m=prepare_centerline(data_path=a.data,n=a.n); D=float(m['D_metadata'])
    p,q,_,_=make_counter_channels(c,a.offset*D,phase=a.phase); x0=np.stack((p,q),axis=0)
    T=a.period
    if T is None:
        seed=search_relative_periodic_orbit(c,D=D,offset_over_D=a.offset,eps_over_D=a.eps,channel_phase=a.phase,
            dt_hat=a.dt,max_time_hat=.9,min_time_hat=.15,snapshot_stride=max(1,int(.03/a.dt)),
            recurrence_tol_over_D=.05,force_python=a.force_python,skip_build=True)
        T=float(seed['candidate']['period_hat'])
    r=newton_krylov_multiple_shooting(c,D=D,state0=x0,seed_period_hat=T,eps_over_D=a.eps,
        segments=a.segments,basis_cols=a.basis_cols,dt_hat=a.dt,max_newton=a.iterations,
        force_python=a.force_python,skip_build=True)
    clean={k:v for k,v in r.items() if k not in {'corrected_initial_state','terminal_state','shooting_vector'}}
    clean['alpha_opened']=False; write_json(a.out,clean); print(json.dumps(clean,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
