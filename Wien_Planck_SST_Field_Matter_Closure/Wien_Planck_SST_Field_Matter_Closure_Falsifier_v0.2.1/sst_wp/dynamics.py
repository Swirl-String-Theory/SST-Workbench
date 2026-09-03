from __future__ import annotations
import math, numpy as np
from .kernels import velocity
from .geometry import spacing_metrics,reparameterize

def rhs(X,offs,gamma,core,require_native=False):
    return velocity(X,offs,gamma,core,require_native)

def rk4(X,dt,offs,gamma,core,require_native=False):
    k1=rhs(X,offs,gamma,core,require_native)
    k2=rhs(X+.5*dt*k1,offs,gamma,core,require_native)
    k3=rhs(X+.5*dt*k2,offs,gamma,core,require_native)
    k4=rhs(X+dt*k3,offs,gamma,core,require_native)
    return X+(dt/6)*(k1+2*k2+2*k3+k4)

def evolve(X0,offs,cfg,sample_count=256,cfl_divisor=1.0):
    X=np.asarray(X0,float).copy(); gamma=float(cfg['gamma_dimensionless']);core=float(cfg['core_fraction']);T=float(cfg['t_final']);
    cfl=float(cfg['stability_cfl'])/float(cfl_divisor);req=bool(cfg.get('require_native',False));maxsteps=int(cfg.get('max_substeps',200000)); reps=int(cfg.get('reparameterization_events',8))
    sample_times=np.linspace(0,T,max(16,int(sample_count)))
    rep_times=np.linspace(0,T,reps+2)[1:-1] if reps>0 else np.array([])
    event_times=np.unique(np.concatenate([sample_times,rep_times,[T]]))
    samples=[];times=[];diags=[];nsteps=0;dtmin=float('inf');dtmax=0.0;t=0.0;si=0
    # exact t=0 sample
    samples.append(X.copy());times.append(0.0)
    for target in event_times[1:]:
        while t < target-1e-15*max(1.0,T):
            sm=spacing_metrics(X,offs)
            dt_target=4*math.pi*cfl*sm['ds_min']**2/max(abs(gamma),1e-300)
            dt=min(dt_target,target-t)
            if not np.isfinite(dt) or dt<=0: raise RuntimeError('invalid adaptive timestep')
            X=rk4(X,dt,offs,gamma,core,req);t+=dt;nsteps+=1;dtmin=min(dtmin,dt);dtmax=max(dtmax,dt)
            if nsteps>maxsteps: raise RuntimeError(f'max_substeps exceeded: >{maxsteps}')
        if len(rep_times) and np.min(np.abs(rep_times-target)) < 1e-12*max(1,T):
            X,o2=reparameterize(X,offs)
            if not np.array_equal(o2,offs): raise RuntimeError('component offsets changed during reparameterization')
        # sample only at scheduled sample times
        if np.min(np.abs(sample_times-target)) < 1e-12*max(1,T):
            samples.append(X.copy());times.append(float(target));diags.append(spacing_metrics(X,offs))
    sm0=spacing_metrics(np.asarray(X0,float),offs);smf=spacing_metrics(X,offs)
    return np.array(times),np.array(samples),{'dt_min':dtmin,'dt_max':dtmax,'n_steps':nsteps,'initial_mesh':sm0,'final_mesh':smf,'sample_mesh_max_cv':max([d['ds_cv'] for d in diags] or [sm0['ds_cv']]),'cfl_divisor':float(cfl_divisor),'fixed_t_final':T}
