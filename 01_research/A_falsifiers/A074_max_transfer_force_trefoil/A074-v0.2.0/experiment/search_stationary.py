"""Predeclared topology-constrained candidate discovery and independent grid holdouts.

Random+local search aims at relative equilibrium in a *finite-width 3D Euler*
initial condition, not at geometrical ropelength or the gravitational target.
No stability claim follows even if a low residual is obtained.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from .euler3d import Euler3D
from .model import sample_seed,load_seed,relative_equilibrium_residual,min_nonlocal_distance,length

ROOT=Path(__file__).resolve().parents[1]

def shape(x,params):
    sx,sy,sz,bz,bx=params
    y=x.copy()
    y[:,0]*=sx;y[:,1]*=sy;y[:,2]*=sz
    t=np.arange(len(y))*2*np.pi/len(y)
    y[:,2]+=bz*np.cos(2*t)
    y[:,0]+=bx*np.sin(3*t)
    y-=y.mean(axis=0)
    y/=np.max(np.hypot(y[:,0],y[:,1]))
    return y

def evaluate(m,base,params,core):
    xx=shape(base,params)
    gap=min_nonlocal_distance(xx,max(4,len(xx)//12))
    if gap<2*core*1.02:return float('inf'),gap,xx
    uhat=m.omega_initial(xx,core)
    velocity=m.sample(m.ifft(uhat),xx)
    residual=relative_equilibrium_residual(xx,velocity)['normal_residual']
    return float(residual),float(gap),xx

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--trials',type=int,default=150)
    ap.add_argument('--output',default=None)
    ar=ap.parse_args(argv)
    cfg=json.loads((ROOT/'configs/euler_study.json').read_text())
    seed=load_seed(ROOT/'seeds/trefoil_ideal_3_1_1.json')
    base=sample_seed(seed,int(cfg['material_marker_N']))
    out=Path(ar.output or ROOT/'Trefoil_Max_Transfer_Force_v0.2.0-outputs');out.mkdir(exist_ok=True,parents=True)
    rng=np.random.default_rng(20261026)
    bounds=np.array([[.83,1.17],[.83,1.17],[.7,1.30],[-.10,.10],[-.10,.10]])
    steps=np.array([.06,.06,.12,.035,.035])
    model=Euler3D(32,cfg['box_m'])
    trials=[];best=(float('inf'),None,None)
    core_choices=cfg['candidate_core_radii_m']
    for core in core_choices:
        for run in range(ar.trials):
            params=np.array([1,1,1,0,0]) if run==0 else rng.uniform(bounds[:,0],bounds[:,1])
            res,gap,_=evaluate(model,base,params,core)
            trials.append({'core_m':core,'kind':'discovery','score':res,'gap_m':gap,'params':params.tolist()})
            if res<best[0]:best=(res,core,params.copy())
    bestscore,core,p=best
    if p is None:raise RuntimeError('no admissible candidates')
    for _ in range(9):
        improvement=False
        for k in range(5):
            for direction in (-1,1):
                q=p.copy();q[k]=np.clip(q[k]+direction*steps[k],*bounds[k])
                res,gap,_=evaluate(model,base,q,core)
                trials.append({'core_m':core,'kind':'local_refine','score':res,'gap_m':gap,'params':q.tolist()})
                if res<bestscore:
                    bestscore,p=res,q
                    improvement=True
        if not improvement:steps*=.5
    # True held-out grids. They do not influence discovery.
    candidate=shape(base,p)
    holdouts=[]
    for n in [32,48,64]:
        v=Euler3D(n,cfg['box_m'])
        residual,gap,_=evaluate(v,base,p,core)
        holdouts.append({'n':n,'normal_relative_residual':residual,'core_cells':core/v.dx,
                         'gap_over_2core':gap/(2*core), 'length_m':length(candidate)})
    summary={'schema':'SST-REL-EQUILIBRIUM-SEARCH-1','status':'DEVELOPMENT_DISCOVERY_NOT_STABILITY',
             'discovery_grid_n':32,'random_seed':20261026,'initial_random_trials_per_core':ar.trials,
             'selected_discovery_residual':bestscore,'chosen_core_m':core,'parameter_vector':p.tolist(),
             'parameter_bounds':bounds.tolist(),'independent_grids':holdouts,
             'n_evaluations':len(trials),'source':'gilbert 3:1:1','objective':'normal-plane velocity relative-equilibrium residual',
             'not_certified':'Finite-width Euler, but no stationary 3D Euler-state solve, Floquet test or long-time stability'}
    (out/'EQUILIBRIUM_SEARCH.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (out/'EQUILIBRIUM_SEARCH_TRIALS.json').write_text(json.dumps(trials,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return summary
if __name__=='__main__':main()
