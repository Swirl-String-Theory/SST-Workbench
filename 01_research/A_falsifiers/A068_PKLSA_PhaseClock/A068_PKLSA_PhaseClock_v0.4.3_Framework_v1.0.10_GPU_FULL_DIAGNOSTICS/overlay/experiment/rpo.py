"""Full velocity-field relative-periodic-orbit detection (translations and cube rotations).

A low residual is a candidate only; independent temporal/spatial refinement and
full-field return after *reintegration* are separate prerequisites for certification.
"""
from __future__ import annotations
import itertools
import numpy as np
from scipy.optimize import minimize


def cube_rotations():
    mats=[]
    for p in itertools.permutations(range(3)):
        P=np.eye(3,dtype=int)[list(p)]
        for signs in itertools.product([-1,1],repeat=3):
            M=np.diag(signs)@P
            if round(np.linalg.det(M))==1:mats.append(M)
    assert len(mats)==24
    return mats


def rotate_field(u,M):
    """Proper cube symmetry about the cell-centred periodic domain origin."""
    m=np.asarray(M,int); out=np.empty_like(u)
    perm=tuple(int(np.where(m[k]!=0)[0][0]) for k in range(3))
    for i in range(3):
        arr=u[perm[i]].transpose(perm)
        for a in range(3):
            if m[a,perm[a]]<0:arr=np.flip(arr,axis=a)
        out[i]=int(m[i,perm[i]])*arr
    return out


def shift_field(u,s):
    n=u.shape[1]
    k=np.fft.fftfreq(n)*n
    x,y,z=np.meshgrid(k,k,k,indexing='ij')
    p=np.exp(-2j*np.pi*(x*s[0]+y*s[1]+z*s[2])/n)
    return np.fft.ifftn(np.fft.fftn(u,axes=(-3,-2,-1))*p,axes=(-3,-2,-1)).real


def best_translation(reference, sample,refine=True):
    """Min ||sample - shift(reference,s)|| / ||reference||, s in grid cells."""
    a=np.asarray(reference,float);b=np.asarray(sample,float)
    n=a.shape[1]
    fa=np.fft.fftn(a,axes=(-3,-2,-1)); fb=np.fft.fftn(b,axes=(-3,-2,-1))
    correlation=np.fft.ifftn(np.sum(np.conj(fa)*fb,axis=0)).real
    idx=np.unravel_index(np.argmax(correlation),correlation.shape)
    init=np.asarray(idx,dtype=float)
    init=np.where(init>n/2,init-n,init)
    norm=np.linalg.norm(a)
    def obj(x):
        residual=b-shift_field(a,x)
        return float(np.sum(residual*residual))/max(norm**2,1e-30)
    if refine:
        fit=minimize(obj,init,method='Powell',options={'maxiter':25,'xtol':1e-4,'ftol':1e-7})
        shift=np.asarray(fit.x);cost=float(fit.fun)
    else:shift=init;cost=obj(init)
    return {'residual':float(np.sqrt(max(cost,0))), 'shift_cells':((shift+n/2)%n-n/2).tolist(), 'shift_dimless':(((shift+n/2)%n-n/2)*2*np.pi/n).tolist()}


def full_field_rpo(t,fields,minimum_period=1.,tol=0.03,rotate=True,top_k=6):
    """Find candidate relative returns in *all 3*n^3 components*, not scalar phases.

    Search endpoints from a frozen t0=0; exhaustive 24 rotations for each endpoint.
    t0 reset and nonlinear shooting are NOT implemented, hence no certified RPO.
    """
    t=np.asarray(t,float);f=np.asarray(fields,float)
    if len(t)!=len(f) or len(t)<3:raise ValueError('Invalid time-series shape')
    n=f.shape[1];a=f[0].transpose(3,0,1,2)
    rotations=cube_rotations() if rotate else [np.eye(3,dtype=int)]
    allfits=[]
    for j in range(1,len(t)):
        if t[j]<minimum_period:continue
        b=f[j].transpose(3,0,1,2)
        best=None
        for rid,M in enumerate(rotations):
            rotated=rotate_field(a,M)
            trial=best_translation(rotated,b,refine=False)
            if best is None or trial['residual']<best['residual']:
                best={**trial,'rotation':M.tolist(),'rotation_index':rid,'time_index':j,'T_candidate':float(t[j])}
        allfits.append(best)
    allfits.sort(key=lambda q:q['residual'])
    chosen=[]
    for v in allfits:
        if all(abs(v['T_candidate']-w['T_candidate'])>2*(t[1]-t[0]) for w in chosen):
            chosen.append(v)
        if len(chosen)>=top_k:break
    for v in chosen:
        a2=rotate_field(a,np.asarray(v['rotation']))
        refined=best_translation(a2,f[v['time_index']].transpose(3,0,1,2),refine=True)
        v.update(refined)
    chosen.sort(key=lambda q:q['residual'])
    best=chosen[0] if chosen else None
    return {'schema':'SST-RPO-FULL-FIELD-2','search':'t0=0, 24 proper cubic rotations + arbitrary periodic 3D translations',
            'tested_endpoints':len(allfits),'rotation_count':len(rotations),
            'best':best,'top_candidates':chosen,'screen_tolerance_relative_l2':tol,
            'screen_pass':bool(best and best['residual']<tol),
            'certified_rpo':False,
            'qualification_note':'Frozen initial-time candidate search only. RPO requires second-return shooting, relative symmetry closure, mesh/time convergence and group-neutral mode certification; no certified RPO based on this screen alone.'}
