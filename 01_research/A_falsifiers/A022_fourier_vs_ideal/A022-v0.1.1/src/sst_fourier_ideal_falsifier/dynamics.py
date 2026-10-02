from __future__ import annotations
import numpy as np
from .model import CurveSet
from .geometry import arclength,resample_curves,shape_velocity,align_cyclic,high_mode_fraction,deformation_basis
from .native import vortexlab_velocity,regularized_energy,min_nonlocal_segment_distance

CORE_DELTAS={"hollow":0.5,"rankine":0.25,"gp":0.615}

def velocity(cs:CurveSet,gammas,core,core_model='gp',c0=0.1395):
    delta=CORE_DELTAS.get(core_model,float(core_model) if isinstance(core_model,(int,float)) else 0.615)
    return vortexlab_velocity(cs.points,cs.offsets,np.asarray(gammas,float),core,delta,c0)

def cfl_dt(cs:CurveSet,gammas,core,core_model='gp',c0=0.1395,safety=0.35,dt_max=0.01):
    delta=CORE_DELTAS.get(core_model,0.615)
    max_omega=0.0
    gmax=max(float(np.max(np.abs(gammas))),1e-14)
    for c in cs.components():
        e=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)
        lm=float(np.min(e));lp=float(np.max(e))
        ds=max(lm,1e-10)
        arg=max(2*np.sqrt(max(lm,1e-14)*max(lp,1e-14))/(np.exp(delta)*core),1.0000001)
        Lam=abs(np.log(arg)+c0)
        nu=gmax*Lam/(4*np.pi)
        kmax=np.pi/ds
        max_omega=max(max_omega,nu*kmax*kmax)
    if max_omega<=1e-14:return dt_max
    return float(min(dt_max,safety/max_omega))

def rk4_step(cs,gammas,core,dt,n_per_component,core_model='gp',c0=0.1395):
    x=cs.points;o=cs.offsets
    def f(z):
        tmp=CurveSet(z,o.copy())
        return velocity(tmp,gammas,core,core_model,c0)
    k1=f(x);k2=f(x+0.5*dt*k1);k3=f(x+0.5*dt*k2);k4=f(x+dt*k3)
    y=x+dt*(k1+2*k2+2*k3+k4)/6.0
    return resample_curves(CurveSet(y,o.copy()),n_per_component)

