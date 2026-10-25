#!/usr/bin/env python3
"""Standalone A006 double-coil phase experiment, VortexLab v7.6.25b velocityCore semantics.
Raw phase != internal clock. No dynamical topology certification or finite-core Euler closure.
Unit system: R_ref=1, circulation Gamma=1, tau=Gamma*t/R_ref**2.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, time
from pathlib import Path
import numpy as np
from numba import njit
ROOT=Path(__file__).resolve().parent
A006=ROOT/'data/twist_KNOT_3_1_N1024_ORIG.json'
C0=.1395; DELTA=.25

def sample_source(path, N):
    obj=json.loads(path.read_text())
    data=obj['components'][0]['coeffs']; nh=max(4096,16*max(int(x['I']) for x in data))
    t=2*np.pi*np.arange(nh)/nh
    curve=np.zeros((nh,3),dtype=float)
    for off in range(0,len(data),32):
        b=data[off:off+32]
        I=np.array([int(x['I']) for x in b]); aa=np.array([x['A'] for x in b]); bb=np.array([x['B'] for x in b])
        curve += np.cos(np.outer(t,I))@aa + np.sin(np.outer(t,I))@bb
    dl=np.linalg.norm(np.roll(curve,-1,axis=0)-curve,axis=1)
    cum=np.r_[0, np.cumsum(dl)]; target=np.arange(N)*cum[-1]/N
    j=np.searchsorted(cum[1:],target,side='right');w=(target-cum[j])/np.maximum(cum[j+1]-cum[j],1e-30)
    X=curve[j]*(1-w[:,None])+curve[(j+1)%nh]*w[:,None]
    X-=X.mean(axis=0)
    X/=np.max(np.linalg.norm(X[:,:2],axis=1))
    return X

@njit(cache=True)
def velocity(X,Gamma,a):
    """Faithful numerical port: local LIA + *bare* nonlocal self midpoint kernel;
    adjacent segments skipped; no ghost/background, no external forcing.
    """
    n=len(X);v=np.zeros_like(X);pref=Gamma/(4*np.pi);eD=np.exp(DELTA)
    for i in range(n):
        im=(i-1)%n;ip=(i+1)%n
        ax=X[i,0]-X[im,0];ay=X[i,1]-X[im,1];az=X[i,2]-X[im,2]
        bx=X[ip,0]-X[i,0];by=X[ip,1]-X[i,1];bz=X[ip,2]-X[i,2]
        lm=np.sqrt(ax*ax+ay*ay+az*az);lp=np.sqrt(bx*bx+by*by+bz*bz)
        lf=pref*(np.log(2*np.sqrt(lm*lp)/(eD*a))+C0)*2/(lm*lp*(lm+lp))
        vx=lf*(ay*bz-az*by);vy=lf*(az*bx-ax*bz);vz=lf*(ax*by-ay*bx)
        for j in range(n):
            if j==im or j==i: continue
            jn=(j+1)%n
            dx=X[jn,0]-X[j,0];dy=X[jn,1]-X[j,1];dz=X[jn,2]-X[j,2]
            rx=X[i,0]-(X[j,0]+X[jn,0])*.5
            ry=X[i,1]-(X[j,1]+X[jn,1])*.5
            rz=X[i,2]-(X[j,2]+X[jn,2])*.5
            rr=rx*rx+ry*ry+rz*rz
            f=pref/(rr*np.sqrt(rr))
            vx+=(dy*rz-dz*ry)*f;vy+=(dz*rx-dx*rz)*f;vz+=(dx*ry-dy*rx)*f
        v[i,0]=vx;v[i,1]=vy;v[i,2]=vz
    return v

@njit(cache=True)
def rk4(X,dt,gamma,a):
    k1=velocity(X,gamma,a);k2=velocity(X+.5*dt*k1,gamma,a)
    k3=velocity(X+.5*dt*k2,gamma,a);k4=velocity(X+dt*k3,gamma,a)
    return X+(dt/6)*(k1+2*k2+2*k3+k4)

def torus_phase(X,p=2,q=3):
    Y=X-X.mean(0);rho=np.linalg.norm(Y[:,:2],axis=1);R=rho.mean()
    phi=np.arctan2(Y[:,1],Y[:,0]);beta=np.arctan2(Y[:,2],rho-R)
    ds=np.linalg.norm(np.roll(X,-1,axis=0)-X,axis=1)
    amp=np.dot(ds, np.exp(1j*(p*beta-q*phi)))/ds.sum()
    return np.angle(amp), np.abs(amp)

def rigid_normal_fit(X,V):
    """Least-squares best rigid velocity with tangential component projected out.
    NOTE: nearly circular knot => rotation/tangential motions weakly distinguishable.
    """
    r=X-X.mean(0)
    tang=np.roll(X,-1,axis=0)-np.roll(X,1,axis=0)
    tang/=np.linalg.norm(tang,axis=1)[:,None]
    proj=np.eye(3)[None,:,:]-tang[:,:,None]*tang[:,None,:]
    cross=np.zeros((len(X),3,3))
    cross[:,0,1]=r[:,2];cross[:,0,2]=-r[:,1]
    cross[:,1,0]=-r[:,2];cross[:,1,2]=r[:,0]
    cross[:,2,0]=r[:,1];cross[:,2,1]=-r[:,0]
    M=np.concatenate([proj,proj@cross],axis=2).reshape(-1,6)
    tgt=(proj@V[:,:,None]).reshape(-1)
    pars, *_=np.linalg.lstsq(M,tgt,rcond=None)
    residual=np.linalg.norm(tgt-M@pars)/np.sqrt(len(X))
    cond=np.linalg.cond(M)
    return pars[:3],pars[3:],float(residual),float(cond)

def metrics(X,gamma,a):
    phase,coherence=torus_phase(X)
    V=velocity(X,gamma,a)
    U,omega,defr,cond=rigid_normal_fit(X,V)
    ds=np.linalg.norm(np.roll(X,-1,axis=0)-X,axis=1)
    if len(X)%2!=0:raise ValueError('N must be even for paired passage diagnostics')
    pairs=np.linalg.norm(X[:len(X)//2]-X[len(X)//2:],axis=1)
    r=X-X.mean(0)
    return dict(raw_phase=float(phase), coherence=float(coherence), body_omega_z=float(omega[2]),
                body_U_z=float(U[2]), normal_residual=float(defr), fit_condition=float(cond),
                curve_length=float(ds.sum()), rms_radius=float(np.sqrt(np.mean((r*r).sum(1)))),
                pair_distance_p05=float(np.quantile(pairs,.05)),pair_distance_median=float(np.median(pairs)),
                pair_distance_p95=float(np.quantile(pairs,.95)), min_edge=float(np.min(ds)),
                center_z=float(X[:,2].mean()),
                rms_vel=float(np.sqrt(np.mean((V*V).sum(1)))))

def experiment(N=288,dt=1.5e-5,end=.255,a=.002,gamma=1,period_snapshot=60, progress=False):
    X=sample_source(A006,N)
    steps=round(end/dt)
    rows=[];shapes=[]
    start=time.monotonic()
    for k in range(steps+1):
        if k %period_snapshot==0 or k==steps:
            m=metrics(X,gamma,a);m['tau']=k*dt
            rows.append(m);shapes.append(X.copy())
        if progress and k and k%4000==0:
            print('integration',k,'/',steps,'wall_s',round(time.monotonic()-start,1),flush=True)
        if k==steps:break
        X=rk4(X,dt,gamma,a)
        if not np.isfinite(X).all() or np.max(np.abs(X))>100:
            raise RuntimeError('STABILITY FAILURE at step '+str(k))
    t=np.array([r['tau'] for r in rows]);raw=np.unwrap([r['raw_phase'] for r in rows]);Om=np.array([r['body_omega_z'] for r in rows]);alpha=np.r_[0,np.cumsum((Om[1:]+Om[:-1])/2*np.diff(t))]
    corrected=raw-raw[0]+3*alpha
    for j,r in enumerate(rows):
        r['raw_phase_unwrapped']=float(raw[j]-raw[0]);r['rigid_orientation_angle']=float(alpha[j]);r['relative_mode_phase']=float(corrected[j]);
        r['relative_poloidal_roll_phase']=float(corrected[j]/2)
    return rows,np.array(shapes)

def write_rows(path,rows):
    with open(path,'w',newline='',encoding='utf-8') as fp:
        wr=csv.DictWriter(fp,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)

def review(rows, name,N,dt,end,a):
    t=np.array([x['tau'] for x in rows]); raw=np.array([x['raw_phase_unwrapped'] for x in rows]); rel=np.array([x['relative_mode_phase'] for x in rows]); amp=np.array([x['coherence'] for x in rows]);
    rr=np.array([x['rms_radius'] for x in rows]); dd=np.array([x['pair_distance_median'] for x in rows]);
    om=np.array([x['body_omega_z'] for x in rows]);
    raw_cycle_times=np.interp(np.arange(1, int(abs(raw[-1]/(2*np.pi)))+1)*2*np.pi, -raw, t) if raw[-1]<0 else np.array([])
    periods=np.diff(np.r_[0,raw_cycle_times])
    return dict(name=name,N=N,dt=dt,final_tau=float(t[-1]),core_ratio=a,
      raw_mode_cycles=float(raw[-1]/(2*np.pi)),relative_poloidal_cycles=float(rel[-1]/(4*np.pi)),
      raw_mode_cycle_period_median=float(np.median(periods)) if len(periods) else None,
      raw_cycle_period_spread_p90_p10=float(np.quantile(periods,.9)-np.quantile(periods,.1)) if len(periods)>2 else None,
      coherence_min=float(amp.min()),coherence_end=float(amp[-1]),
      body_omega_initial=float(om[0]),body_omega_final=float(om[-1]),
      normal_residual_initial=float(rows[0]['normal_residual']),normal_residual_final=float(rows[-1]['normal_residual']),
      rigid_fit_condition_max=float(max(r['fit_condition'] for r in rows)),
      radius_peak_deviation_frac=float(np.max(abs(rr/rr[0]-1))),
      pair_distance_peak_deviation_frac=float(np.max(abs(dd/dd[0]-1))),
      minimum_pair_distance_p05=float(min(r['pair_distance_p05'] for r in rows)),
      source_sha256=hashlib.sha256(A006.read_bytes()).hexdigest())

def invariance_tests():
    X=sample_source(A006,96);v=velocity(X,1,.002)
    assert np.max(abs(velocity(X,-1,.002)+v))<1e-10
    shift=np.array([.17,-.2,3.7]);assert np.max(abs(velocity(X+shift,1,.002)-v))<1e-9
    phi,amp=torus_phase(X)
    X2=np.roll(X,13,axis=0);ph2,amp2=torus_phase(X2)
    assert abs(np.angle(np.exp(1j*(ph2-phi))))<1e-12 and abs(amp2-amp)<1e-12
    th=.11;c=np.cos(th);s=np.sin(th);rot=np.array([[c,-s,0],[s,c,0],[0,0,1.]])
    phi_rot,_=torus_phase(X@rot.T)
    rotphase_err=abs(np.angle(np.exp(1j*(phi_rot-phi+3*th))))
    assert rotphase_err<1e-10
    return {'gamma_reversal_max_abs':float(np.max(abs(velocity(X,-1,.002)+v))),
      'uniform_translation_velocity_max_abs':float(np.max(abs(velocity(X+shift,1,.002)-v))),
      'index_cyclic_phase_error_rad':float(abs(np.angle(np.exp(1j*(ph2-phi))))),
      'rigid_z_rotation_phase_error_rad':float(rotphase_err)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--N',type=int,default=288);p.add_argument('--dt',type=float,default=1.5e-5);p.add_argument('--end',type=float,default=.255)
    p.add_argument('--a',type=float,default=.002);p.add_argument('--name',default='main');p.add_argument('--progress',action='store_true');q=p.parse_args()
    out=ROOT/'results';out.mkdir(exist_ok=True)
    gates=invariance_tests()
    rows,shapes=experiment(N=q.N,dt=q.dt,end=q.end,a=q.a,progress=q.progress)
    write_rows(out/(q.name+'.csv'),rows)
    np.savez_compressed(out/(q.name+'_snapshots.npz'), X0=shapes[0], Xend=shapes[-1],
                        snapshots=shapes,t=np.array([r['tau'] for r in rows]))
    report=review(rows,q.name,q.N,q.dt,q.end,q.a)
    (out/(q.name+'_summary.json')).write_text(json.dumps({'scope':'DIMENSIONLESS CENTERLINE MODEL; NO MATERIAL CLOCK CERTIFICATION', 'tests':gates,'summary':report},indent=2))
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
