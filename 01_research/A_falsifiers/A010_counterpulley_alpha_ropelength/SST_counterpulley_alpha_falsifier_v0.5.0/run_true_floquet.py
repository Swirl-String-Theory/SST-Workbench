#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,numpy as np
from sst_counterpulley.core import DEFAULT_DATA,prepare_centerline,write_json
from sst_counterpulley.geometry import make_counter_channels
from sst_counterpulley.orbit import search_relative_periodic_orbit
from sst_counterpulley.rpo_solver import newton_krylov_multiple_shooting
from sst_counterpulley.monodromy import full_relative_monodromy_fd,kelvin_restricted_true_monodromy

def main()->int:
    ap=argparse.ArgumentParser(description='v0.5: construct true D(g^-1 o phi_T) only after Newton-Krylov RPO acceptance.')
    ap.add_argument('--data',default=str(DEFAULT_DATA)); ap.add_argument('--n',type=int,default=16)
    ap.add_argument('--offset',type=float,default=.25); ap.add_argument('--eps',type=float,default=.10)
    ap.add_argument('--phase',type=float,default=math.pi/2); ap.add_argument('--period',type=float,default=None)
    ap.add_argument('--dt',type=float,default=.008); ap.add_argument('--segments',type=int,default=4)
    ap.add_argument('--basis-cols',type=int,default=10); ap.add_argument('--iterations',type=int,default=5)
    ap.add_argument('--out',default='true_floquet.json'); ap.add_argument('--force-python',action='store_true')
    a=ap.parse_args(); c,m=prepare_centerline(data_path=a.data,n=a.n); D=float(m['D_metadata'])
    p,q,_,_=make_counter_channels(c,a.offset*D,phase=a.phase); x0=np.stack((p,q),axis=0)
    T=a.period
    if T is None:
        seed=search_relative_periodic_orbit(c,D=D,offset_over_D=a.offset,eps_over_D=a.eps,channel_phase=a.phase,
            dt_hat=a.dt,max_time_hat=.9,min_time_hat=.15,snapshot_stride=max(1,int(.03/a.dt)),
            recurrence_tol_over_D=.05,force_python=a.force_python,skip_build=True)
        T=float(seed['candidate']['period_hat'])
    nk=newton_krylov_multiple_shooting(c,D=D,state0=x0,seed_period_hat=T,eps_over_D=a.eps,
        segments=a.segments,basis_cols=a.basis_cols,dt_hat=a.dt,max_newton=a.iterations,
        recurrence_tol_over_D=.05,vf_tol=.10,force_python=a.force_python,skip_build=True)
    cand=nk['result']
    if not cand['accepted']:
        out={'status':'BLOCKED_NO_NEWTON_KRYLOV_RPO','alpha_opened':False,'candidate':cand,
             'reason':'Full-state recurrence/tangent/core gates did not accept the Newton-Krylov candidate.'}
        write_json(a.out,out); print(json.dumps(out,indent=2)); return 3
    x0c=np.asarray(nk['corrected_initial_state'])
    mon=full_relative_monodromy_fd(x0c,D=D,period_hat=cand['period_hat'],dt_hat=a.dt,
        shift=cand['shift'],rotation=np.asarray(cand['rotation']),translation=np.asarray(cand['translation_over_D'])*D,
        eps_over_D=a.eps,fd_step_over_D=2e-5,max_n=24,force_python=a.force_python,skip_build=True)
    kr=kelvin_restricted_true_monodromy(mon,c,x0c)
    out={'status':'TRUE_RELATIVE_MONODROMY_CONSTRUCTED_AFTER_NEWTON_KRYLOV_RPO','alpha_opened':False,'candidate':cand,
         'monodromy':{'n':mon['n'],'dimension':mon['dimension'],'period_hat':mon['period_hat'],
            'base_relative_map_residual':mon['base_relative_map_residual'],'time_tangent_neutral_residual':mon['time_tangent_neutral_residual']},
         'kelvin_readout':{'true_floquet_phase_turns':kr['true_floquet_phase_turns'],'kelvin_subspace_leakage':kr['kelvin_subspace_leakage'],
            'eigenphases_turns':[float(x) for x in kr['kelvin_eigenphases_turns']]}}
    write_json(a.out,out); print(json.dumps(out,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
