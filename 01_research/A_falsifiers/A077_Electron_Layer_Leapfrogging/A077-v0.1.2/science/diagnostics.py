"""A077-v0.1.1 deterministic diagnostics for the *reduced* ring model.

Cubic Hermite roots use endpoint states and the same right-hand-side ODE;
not an exact RK4 dense output. Crossing accuracy is certified only by refinement.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
from .ring_model import ring_derivative,trajectory


def clearance_trace(t, y, core_volumes):
    states=np.asarray(y,dtype=float).reshape((len(t),-1,2))
    v=np.asarray(core_volumes,dtype=float)
    radius=states[:,:,0]
    core=np.sqrt(v[None,:]/radius)
    if np.any(core<=0) or np.any(radius<=0): raise ValueError('invalid radius/core')
    out=np.full(len(t),np.inf)
    for i in range(states.shape[1]):
        for j in range(i+1,states.shape[1]):
            dist=np.hypot(radius[:,i]-radius[:,j],states[:,i,1]-states[:,j,1])
            out=np.minimum(out,dist-core[:,i]-core[:,j])
    return out


def hermite_event(t0,t1,f0,f1,df0,df1):
    """Bracketed cubic Hermite crossing time; root inside a sign-changing step."""
    if f0*f1>=0: raise ValueError('No sign-changing bracket')
    h=t1-t0
    def f(s):
        return ((2*s**3-3*s*s+1)*f0+(s**3-2*s*s+s)*h*df0+
                (-2*s**3+3*s*s)*f1+(s**3-s*s)*h*df1)
    lo=0.; hi=1.;flo=f0
    for _ in range(54):
        mid=(lo+hi)/2;fm=f(mid)
        if fm==0:return t0+h*mid
        if flo*fm<=0:hi=mid
        else:lo=mid;flo=fm
    return t0+h*(lo+hi)/2


def precise_events(t,y,gamma,volumes,ntheta,self_constant):
    times=np.asarray(t,float); vals=np.asarray(y,float)
    if vals.shape[1]!=4: raise ValueError('two rings required')
    dz=vals[:,3]-vals[:,1]
    slopes=np.array([ring_derivative(q,gamma,volumes,ntheta,self_constant)[3]
                     -ring_derivative(q,gamma,volumes,ntheta,self_constant)[1]
                     for q in vals])
    result=[]
    for i in range(len(times)-1):
        if dz[i]==0.0:
            result.append({'t':float(times[i]),'bracket':list(map(float,(times[i],times[i]))),'method':'sample_hit'})
        elif dz[i]*dz[i+1]<0:
            s=hermite_event(times[i],times[i+1],dz[i],dz[i+1],slopes[i],slopes[i+1])
            result.append({'t':float(s),'bracket':[float(times[i]),float(times[i+1])],
                           'bracket_width':float(times[i+1]-times[i]),'method':'cubic_hermite_bracketed'})
    return result


def detailed_run(initial,gamma,core,*,tf,steps,ntheta=96,self_constant=0.25):
    s=trajectory(initial,gamma,core,dt=tf/steps,steps=steps,ntheta=ntheta,self_constant=self_constant)
    yy=s['y'];tt=s['t'];v=s['a2R']
    assert len(tt)==steps+1
    clr=clearance_trace(tt,yy,v)
    events=precise_events(tt,yy,gamma,v,ntheta,self_constant) if len(gamma)==2 else []
    return s,{'events':events,'event_count':len(events),
               'minimum_surface_clearance':float(np.min(clr)) if len(gamma)>1 else None,
               'minimum_centerline_separation':float(np.min(clr+np.sum(np.sqrt(v[None,:]/yy.reshape(-1,len(gamma),2)[:,:,0]),axis=1))) if len(gamma)==2 else None,
               'collision_free_sampled':bool(np.all(clr>0)),
               'max_core_to_radius':float(np.max(np.sqrt(v[None,:]/yy.reshape(-1,len(gamma),2)[:,:,0]) / yy.reshape(-1,len(gamma),2)[:,:,0])),
               'final':yy[-1].tolist()},clr


def dump_trace(path,t,y,core_volumes,clearance,t_scale,r_scale):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    n=(len(y[0])//2)
    with path.open('w',encoding='utf-8',newline='') as fh:
        w=csv.writer(fh)
        w.writerow(['step','t_dimensionless','t_SI_s',*sum(([f'R{i}_dimensionless',f'z{i}_dimensionless',f'a{i}_dimensionless',f'R{i}_SI_m',f'z{i}_SI_m'] for i in range(n)),[]),'surface_clearance_dimensionless'])
        for step,(tt,q,cc) in enumerate(zip(t,y,clearance)):
            data=[]
            for i in range(n):
                r=float(q[2*i]);z=float(q[2*i+1]);a=float(math.sqrt(core_volumes[i]/r))
                data.extend([r,z,a,r*r_scale,z*r_scale])
            w.writerow([step,float(tt),float(tt*t_scale),*data,float(cc)])
    return path


def compare_refinements(cfg,case,axis_filter=None):
    p=cfg['initial_conditions_dimensionless'][case]
    y=np.column_stack((p['radii'],p['z'])).ravel()
    g=np.asarray(p['gamma_signs'],float)
    a=np.asarray(p['radii'],float)*cfg['core_ratio']
    tf=float(cfg['normalized_time_end']);ref=cfg['refinement_v011']
    sequence=[]
    for axis,levels,fixed in (
        ('angular',ref['angular_quadrature'],ref['fixed_steps']),
        ('temporal',ref['temporal_steps'],ref['fixed_ntheta'])):
        if axis_filter is not None and axis!=axis_filter:
            continue
        observations=[]
        for level in levels:
            st=fixed if axis=='angular' else level
            nt=level if axis=='angular' else fixed
            _,metric,_=detailed_run(y,g,a,tf=tf,steps=st,ntheta=nt,self_constant=cfg['self_induction_constant'])
            observations.append({'resolution':level,'steps':st,'ntheta':nt,'final':metric['final'],
                                 'events':[e['t'] for e in metric['events']],
                                 'clearance':metric['minimum_surface_clearance']})
        for low,high in zip(observations[:-1],observations[1:]):
            a0=np.asarray(low['final']);a1=np.asarray(high['final'])
            low['relative_endpoint_delta_to_next']=float(np.linalg.norm(a1-a0)/max(np.linalg.norm(a1),1e-14))
            low['max_event_shift_to_next']=(float(np.max(np.abs(np.array(low['events'])-np.array(high['events']))))
                  if len(low['events'])==len(high['events']) and low['events'] else None)
        sequence.append({'axis':axis,'levels':observations,'fixed_final_time':tf})
    return sequence
