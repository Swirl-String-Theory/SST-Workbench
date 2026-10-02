from __future__ import annotations
import numpy as np
from native_ext import biot_savart,interaction_energy,gauss_linking
from .geometry import tangents

def total_velocity(comps,core_radius,kernel='softcore',threads=0):
    outs=[]
    for q in comps:
        v=np.zeros_like(q)
        for src in comps:v+=biot_savart(src,q,core_radius,kernel,threads)
        outs.append(v)
    return outs

def total_energy_length(comps,core_radius,threads=0):
    s=0.0
    for a in comps:
        for b in comps:s+=interaction_energy(a,b,core_radius,threads)
    return 0.5*s  # E/(rho Gamma^2), dimensions of length

def relative_equilibrium(comps,vels):
    pts=np.vstack(comps);vv=np.vstack(vels);tt=np.vstack([tangents(p) for p in comps]);c=pts.mean(axis=0);rows=[];rhs=[]
    for x,v,t in zip(pts,vv,tt):
        P=np.eye(3)-np.outer(t,t);r=x-c;S=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]],float)
        rows.append(np.hstack([P,-P@S]));rhs.append(P@v)
    A=np.vstack(rows);b=np.concatenate(rhs);coef,*_=np.linalg.lstsq(A,b,rcond=None);U=coef[:3];Om=coef[3:];pred=[];res=[];base=[]
    for x,v,t in zip(pts,vv,tt):
        P=np.eye(3)-np.outer(t,t);rig=U+np.cross(Om,x-c);pred.append(rig);res.append(P@(v-rig));base.append(P@v)
    res=np.vstack(res);base=np.vstack(base);den=np.linalg.norm(base);nrmse=float(np.linalg.norm(res)/max(den,1e-300));return {'normal_nrmse':nrmse,'translation':U.tolist(),'omega':Om.tolist(),'normal_velocity_rms':float(np.sqrt(np.mean(np.sum(base*base,axis=1)))),'residual_rms':float(np.sqrt(np.mean(np.sum(res*res,axis=1))))}

def orientation_symmetry(comps,core_radius,kernel,threads=0):
    v=total_velocity(comps,core_radius,kernel,threads);rev=[p[::-1].copy() for p in comps];vr=total_velocity(rev,core_radius,kernel,threads);num=0.0;den=0.0
    for a,b in zip(v,vr):num+=np.sum((b[::-1]+a)**2);den+=np.sum(a*a)
    return float(np.sqrt(num/max(den,1e-300)))

def mirror_symmetry(comps,core_radius,kernel,threads=0):
    M=np.diag([-1.0,1.0,1.0]);v=total_velocity(comps,core_radius,kernel,threads);mir=[p@M.T for p in comps];vm=total_velocity(mir,core_radius,kernel,threads);num=0.0;den=0.0
    for a,b in zip(v,vm):target=-(a@M.T);num+=np.sum((b-target)**2);den+=np.sum(target*target)
    return float(np.sqrt(num/max(den,1e-300)))

def _frame(t):
    axes=np.eye(3);ref=axes[np.argmin(np.abs(axes@t))];n1=np.cross(t,ref);n1/=np.linalg.norm(n1);n2=np.cross(t,n1);return n1,n2

def meridian_loop(p,idx,radius,npts):
    t=tangents(p)[idx];n1,n2=_frame(t);ang=np.linspace(0,2*np.pi,npts,endpoint=False);return p[idx]+radius*(np.cos(ang)[:,None]*n1+np.sin(ang)[:,None]*n2)

def holonomy_metrics(comps,thickness,stations_per_component=3,loop_points=96,loop_radius_fraction=0.25,threads=0):
    rows=[];rad=loop_radius_fraction*thickness
    for ci,p in enumerate(comps):
        ids=np.linspace(0,len(p)-1,stations_per_component,endpoint=False,dtype=int)
        for idx in ids:
            loop=meridian_loop(p,int(idx),rad,loop_points);q=np.roll(loop,-1,axis=0);mid=.5*(loop+q);dl=q-loop;v=np.zeros_like(mid)
            for src in comps:v+=biot_savart(src,mid,0.0,'singular',threads)
            h=float(np.sum(v*dl));lk=sum(gauss_linking(src,loop,0.0,threads) for src in comps);nearest=int(np.rint(lk));rows.append({'component':ci,'station':int(idx),'holonomy_over_Gamma':h,'gauss_linking':float(lk),'nearest_integer':nearest,'integer_abs_error':float(abs(h-nearest))})
    return rows
