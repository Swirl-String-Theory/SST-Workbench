"""Independent fixed-time N, dt and regularization sensitivity screening.
This cannot promote a result to a long-time convergence-certified outcome.
"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np
from .model import torus_knot,RubanModel
from .metrics import shape_drift,length

def evolve(n,dt,t,b0,delta,Lambda,perturb=1e-4,seed=20261030):
    m=RubanModel(Lambda,delta)
    x=torus_knot(n,b0,perturbation=perturb,seed=seed)
    e0=m.energy(x)
    steps=math.ceil(t/dt)
    for i in range(steps):
        x=m.rk4(x,min(dt,t-i*dt))
    return x,abs(m.energy(x)/e0-1)

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--final-time',type=float,default=0.05)
    parser.add_argument('--dt',type=float,default=0.001)
    parser.add_argument('--n',type=int,nargs='+',default=[64,128,256])
    parser.add_argument('--delta',type=float,nargs='+',default=[0.05,0.025])
    parser.add_argument('--b0',type=float,default=0.154)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    if args.final_time<=0 or args.dt<=0:raise ValueError('positive final-time and dt required')
    Lambda=1.4+0.5*math.log(200)
    t0=time.perf_counter()
    records=[]
    xs={}
    for delta in args.delta:
        for n in args.n:
            for factor in [1,0.5]:
                dt=args.dt*factor
                x,energy=evolve(n,dt,args.final_time,args.b0,delta,Lambda)
                key=(delta,n,dt)
                xs[key]=x
                row=dict(delta=delta,n=n,dt=dt,final_time=args.final_time,
                    energy_drift=energy,length=length(x),
                    drift_from_analytic=shape_drift(x,torus_knot(n,args.b0),quick=False))
                records.append(row)
                print(f'delta={delta} N={n} dt={dt} Edrift={energy:.2e}',flush=True)
    diffs=[]
    for delta in args.delta:
        for n in args.n:
            dta=args.dt;dtb=dta*0.5
            diffs.append(dict(type='temporal',delta=delta,n=n,
               final_time=args.final_time,shape_difference=shape_drift(xs[(delta,n,dta)],xs[(delta,n,dtb)])))
        for low,high in zip(args.n[:-1],args.n[1:]):
            diffs.append(dict(type='spatial',delta=delta,n_pair=[low,high],
               final_time=args.final_time,shape_difference=shape_drift(xs[(delta,low,args.dt/2)],xs[(delta,high,args.dt/2)])))
    for n in args.n:
        if len(args.delta)>1:
            diffs.append(dict(type='regularization_sensitivity',n=n,delta_pair=args.delta[:2],
               final_time=args.final_time,shape_difference=shape_drift(xs[(args.delta[0],n,args.dt/2)],xs[(args.delta[1],n,args.dt/2)])))
    result=dict(status='DEVELOPMENT_NOT_LONG_TIME_CERTIFIED',
      note='dt and N compared at exactly the same t. delta comparison probes regularization-model sensitivity, not core-radius convergence.',
      elapsed_s=time.perf_counter()-t0,records=records,differences=diffs)
    out=args.output or Path(__file__).resolve().parents[1]/'Ruban_T23_Reproduction_v0.1.0-convergence.json'
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Wrote',out)
    return 0
if __name__=='__main__':raise SystemExit(main())
