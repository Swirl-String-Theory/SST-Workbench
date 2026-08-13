#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,numpy as np
from sst_counterpulley.core import DEFAULT_DATA,prepare_centerline,write_json
from sst_counterpulley.orbit import search_relative_periodic_orbit
from sst_counterpulley.monodromy import full_relative_monodromy_fd,kelvin_restricted_true_monodromy

def main()->int:
    ap=argparse.ArgumentParser(description='Construct true D(g^-1 o phi_T) only after an accepted RPO search.')
    ap.add_argument('--data',default=str(DEFAULT_DATA)); ap.add_argument('--n',type=int,default=16)
    ap.add_argument('--offset',type=float,default=.5); ap.add_argument('--eps',type=float,default=.05)
    ap.add_argument('--phase',type=float,default=0.0); ap.add_argument('--dt',type=float,default=.003)
    ap.add_argument('--max-time',type=float,default=2.0); ap.add_argument('--out',default='true_floquet.json')
    ap.add_argument('--force-python',action='store_true')
    a=ap.parse_args(); c,m=prepare_centerline(data_path=a.data,n=a.n); D=float(m['D_metadata'])
    r=search_relative_periodic_orbit(c,D=D,offset_over_D=a.offset,eps_over_D=a.eps,channel_phase=a.phase,
        dt_hat=a.dt,max_time_hat=a.max_time,min_time_hat=.2,snapshot_stride=max(1,int(.03/a.dt)),
        recurrence_tol_over_D=.05,force_python=a.force_python,skip_build=True)
    cand=r['candidate']
    if not cand['accepted']:
        out={'status':'BLOCKED_NO_ACCEPTED_RPO','alpha_opened':False,'candidate':cand,
             'termination_reason':r.get('termination_reason'),'termination_time_hat':r.get('termination_time_hat')}
        write_json(a.out,out); print(json.dumps(out,indent=2)); return 3
    mon=full_relative_monodromy_fd(r['initial_state'],D=D,period_hat=cand['period_hat'],dt_hat=a.dt,
        shift=cand['shift'],rotation=np.asarray(cand['rotation']),translation=np.asarray(cand['translation_over_D'])*D,
        eps_over_D=a.eps,fd_step_over_D=2e-5,max_n=24,force_python=a.force_python,skip_build=True)
    kr=kelvin_restricted_true_monodromy(mon,c,r['initial_state'])
    out={'status':'TRUE_RELATIVE_MONODROMY_CONSTRUCTED','alpha_opened':False,'candidate':cand,
         'monodromy':{'n':mon['n'],'dimension':mon['dimension'],'period_hat':mon['period_hat'],
            'base_relative_map_residual':mon['base_relative_map_residual'],
            'time_tangent_neutral_residual':mon['time_tangent_neutral_residual']},
         'kelvin_readout':{'true_floquet_phase_turns':kr['true_floquet_phase_turns'],
            'kelvin_subspace_leakage':kr['kelvin_subspace_leakage'],
            'eigenphases_turns':[float(x) for x in kr['kelvin_eigenphases_turns']]}}
    write_json(a.out,out); print(json.dumps(out,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
