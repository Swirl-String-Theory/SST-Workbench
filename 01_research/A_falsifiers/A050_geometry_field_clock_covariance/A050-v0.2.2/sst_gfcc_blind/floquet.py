import numpy as np
from .geometry import resample_closed
from .filament import evolve_curve
from .modes import kabsch_align, helical_basis


def shape_residual(points, reference):
    p=resample_closed(np.asarray(points,float),len(reference))
    q=np.asarray(reference,float)
    p=kabsch_align(p,q)
    d=p-q
    scale=np.sqrt(np.mean(np.sum((q-q.mean(axis=0))**2,axis=1)))
    return float(np.sqrt(np.mean(np.sum(d*d,axis=1)))/max(scale,1e-15))


def detect_return(frames, cfg):
    ref=frames[0]
    r=np.asarray([shape_residual(p,ref) for p in frames],float)
    dep=None
    for i in range(1,len(r)):
        if r[i]>=float(cfg['departure_residual_min']):
            dep=i; break
    if dep is None:
        return {'status':'INDETERMINATE_NO_DEPARTURE','return_step':None,'return_residual':None,'residual_series':r.tolist()}
    lo=max(dep+1,int(cfg['min_return_steps']))
    hi=min(len(r)-1,int(cfg.get('max_return_steps',len(r)-1)))
    cand=[]
    for i in range(lo,hi):
        if r[i]<=r[i-1] and r[i]<=r[i+1] and r[i]<=float(cfg['return_residual_max']):
            cand.append(i)
    if not cand:
        return {'status':'INDETERMINATE_NO_RECURRENCE','return_step':None,'return_residual':None,'residual_series':r.tolist()}
    i=min(cand,key=lambda j:r[j])
    return {'status':'RETURN_CANDIDATE','return_step':int(i),'return_residual':float(r[i]),'residual_series':r.tolist()}


def _monodromy_once(p0, base_final, basis, core, dt, steps, reparam, chunk, eps):
    cols=[]
    for v in basis:
        q0=np.asarray(p0,float)+float(eps)*v
        q0-=q0.mean(axis=0,keepdims=True)
        q0=resample_closed(q0,len(q0))
        qf=evolve_curve(q0,core,dt,steps,reparam,chunk)[-1]
        qf=kabsch_align(qf,base_final)
        d=qf-base_final
        col=[]
        for w in basis:
            col.append(float(np.sum(w*d)/max(float(eps)*np.sum(w*w),1e-30)))
        cols.append(col)
    return np.asarray(cols,float).T


def floquet_gate(p0, core, dt, search_steps, reparam, chunk, cfg):
    frames=evolve_curve(p0,core,dt,int(search_steps),reparam,chunk)
    ret=detect_return(frames,cfg)
    if ret['return_step'] is None:
        return {**ret,'resolved':False,'classification':None,'spectral_radius':None,'multipliers':[],'fd_relative_delta':None}
    step=int(ret['return_step'])
    base_final=frames[step]
    labels,basis=helical_basis(p0,cfg['basis_modes'])
    if len(basis)<2:
        return {**ret,'status':'INDETERMINATE_BASIS','resolved':False,'classification':None,'spectral_radius':None,'multipliers':[],'fd_relative_delta':None}
    e1=float(cfg['perturbation_size']); e2=e1*float(cfg['perturbation_ratio'])
    m1=_monodromy_once(p0,base_final,basis,core,dt,step,reparam,chunk,e1)
    m2=_monodromy_once(p0,base_final,basis,core,dt,step,reparam,chunk,e2)
    ev1=np.linalg.eigvals(m1); ev2=np.linalg.eigvals(m2)
    rho1=float(np.max(np.abs(ev1))); rho2=float(np.max(np.abs(ev2)))
    fd=abs(rho1-rho2)/max(abs(rho2),1e-12)
    if not np.isfinite(fd) or fd>float(cfg['fd_relative_delta_max']):
        return {**ret,'status':'INDETERMINATE_FD_CONVERGENCE','resolved':False,'classification':None,'spectral_radius':rho2,'multipliers':[[float(z.real),float(z.imag)] for z in ev2],'fd_relative_delta':float(fd),'basis_labels':labels,'monodromy':m2.tolist()}
    tol=float(cfg['marginal_tolerance'])
    if rho2<1.0-tol: cls='CONTRACTING'
    elif rho2>1.0+tol: cls='EXPANDING'
    else: cls='MARGINAL'
    return {**ret,'status':'FLOQUET_RESOLVED','resolved':True,'classification':cls,'spectral_radius':rho2,'multipliers':[[float(z.real),float(z.imag)] for z in ev2],'fd_relative_delta':float(fd),'basis_labels':labels,'monodromy':m2.tolist()}
