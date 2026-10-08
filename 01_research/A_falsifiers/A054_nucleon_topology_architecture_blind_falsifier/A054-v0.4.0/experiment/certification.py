from __future__ import annotations
import numpy as np, math
from .physics import flatten, split
from .mechanisms import injected_velocity, make_context
from .modes import build_mode_basis, family_indices

def fit_rigid(comps,vels):
    x=flatten(comps); u=flatten(vels); xc=x.mean(0); r=x-xc; A=np.zeros((3*len(x),6)); b=u.reshape(-1)
    for i,(rx,ry,rz) in enumerate(r):
        M=np.array([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]],float); A[3*i:3*i+3,:3]=np.eye(3); A[3*i:3*i+3,3:]=M
    q,*_=np.linalg.lstsq(A,b,rcond=None); return q,u-(A@q).reshape(-1,3)

def perturb(comps,field,amp):
    sizes=[len(c) for c in comps]; return split(flatten(comps)+float(amp)*np.asarray(field,float),sizes)

def rhs(Y,sizes,gammas,core,ctx):
    cs=split(Y,sizes); return flatten(injected_velocity(cs,gammas,core,ctx))

def rk4(comps,gammas,core,ctx,dt,steps):
    sizes=[len(c) for c in comps]; Y=flatten(comps).copy()
    for _ in range(int(steps)):
        k1=rhs(Y,sizes,gammas,core,ctx); k2=rhs(Y+0.5*dt*k1,sizes,gammas,core,ctx); k3=rhs(Y+0.5*dt*k2,sizes,gammas,core,ctx); k4=rhs(Y+dt*k3,sizes,gammas,core,ctx)
        Y += dt*(k1+2*k2+2*k3+k4)/6
        if not np.isfinite(Y).all(): raise FloatingPointError('non-finite state')
    return split(Y,sizes)

def shape_distance(ref,cur):
    X=flatten(ref); Y=flatten(cur); Xc=X-X.mean(0); Yc=Y-Y.mean(0); U,_,Vt=np.linalg.svd(Yc.T@Xc); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    Ya=Yc@R+X.mean(0); rg=np.sqrt(np.mean(np.sum(Xc*Xc,axis=1))); return float(np.sqrt(np.mean(np.sum((Ya-X)**2,axis=1)))/max(rg,1e-15))

def min_intercomponent(cs):
    best=np.inf
    for i in range(len(cs)):
        for j in range(i+1,len(cs)):
            best=min(best,float(np.min(np.linalg.norm(cs[i][:,None,:]-cs[j][None,:,:],axis=2))))
    return best

def gauss_link(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); aq=np.roll(a,-1,axis=0); bq=np.roll(b,-1,axis=0); da=aq-a; db=bq-b; am=.5*(a+aq); bm=.5*(b+bq); total=0.0
    for i in range(len(a)):
        r=am[i][None,:]-bm; den=np.linalg.norm(r,axis=1)**3; total += np.sum(np.einsum('ij,ij->i',np.cross(da[i][None,:],db),r)/np.maximum(den,1e-15))
    return total/(4*np.pi)

def topology_drift(ref,cur):
    vals=[]
    for i in range(len(ref)):
        for j in range(i+1,len(ref)):
            vals.append(abs(gauss_link(ref[i],ref[j])-gauss_link(cur[i],cur[j])))
    return max(vals,default=0.0)

def reduced_rhs(comps,gammas,core,ctx,mi):
    vel=injected_velocity(comps,gammas,core,ctx); _,urel=fit_rigid(comps,vel); return np.array([np.sum(b*urel) for b in mi['basis']],float)

def projected_jacobian(comps,gammas,core,ctx,mi,eps):
    B=mi['basis']; J=np.zeros((len(B),len(B)))
    for j in range(len(B)):
        J[:,j]=(reduced_rhs(perturb(comps,B[j],eps),gammas,core,ctx,mi)-reduced_rhs(perturb(comps,B[j],-eps),gammas,core,ctx,mi))/(2*eps)
    return J

def kelvin_growth(J,mi):
    ix=family_indices(mi,'kelvin')
    if not ix: return float('inf')
    vals=np.linalg.eigvals(J[np.ix_(ix,ix)]); scale=max(float(np.max(np.abs(vals))),1e-12); return float(np.max(vals.real)/scale)

