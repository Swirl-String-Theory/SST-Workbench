from __future__ import annotations
import numpy as np


def closed_arclength_resample(points,n):
    P=np.asarray(points,float); Q=np.vstack([P,P[0]])
    seg=np.linalg.norm(np.diff(Q,axis=0),axis=1)
    if np.any(seg<=0) or not np.isfinite(seg).all(): raise ValueError("degenerate centerline")
    u=np.concatenate([[0.0],np.cumsum(seg)]); x=np.linspace(0,u[-1],int(n),endpoint=False)
    return np.column_stack([np.interp(x,u,Q[:,j]) for j in range(3)])


def canonicalize(points,n,target_rms_radius=1.0):
    P=closed_arclength_resample(points,n); P=P-P.mean(axis=0); rms=float(np.sqrt(np.mean(np.sum(P*P,axis=1))))
    if not (rms>0): raise ValueError("zero RMS radius")
    return P*(float(target_rms_radius)/rms),{"input_rms_radius":rms,"scale_to_target":float(target_rms_radius)/rms}


def tangents(P):
    P=np.asarray(P,float); T=np.roll(P,-1,axis=0)-np.roll(P,1,axis=0); n=np.linalg.norm(T,axis=1)
    if np.any(n<=0): raise ValueError("degenerate tangent")
    return T/n[:,None]


def _rot_vec(v,axis,ang):
    axis=np.asarray(axis,float); n=np.linalg.norm(axis)
    if n<1e-14: return np.asarray(v,float)
    a=axis/n; v=np.asarray(v,float); c=np.cos(ang); s=np.sin(ang)
    return v*c+np.cross(a,v)*s+a*np.dot(a,v)*(1-c)


def bishop_frame_closed(P):
    T=tangents(P); n=len(P); E1=np.empty_like(T)
    axes=np.eye(3); ref=axes[np.argmin(np.abs(axes@T[0]))]; e=ref-np.dot(ref,T[0])*T[0]; e/=np.linalg.norm(e); E1[0]=e
    for j in range(n-1):
        a=T[j]; b=T[j+1]; ax=np.cross(a,b); sn=np.linalg.norm(ax); cs=np.clip(np.dot(a,b),-1,1)
        if sn>1e-14: e=_rot_vec(e,ax,np.arctan2(sn,cs))
        e=e-np.dot(e,b)*b; e/=np.linalg.norm(e); E1[j+1]=e
    # parallel-transport once across closure, then distribute the holonomy mismatch.
    a=T[-1]; b=T[0]; ax=np.cross(a,b); sn=np.linalg.norm(ax); cs=np.clip(np.dot(a,b),-1,1); eend=E1[-1]
    if sn>1e-14: eend=_rot_vec(eend,ax,np.arctan2(sn,cs))
    eend=eend-np.dot(eend,b)*b; eend/=np.linalg.norm(eend)
    delta=np.arctan2(np.dot(np.cross(eend,E1[0]),b),np.dot(eend,E1[0]))
    for j in range(n): E1[j]=_rot_vec(E1[j],T[j],delta*j/n)
    E2=np.cross(T,E1); E2/=np.linalg.norm(E2,axis=1)[:,None]
    return T,E1,E2,float(delta)


def kelvin_perturb(P,epsilon,mode):
    T,E1,E2,hol=bishop_frame_closed(P); th=2*np.pi*np.arange(len(P))/len(P); phase=mode*th
    Q=P+float(epsilon)*(np.cos(phase)[:,None]*E1+np.sin(phase)[:,None]*E2)
    return Q,{"mode":int(mode),"epsilon":float(epsilon),"frame_holonomy_correction":hol,"E1":E1,"E2":E2,"theta":th}


def align_by_base(base,pert,reference):
    B=np.asarray(base,float); P=np.asarray(pert,float); R=np.asarray(reference,float)
    bc=B.mean(axis=0); rc=R.mean(axis=0); X=B-bc; Y=R-rc
    U,_,Vt=np.linalg.svd(X.T@Y); Q=U@Vt
    if np.linalg.det(Q)<0: U[:,-1]*=-1; Q=U@Vt
    return (B-bc)@Q+rc,(P-bc)@Q+rc


def phase_and_ringdown(times,base_markers,pert_markers,reference,mode,amplitude_floor_fraction=0.03):
    _,E1,E2,_=bishop_frame_closed(reference); th=2*np.pi*np.arange(len(reference))/len(reference); carrier=np.exp(-1j*int(mode)*th)
    ph=[]; cm=[]; amps=[]
    for B,P in zip(base_markers,pert_markers):
        Ba,Pa=align_by_base(B,P,reference); d=Pa-Ba
        q=np.einsum('ij,ij->i',d,E1)+1j*np.einsum('ij,ij->i',d,E2)
        z=q*carrier; ph.append(np.angle(z)); cm.append(np.mean(z)); amps.append(np.abs(q))
    phi=np.unwrap(np.unwrap(np.asarray(ph),axis=1),axis=0)
    amp=np.asarray(amps); a0=max(float(np.median(amp[0])),1e-30); valid=float(np.mean(amp>=float(amplitude_floor_fraction)*a0))
    c=np.asarray(cm); R=np.abs(c)/max(abs(c[0]),1e-30)
    return phi,np.asarray(times,float),R,{"phase_valid_fraction":valid,"initial_median_perturbation_amplitude":a0,"initial_mode_amplitude":float(abs(c[0]))}
