from __future__ import annotations
import numpy as np
from .model import CurveSet
from .geometry import arclength,resample_closed,shape_velocity,align_cyclic,high_mode_fraction,deformation_basis
from .native import vortex_velocity,regularized_energy,min_nonlocal_segment_distance
from .pressure import pressure_poisson_metrics

CORE_DELTAS={'hollow':0.5,'rankine':0.25,'gp':0.615}

def combine_resample(cs,n_carrier,n_thread,nc):
    comps=[]
    for i,c in enumerate(cs.components()): comps.append(resample_closed(c,n_carrier if i<nc else n_thread))
    return CurveSet.from_components(comps)

def carrier_view(cs,nc): return CurveSet.from_components(cs.components()[:nc])

def velocity(cs,gammas,core,model='gp',c0=0.1395): return vortex_velocity(cs.points,cs.offsets,np.asarray(gammas,float),core,CORE_DELTAS.get(model,0.615),c0)

def cfl_dt(cs,gammas,core,model='gp',c0=.1395,safety=.32,dt_max=.01):
    gmax=max(float(np.max(np.abs(gammas))),1e-14);om=0.
    for c in cs.components():
        e=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1);lm=max(float(np.min(e)),1e-10);lp=max(float(np.max(e)),1e-10);arg=max(2*np.sqrt(lm*lp)/(np.exp(CORE_DELTAS.get(model,.615))*core),1.0000001);nu=gmax*abs(np.log(arg)+c0)/(4*np.pi);om=max(om,nu*(np.pi/lm)**2)
    return float(min(dt_max,safety/max(om,1e-14)))

def rk4(cs,gammas,core,dt,nc,n_carrier,n_thread,model='gp',c0=.1395):
    x=cs.points;o=cs.offsets.copy()
    def f(z):return velocity(CurveSet(z,o),gammas,core,model,c0)
    k1=f(x);k2=f(x+.5*dt*k1);k3=f(x+.5*dt*k2);k4=f(x+dt*k3);y=x+dt*(k1+2*k2+2*k3+k4)/6
    return combine_resample(CurveSet(y,o),n_carrier,n_thread,nc)

def _carrier_velocity(cs,nc,v):
    cv=carrier_view(cs,nc);return cv,v[:cv.points.shape[0]]

def integrate_metrics(cs,gammas,nc,cfg):
    core=float(cfg['core']);model=cfg.get('core_model','gp');c0=float(cfg.get('vortexlab_c0',.1395));nC=int(cfg['carrier_n']);nT=int(cfg['thread_n']);t_end=float(cfg['tau_end'])/max(abs(float(gammas[0])),1e-14);records=int(cfg.get('records',16))
    x=cs;ref=carrier_view(cs,nc);E0=regularized_energy(x.points,x.offsets,gammas,core);L0=sum(arclength(c) for c in ref.components());v0=velocity(x,gammas,core,model,c0);_,vc0=_carrier_velocity(x,nc,v0);w0,U,Om=shape_velocity(ref,vc0);vrms=float(np.sqrt(np.mean(np.sum(vc0*vc0,axis=1))));wrms=float(np.sqrt(np.mean(np.sum(w0*w0,axis=1))));rel0=wrms/max(vrms,1e-14);h0=float(np.mean([high_mode_fraction(c,cfg.get('high_mode_cut_fraction',.35)) for c in ref.components()]));gap0=min_nonlocal_segment_distance(x.points,x.offsets,int(cfg.get('contact_adjacency',3)))/core
    target=np.linspace(0,t_end,records+1);ri=0;t=0.;steps=0;rows=[];contact=False
    while True:
        if ri<len(target) and (t>=target[ri]-1e-12 or t>=t_end-1e-12):
            cv=carrier_view(x,nc);_,d,*_=align_cyclic(ref,cv,2);E=regularized_energy(x.points,x.offsets,gammas,core);L=sum(arclength(c) for c in cv.components());hm=float(np.mean([high_mode_fraction(c,cfg.get('high_mode_cut_fraction',.35)) for c in cv.components()]));gap=min_nonlocal_segment_distance(x.points,x.offsets,int(cfg.get('contact_adjacency',3)))/core
            rows.append({'tau':float(t*abs(gammas[0])),'shape_distance':d,'high_mode_fraction':hm,'energy_rel':float((E-E0)/max(abs(E0),1e-14)),'carrier_length_rel':float((L-L0)/max(abs(L0),1e-14)),'gap_core':float(gap)});ri+=1
            if ri>=len(target) and t>=t_end-1e-12:break
        if t>=t_end-1e-12:break
        gap=min_nonlocal_segment_distance(x.points,x.offsets,int(cfg.get('contact_adjacency',3)))
        if gap<float(cfg.get('contact_core_multiple',2.05))*core:contact=True;break
        dt=min(cfl_dt(x,gammas,core,model,c0,float(cfg.get('cfl_safety',.32)),float(cfg.get('dt_max',.008))),t_end-t)
        if dt<float(cfg.get('dt_min',1e-7)):raise RuntimeError('CFL dt collapsed')
        x=rk4(x,gammas,core,dt,nc,nC,nT,model,c0);t+=dt;steps+=1
        if steps>int(cfg.get('max_steps',12000)):raise RuntimeError('max_steps exceeded')
    times=np.array([r['tau'] for r in rows]);dist=np.array([r['shape_distance'] for r in rows]);hm=np.array([r['high_mode_fraction'] for r in rows]);auc=float(np.trapezoid(dist,times)/times[-1]) if len(times)>1 and times[-1]>0 else float(dist[-1]);eligible=[r for r in rows if r['tau']>=float(cfg.get('rpo_min_fraction',.25))*float(cfg['tau_end'])];rpo=min((r['shape_distance'] for r in eligible),default=1e12)
    return {'initial_relative_equilibrium_residual':rel0,'initial_shape_speed_rms':wrms,'initial_total_speed_rms':vrms,'rigid_U':U.tolist(),'rigid_Omega':Om.tolist(),'initial_high_mode_fraction':h0,'peak_high_mode_fraction':float(np.max(hm)),'shape_auc':auc,'final_shape_distance':float(dist[-1]),'rpo_residual':float(rpo),'max_abs_energy_drift':float(max(abs(r['energy_rel']) for r in rows)),'max_abs_carrier_length_drift':float(max(abs(r['carrier_length_rel']) for r in rows)),'initial_gap_core':float(gap0),'min_gap_core':float(min(r['gap_core'] for r in rows)),'contact_stop':contact,'contact_survival_deficit':float(max(t_end-t,0.)/max(t_end,1e-14)),'steps':steps,'actual_tau_end':float(t*abs(gammas[0])),'history':rows}