def integrate_metrics(cs,gammas,cfg):
    core=float(cfg['core']);model=cfg.get('core_model','gp');c0=float(cfg.get('vortexlab_c0',0.1395))
    n=int(cfg['resample_n']);t_end=float(cfg['t_end']);records=int(cfg.get('records',25));
    x=cs;E0=regularized_energy(x.points,x.offsets,gammas,core);L0=sum(arclength(c) for c in x.components())
    v0=velocity(x,gammas,core,model,c0);w0,U0,Om0=shape_velocity(x,v0)
    vrms=float(np.sqrt(np.mean(np.sum(v0*v0,axis=1))));wrms=float(np.sqrt(np.mean(np.sum(w0*w0,axis=1))))
    rel0=wrms/max(vrms,1e-14)
    h0=float(np.mean([high_mode_fraction(c,cfg.get('high_mode_cut_fraction',0.35)) for c in x.components()]))
    min0=min_nonlocal_segment_distance(x.points,x.offsets,int(cfg.get('contact_adjacency',3)))
    target_times=np.linspace(0,t_end,records+1);next_rec=0;t=0.0;steps=0;rows=[];contact=False
    while True:
        if next_rec<len(target_times) and (t>=target_times[next_rec]-1e-12 or t>=t_end-1e-12):
            _,d,*_=align_cyclic(cs,x,2);E=regularized_energy(x.points,x.offsets,gammas,core);L=sum(arclength(c) for c in x.components())
            hm=float(np.mean([high_mode_fraction(c,cfg.get('high_mode_cut_fraction',0.35)) for c in x.components()]))
            gap=min_nonlocal_segment_distance(x.points,x.offsets,int(cfg.get('contact_adjacency',3)))
            rows.append({'time':float(t),'shape_distance':d,'high_mode_fraction':hm,'energy_rel':float((E-E0)/max(abs(E0),1e-14)),'length_rel':float((L-L0)/max(abs(L0),1e-14)),'gap_core':float(gap/core)})
            next_rec+=1
            if next_rec>=len(target_times) and t>=t_end-1e-12:break
        if t>=t_end-1e-12:break
        gap=min_nonlocal_segment_distance(x.points,x.offsets,int(cfg.get('contact_adjacency',3)))
        if gap < float(cfg.get('contact_core_multiple',2.2))*core:
            contact=True;break
        dt=cfl_dt(x,gammas,core,model,c0,float(cfg.get('cfl_safety',0.35)),float(cfg.get('dt_max',0.01)))
        dt=min(dt,t_end-t)
        if dt < float(cfg.get('dt_min',1e-7)):
            raise RuntimeError(f'CFL dt collapsed: {dt:g}')
        x=rk4_step(x,gammas,core,dt,n,model,c0);t+=dt;steps+=1
        if steps>int(cfg.get('max_steps',20000)):raise RuntimeError('max_steps exceeded')
    if not rows:
        raise RuntimeError('no integration records')
    times=np.array([r['time'] for r in rows]);dist=np.array([r['shape_distance'] for r in rows]);hm=np.array([r['high_mode_fraction'] for r in rows])
    if len(times)>=2 and times[-1]>0:
        auc=float(np.trapezoid(dist,times)/times[-1])
    else:auc=float(dist[-1])
    min_rpo_time=float(cfg.get('rpo_min_fraction',0.25))*max(t_end,1e-14)
    eligible=[r for r in rows if r['time']>=min_rpo_time]
    rpo=min((r['shape_distance'] for r in eligible),default=float('inf'))
    return {
      'initial_relative_equilibrium_residual':rel0,
      'initial_shape_speed_rms':wrms,
      'initial_total_speed_rms':vrms,
      'rigid_U':U0.tolist(),'rigid_Omega':Om0.tolist(),
      'initial_high_mode_fraction':h0,
      'peak_high_mode_fraction':float(np.max(hm)),
      'high_mode_growth':float(np.max(hm)-h0),
      'shape_auc':auc,'final_shape_distance':float(dist[-1]),'rpo_residual':float(rpo),
      'max_abs_energy_drift':float(max(abs(r['energy_rel']) for r in rows)),
      'max_abs_length_drift':float(max(abs(r['length_rel']) for r in rows)),
      'min_gap_core':float(min(r['gap_core'] for r in rows)),
      'initial_gap_core':float(min0/core),'contact_stop':contact,'contact_survival_deficit':float(max(t_end-t,0.0)/max(t_end,1e-14)),'steps':steps,'actual_t_end':float(t),'history':rows
    }

def restoring_modes(cs,gammas,cfg):
    B,labels=deformation_basis(cs,int(cfg.get('mode_m_min',2)),int(cfg.get('mode_m_max',4)),int(cfg.get('modal_dims',6)))
    if B.shape[1]==0:return {'n_modes':0,'restoring_fraction':float('nan'),'max_real_growth':float('nan'),'mode_labels':[]}
    eps=float(cfg.get('mode_eps',0.008));core=float(cfg['core']);model=cfg.get('core_model','gp');c0=float(cfg.get('vortexlab_c0',0.1395))
    def modal_rate(c):
        v=velocity(c,gammas,core,model,c0);w,*_=shape_velocity(c,v);return B.T@w.reshape(-1)
    d=B.shape[1];J=np.zeros((d,d));diag=[]
    for j in range(d):
        q=np.zeros(d);q[j]=eps;cp=CurveSet(cs.points+(B@q).reshape(cs.points.shape),cs.offsets.copy())
        q[j]=-eps;cm=CurveSet(cs.points+(B@q).reshape(cs.points.shape),cs.offsets.copy())
        fp=modal_rate(cp);fm=modal_rate(cm);J[:,j]=(fp-fm)/(2*eps)
        diag.append(float(J[j,j]))
    eig=np.linalg.eigvals(J);frac=float(np.mean(np.asarray(diag)<0))
    return {'n_modes':d,'restoring_fraction':frac,'restoring_diagonal':diag,'max_real_growth':float(np.max(eig.real)),'eigenvalues':[[float(z.real),float(z.imag)] for z in eig],'mode_labels':labels}
