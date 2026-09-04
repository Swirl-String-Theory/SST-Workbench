from __future__ import annotations
import numpy as np
from .backend import biot_savart, hamiltonian
from .constants import TAU_C
from .geometry import impulse

def _velocity(p,cfg,backend,allow_sycl_cpu):
    return biot_savart(p,p,cfg["gamma_m2_s"],cfg["core_m"],backend=backend,allow_sycl_cpu=allow_sycl_cpu)

def choose_dt(p,cfg,backend,allow_sycl_cpu):
    v,info=_velocity(p,cfg,backend,allow_sycl_cpu)
    ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    vmax=max(float(np.max(np.linalg.norm(v,axis=1))),1e-300)
    cfl_dt=float(cfg["cfl"])*float(np.min(ds))/vmax
    dt=float(cfg["dt_tau"])*TAU_C
    ratio=dt/max(cfl_dt,1e-300)
    if ratio>1.0:
        raise RuntimeError(f"fixed dt violates initial CFL: dt/cfl_dt={ratio:.3g}; lower dt_tau")
    return dt,{"vmax_initial_m_s":vmax,"min_ds_initial_m":float(np.min(ds)),"cfl_dt_s":cfl_dt,"dt_over_cfl":ratio,**info}

def integrate(p0,cfg,backend="auto",allow_sycl_cpu=False,record_geometry=False):
    p=np.ascontiguousarray(p0.copy());dt,backend_info=choose_dt(p,cfg,backend,allow_sycl_cpu)
    t_end=float(cfg["t_end_tau"])*TAU_C;steps=int(round(t_end/dt));steps=max(1,steps);dt=t_end/steps
    max_steps=int(cfg.get("max_steps",5000))
    if steps>max_steps: raise RuntimeError(f"required steps {steps} exceeds max_steps={max_steps}")
    stride=max(1,int(cfg.get("sample_stride",5)));times=[];H=[];I=[];frames=[]
    def record(step):
        h,_=hamiltonian(p,cfg["rho_kg_m3"],cfg["gamma_m2_s"],cfg["core_m"],backend=backend,allow_sycl_cpu=allow_sycl_cpu)
        times.append(step*dt);H.append(h);I.append(impulse(p,cfg["rho_kg_m3"],cfg["gamma_m2_s"]))
        if record_geometry:frames.append(p.copy())
    record(0);last_info=backend_info
    for step in range(1,steps+1):
        # Heun/RK2: same deterministic fixed clock for baseline and all perturbations.
        v1,last_info=_velocity(p,cfg,backend,allow_sycl_cpu);trial=p+dt*v1;v2,last_info=_velocity(trial,cfg,backend,allow_sycl_cpu)
        p=np.ascontiguousarray(p+0.5*dt*(v1+v2))
        if step%stride==0 or step==steps:record(step)
    return {"times":np.asarray(times),"H":np.asarray(H),"I":np.asarray(I),"frames":frames,"final":p,"dt_s":dt,"steps":steps,"backend_info":last_info}