def screen_case(comps,gammas,core,arm,gain,cfg,core_cfg):
    mi=build_mode_basis(comps,kelvin_harmonics=(1,2,3)); ctx=make_context(comps,gammas,core,arm,gain,core_cfg)
    # projected Jacobian and Kelvin
    J=projected_jacobian(comps,gammas,core,ctx,mi,0.005); kg=kelvin_growth(J,mi)
    # restoring: worst separation mode +/-
    restore=[]; base_clear=min_intercomponent(comps)
    for ii in family_indices(mi,'separation'):
        for sign in (-1.,1.):
            init=perturb(comps,mi['basis'][ii],sign*0.01); d0=max(shape_distance(comps,init),1e-12); steps=max(1,round(cfg['restore_T']/cfg['restore_dt'])); fin=rk4(init,gammas,core,ctx,cfg['restore_dt'],steps)
            restore.append((shape_distance(comps,fin)/d0,min_intercomponent(fin)/max(base_clear,1e-12),topology_drift(comps,fin)))
    rr=max((x[0] for x in restore),default=float('inf')); clear=min((x[1] for x in restore),default=0.0); lk=max((x[2] for x in restore),default=float('inf'))
    # ringdown along most unstable eigenvector
    vals,vecs=np.linalg.eig(J); k=int(np.argmax(vals.real)); f=np.tensordot(vecs[:,k].real,mi['basis'],axes=(0,0)); f/=max(np.linalg.norm(f),1e-12); init=perturb(comps,f,0.01); d0=max(shape_distance(comps,init),1e-12); cur=init; maxd=d0; steps=max(1,round(cfg['ring_T']/cfg['ring_dt']))
    for _ in range(steps): cur=rk4(cur,gammas,core,ctx,cfg['ring_dt'],1); maxd=max(maxd,shape_distance(comps,cur))
    ring=maxd/d0; lk=max(lk,topology_drift(comps,cur)); clear=min(clear,min_intercomponent(cur)/max(base_clear,1e-12))
    recovered=bool(rr<=1.25 and kg<=0.12 and ring<=1.75 and lk<=0.05 and clear>=0.5)
    return {'restoring_return_ratio_max':rr,'kelvin_growth':kg,'ringdown_max_over_initial':ring,'max_linking_drift':lk,'min_clearance_ratio':clear,'recovered':recovered,'mechanism_context':ctx}

def full_certify_case(comps,gammas,core,arm,gain,hard,core_cfg):
    mi=build_mode_basis(comps,kelvin_harmonics=tuple(hard.get('kelvin_harmonics',[1,2,3]))); ctx=make_context(comps,gammas,core,arm,gain,core_cfg)
    epss=[float(x) for x in hard.get('jacobian_eps_values',[0.0025,0.005])]
    Js=[projected_jacobian(comps,gammas,core,ctx,mi,e) for e in epss]
    jconv=0.0 if len(Js)<2 else max(float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-12)) for a,b in zip(Js[:-1],Js[1:]))
    J=Js[-1]; kg=kelvin_growth(J,mi)
    # restoring with full registered horizon
    base_clear=min_intercomponent(comps); restore=[]
    amp=float(hard['restoring_amp']); dt=float(hard['restoring_dt_ref']); steps=max(1,round(float(hard['restoring_T_final'])/dt))
    for ii in family_indices(mi,'separation'):
        for sign in (-1.,1.):
            init=perturb(comps,mi['basis'][ii],sign*amp); d0=max(shape_distance(comps,init),1e-12); fin=rk4(init,gammas,core,ctx,dt,steps)
            restore.append((shape_distance(comps,fin)/d0,min_intercomponent(fin)/max(base_clear,1e-12),topology_drift(comps,fin)))
    rr=max((x[0] for x in restore),default=float('inf')); clear=min((x[1] for x in restore),default=0.0); lk=max((x[2] for x in restore),default=float('inf'))
    # nonlinear ringdown along most unstable projected eigenvector
    vals,vecs=np.linalg.eig(J); k=int(np.argmax(vals.real)); f=np.tensordot(vecs[:,k].real,mi['basis'],axes=(0,0)); f/=max(np.linalg.norm(f),1e-12)
    amp=float(hard['ringdown_amp']); dt=float(hard['ringdown_dt_ref']); steps=max(1,round(float(hard['ringdown_T_final'])/dt)); stride=max(1,int(hard.get('ringdown_stride',1)))
    init=perturb(comps,f,amp); d0=max(shape_distance(comps,init),1e-12); cur=init; maxd=d0
    for s in range(steps):
        cur=rk4(cur,gammas,core,ctx,dt,1)
        if (s+1)%stride==0: maxd=max(maxd,shape_distance(comps,cur)); lk=max(lk,topology_drift(comps,cur)); clear=min(clear,min_intercomponent(cur)/max(base_clear,1e-12))
    ring=maxd/d0
    gates={
      'C0_jacobian_converged': bool(jconv<=float(hard['jacobian_convergence_max'])),
      'C2_restoring_bounded': bool(rr<=float(hard['restoring_return_ratio_max']) and clear>=float(hard['min_clearance_ratio_min']) and lk<=float(hard['max_linking_drift'])),
      'C3_kelvin_bounded': bool(kg<=float(hard.get('kelvin_restricted_normalized_growth_max',hard['normalized_growth_max']))),
      'C4_ringdown_bounded': bool(ring<=float(hard['ringdown_max_over_initial']) and clear>=float(hard['min_clearance_ratio_min']) and lk<=float(hard['max_linking_drift']))
    }
    recovered=all(gates.values())
    return {'jacobian_convergence':jconv,'restoring_return_ratio_max':rr,'kelvin_growth':kg,'ringdown_max_over_initial':ring,'max_linking_drift':lk,'min_clearance_ratio':clear,'gates':gates,'recovered':recovered,'mechanism_context':ctx}