def restoring_modes(cs,gammas,nc,cfg):
    carrier=carrier_view(cs,nc);B,labels=deformation_basis(carrier,int(cfg.get('mode_m_min',2)),int(cfg.get('mode_m_max',4)),int(cfg.get('modal_dims',6)))
    if B.shape[1]==0:return {'n_modes':0,'restoring_fraction':float('nan'),'max_real_growth':float('nan'),'eigenvalues':[]}
    eps=float(cfg.get('mode_eps',.006));core=float(cfg['core']);base=cs.points.copy();cn=len(carrier.points)
    def rate(delta):
        z=base.copy();z[:cn]+=delta.reshape((cn,3));tmp=CurveSet(z,cs.offsets.copy());v=velocity(tmp,gammas,core,cfg.get('core_model','gp'),float(cfg.get('vortexlab_c0',.1395)))[:cn];w,*_=shape_velocity(CurveSet(z[:cn],carrier.offsets.copy()),v);return B.T@w.reshape(-1)
    d=B.shape[1];J=np.zeros((d,d));diag=[]
    for j in range(d):
        delta=(eps*B[:,j]).reshape((cn,3));J[:,j]=(rate(delta)-rate(-delta))/(2*eps);diag.append(float(J[j,j]))
    eig=np.linalg.eigvals(J);return {'n_modes':d,'restoring_fraction':float(np.mean(np.asarray(diag)<0)),'restoring_diagonal':diag,'max_real_growth':float(np.max(eig.real)),'eigenvalues':[[float(z.real),float(z.imag)] for z in eig],'mode_labels':labels}

def analyze(cs,gammas,nc,cfg):
    dyn=integrate_metrics(cs,gammas,nc,cfg);rest=restoring_modes(cs,gammas,nc,cfg);p=pressure_poisson_metrics(cs.points,cs.offsets,gammas,float(cfg['core']),int(cfg.get('pressure_grid_n',12)),float(cfg.get('pressure_box_half',2.4))) if cfg.get('pressure_enabled',True) else {}
    return {**{k:v for k,v in dyn.items() if k!='history'},'history':dyn['history'],'restoring_fraction':rest['restoring_fraction'],'max_real_growth':rest['max_real_growth'],'max_real_growth_positive':max(rest['max_real_growth'],0.0),'restoring':rest,**p}
