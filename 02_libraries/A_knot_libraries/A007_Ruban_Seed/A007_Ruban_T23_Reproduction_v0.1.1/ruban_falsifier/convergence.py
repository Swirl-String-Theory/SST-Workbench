"""Fixed-final-time convergence screen; explicitly not a framework certification."""
from __future__ import annotations
import argparse,json,math,time
from pathlib import Path
import numpy as np
from .model import torus_knot,RubanModel
from .metrics import shape_drift,length,is_regular
from .runner import local_induction_dt_cap,ROOT,PREFIX,VERSION

def evolve(n,dt,t,b0,delta,Lambda,perturb=1e-4,seed=20261030):
    m=RubanModel(Lambda,delta);x=torus_knot(n,b0,perturbation=perturb,seed=seed)
    e0=m.energy(x);ti=0.;cap_min=math.inf;steps=0;acc_min=math.inf
    while ti<t-1e-12:
        cap=local_induction_dt_cap(x,m.lambda_tilde)
        if cap<=0 or not is_regular(x):raise RuntimeError('invalid geometry / step cap')
        cap_min=min(cap_min,cap);h=min(dt,cap,t-ti)
        if h<1e-10:raise RuntimeError('step underflow')
        x=m.rk4(x,h);ti+=h;steps+=1;acc_min=min(acc_min,h)
        if steps>1000000:raise RuntimeError('max steps exceeded')
    return x,abs(m.energy(x)/e0-1),{'min_stability_cap':cap_min,'min_accepted_step':acc_min,'steps':steps,'requested_dt':dt}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--final-time',type=float,default=.05)
    p.add_argument('--dt',type=float,default=.001);p.add_argument('--n',type=int,nargs='+',default=[64,128,256]);p.add_argument('--delta',type=float,nargs='+',default=[.05,.025]);p.add_argument('--b0',type=float,default=.154);p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    if a.final_time<=0 or a.dt<=0:raise ValueError('t and dt must be positive')
    Lambda=1.4+.5*math.log(200);start=time.perf_counter();xs={};records=[];diffs=[]
    for delta in a.delta:
        for n in a.n:
            # step=dt*(minN/n)^2 keeps the explicit local-induction cap comparable
            for factor in (1,.5):
                dt=a.dt*(min(a.n)/n)**2*factor
                x,energy,steps=evolve(n,dt,a.final_time,a.b0,delta,Lambda)
                xs[(delta,n,factor)]=x
                records.append(dict(delta=delta,n=n,dt=dt,final_time=a.final_time,energy_drift=energy,length=length(x),drift_from_analytic=shape_drift(x,torus_knot(n,a.b0)),**steps))
                print(f'delta={delta} n={n} dt={dt:.3g} energy={energy:.3g}',flush=True)
    for delta in a.delta:
        for n in a.n:
            diffs.append(dict(type='temporal',delta=delta,n=n,shape_difference=shape_drift(xs[(delta,n,1)],xs[(delta,n,.5)]),final_time=a.final_time))
        for low,high in zip(a.n[:-1],a.n[1:]):
            diffs.append(dict(type='spatial',delta=delta,n_pair=[low,high],shape_difference=shape_drift(xs[(delta,low,.5)],xs[(delta,high,.5)]),final_time=a.final_time))
    if len(a.delta)>1:
        for n in a.n:
            diffs.append(dict(type='regularization_sensitivity',n=n,delta_pair=a.delta[:2],shape_difference=shape_drift(xs[(a.delta[0],n,.5)],xs[(a.delta[1],n,.5)]),final_time=a.final_time))
    report=dict(status='DEVELOPMENT_NOT_LONG_TIME_CERTIFIED',notes=['fixed physical final time','requested dt scales N^-2','actual stability caps recorded','delta sensitivity is not finite-core convergence','no framework runtime certification'],elapsed_s=time.perf_counter()-start,records=records,differences=diffs)
    dest=a.output or ROOT/(PREFIX+'_'+VERSION+'-convergence.json');dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Wrote',dest);return 0
if __name__=='__main__':raise SystemExit(main())
