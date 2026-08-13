from __future__ import annotations
import math
import numpy as np

PI=math.pi

def _ring(n:int,R:float)->np.ndarray:
    t=np.arange(n,dtype=float)*(2*PI/n)
    return np.column_stack((R*np.cos(t),R*np.sin(t),np.zeros(n)))

def _weight(r2:float,model:int)->float:
    if model==0: return (r2+1.0)**-1.5
    if model==1:
        r=max(math.sqrt(r2),1e-150); return (1.0-math.exp(-0.5*r2))/(r**3)
    if model==2: return (r2+2.0)**-1.5
    raise ValueError('core_model must be 0, 1 or 2')

def _velocity(p:np.ndarray,cell:float,shell:int,model:int,interaction_only:bool=False)->np.ndarray:
    n=len(p); v=np.zeros_like(p); coeff=1.0/(4*PI)
    for i in range(n):
        for ix in range(-shell,shell+1):
          for iy in range(-shell,shell+1):
           for iz in range(-shell,shell+1):
            if interaction_only and ix==0 and iy==0 and iz==0: continue
            sh=np.array([ix*cell,iy*cell,iz*cell])
            for j in range(n):
                k=(j+1)%n; a=p[j]+sh; b=p[k]+sh; dl=b-a; mid=(a+b)*0.5; r=p[i]-mid
                v[i]+=np.cross(dl,r)*(coeff*_weight(float(r@r),model))
    return v

def _remove_rigid(p:np.ndarray,v:np.ndarray):
    c=p.mean(axis=0); U=v.mean(axis=0); r=p-c; w=v-U
    A=np.zeros((3,3)); b=np.zeros(3)
    for ri,wi in zip(r,w): A += (ri@ri)*np.eye(3)-np.outer(ri,ri); b += np.cross(ri,wi)
    omega=np.linalg.lstsq(A,b,rcond=None)[0]
    s=w-np.cross(np.broadcast_to(omega,r.shape),r)
    return s,U,omega,float(np.sqrt(np.mean(np.sum(v*v,axis=1)))),float(np.sqrt(np.mean(np.sum(s*s,axis=1))))

def ring_base_metrics(n_nodes:int,ring_radius_over_core:float,cell_over_core:float,image_shell:int=1,core_model:int=0):
    p=_ring(n_nodes,ring_radius_over_core); _,U,O,raw,shape=_remove_rigid(p,_velocity(p,cell_over_core,image_shell,core_model))
    return {'raw_rms':raw,'shape_rms':shape,'relative_shape_residual':shape/max(raw,1e-300),'translation':U.tolist(),'rotation':O.tolist()}

def ring_normal_jacobian(n_nodes:int,ring_radius_over_core:float,cell_over_core:float,image_shell:int=1,fd_eps_over_core:float=1e-4,core_model:int=0,threads:int=1,interaction_only:bool=False):
    if cell_over_core <= 2*(ring_radius_over_core+1): raise ValueError('cell overlap')
    p=_ring(n_nodes,ring_radius_over_core); nrm=p.copy(); nrm[:,2]=0; nrm/=np.linalg.norm(nrm,axis=1)[:,None]; bin=np.tile([0.,0.,1.],(n_nodes,1))
    d=2*n_nodes; J=np.zeros((d,d))
    for col in range(d):
        j=col//2; e=bin[j] if col%2 else nrm[j]; pp=p.copy(); pm=p.copy(); pp[j]+=fd_eps_over_core*e; pm[j]-=fd_eps_over_core*e
        vp=_remove_rigid(pp,_velocity(pp,cell_over_core,image_shell,core_model,interaction_only))[0]; vm=_remove_rigid(pm,_velocity(pm,cell_over_core,image_shell,core_model,interaction_only))[0]
        dv=(vp-vm)/(2*fd_eps_over_core); J[0::2,col]=np.sum(dv*nrm,axis=1); J[1::2,col]=np.sum(dv*bin,axis=1)
    return J


def ring_normal_jacobian_c4(n_nodes:int,ring_radius_over_core:float,cell_over_core:float,image_shell:int=1,fd_eps_over_core:float=1e-4,core_model:int=0,threads:int=1,interaction_only:bool=False):
    if n_nodes % 4:
        return ring_normal_jacobian(n_nodes,ring_radius_over_core,cell_over_core,image_shell,fd_eps_over_core,core_model,threads,interaction_only)
    if cell_over_core <= 2*(ring_radius_over_core+1): raise ValueError('cell overlap')
    p=_ring(n_nodes,ring_radius_over_core); nrm=p.copy(); nrm[:,2]=0; nrm/=np.linalg.norm(nrm,axis=1)[:,None]; bin=np.tile([0.,0.,1.],(n_nodes,1))
    d=2*n_nodes; J=np.zeros((d,d)); quarter=n_nodes//4
    for col0 in range(2*quarter):
        j=col0//2; parity=col0%2; e=bin[j] if parity else nrm[j]
        pp=p.copy(); pm=p.copy(); pp[j]+=fd_eps_over_core*e; pm[j]-=fd_eps_over_core*e
        vp=_remove_rigid(pp,_velocity(pp,cell_over_core,image_shell,core_model,interaction_only))[0]; vm=_remove_rigid(pm,_velocity(pm,cell_over_core,image_shell,core_model,interaction_only))[0]
        dv=(vp-vm)/(2*fd_eps_over_core); vn=np.sum(dv*nrm,axis=1); vb=np.sum(dv*bin,axis=1)
        for rot in range(4):
            jt=(j+rot*quarter)%n_nodes; col=2*jt+parity
            idx=(np.arange(n_nodes)+rot*quarter)%n_nodes
            J[2*idx,col]=vn; J[2*idx+1,col]=vb
    return J

def ring_c4_symmetry_audit(n_nodes:int,ring_radius_over_core:float,cell_over_core:float,image_shell:int=1,fd_eps_over_core:float=1e-4,core_model:int=0,interaction_only:bool=False):
    if n_nodes % 4:
        return {'available':False,'relative_error':1.0,'max_abs_error':1.0}
    p=_ring(n_nodes,ring_radius_over_core); nrm=p.copy(); nrm[:,2]=0; nrm/=np.linalg.norm(nrm,axis=1)[:,None]; bin=np.tile([0.,0.,1.],(n_nodes,1)); quarter=n_nodes//4
    cols=[]
    for col in [0,1,2*quarter,2*quarter+1]:
        j=col//2; e=bin[j] if col%2 else nrm[j]; pp=p.copy(); pm=p.copy(); pp[j]+=fd_eps_over_core*e; pm[j]-=fd_eps_over_core*e
        vp=_remove_rigid(pp,_velocity(pp,cell_over_core,image_shell,core_model,interaction_only))[0]; vm=_remove_rigid(pm,_velocity(pm,cell_over_core,image_shell,core_model,interaction_only))[0]
        dv=(vp-vm)/(2*fd_eps_over_core); vals=np.empty(2*n_nodes); vals[0::2]=np.sum(dv*nrm,axis=1); vals[1::2]=np.sum(dv*bin,axis=1); cols.append(vals)
    diff2=ref2=maxabs=0.0
    for a,b in [(cols[0],cols[2]),(cols[1],cols[3])]:
        for i in range(n_nodes):
            it=(i+quarter)%n_nodes
            for k in [0,1]:
                av=float(a[2*i+k]); bv=float(b[2*it+k]); df=av-bv; diff2+=df*df; ref2+=bv*bv; maxabs=max(maxabs,abs(df))
    return {'available':True,'relative_error':math.sqrt(diff2)/max(math.sqrt(ref2),1e-300),'max_abs_error':maxabs}
