#!/usr/bin/env python3
"""Chunked resumable version of rolling_clock; deterministic fixed dt; no backend edits."""
import argparse, time, json
from pathlib import Path
import numpy as np
from rolling_clock import sample_source, A006, metrics, rk4, ROOT
p=argparse.ArgumentParser()
p.add_argument('--chunk',type=int,required=True);p.add_argument('--steps',type=int,default=3500)
p.add_argument('--dt',type=float,default=1.5e-5);p.add_argument('--N',type=int,default=288)
p.add_argument('--a',type=float,default=.002);p.add_argument('--prefix',default='main')
a=p.parse_args();out=ROOT/'results';out.mkdir(exist_ok=True)
if a.chunk==0:X=sample_source(A006,a.N)
else:X=np.load(out/f'{a.prefix}_chunk{a.chunk-1}.npz')['Xend'].copy()
start=a.chunk*a.steps* a.dt
rows=[];Xs=[];t0=time.monotonic()
for k in range(a.steps+1):
 if k%60==0 or k==a.steps:
  r=metrics(X,1,a.a);r['tau']=start+k*a.dt;rows.append(r);Xs.append(X.copy())
 if k<a.steps:X=rk4(X,a.dt,1,a.a)
 if not np.isfinite(X).all() or np.max(np.abs(X))>100:raise RuntimeError('geometry failed')
np.savez_compressed(out/f'{a.prefix}_chunk{a.chunk}.npz', Xend=X, tau=np.array([r['tau'] for r in rows]), Xs=np.array(Xs), metrics_json=json.dumps(rows))
print('CHUNK',a.chunk,'start',round(start,7),'end',round(start+a.steps*a.dt,7),'wall',round(time.monotonic()-t0,2),'coh',round(min(r['coherence'] for r in rows),4),flush=True)
