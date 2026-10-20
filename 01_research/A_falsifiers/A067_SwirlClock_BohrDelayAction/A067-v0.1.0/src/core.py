"""SST Swirl Clock/Bohr-delay numerical controls.

The code does not use h, hbar, electron mass or other target constants.
Scientific inference requires certified, resolved 3D Euler data and a canonical reduction.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import brentq

TAU=2.0*math.pi

def find_branches(theta0: float, beta: float, samples: int=24001) -> list[dict]:
    """Exact dimensionless SST-60 locked roots theta=theta0-beta*sin(theta)."""
    if beta < 0 or samples < 4: raise ValueError('Require beta>=0, samples>=4')
    lo,hi=theta0-beta,theta0+beta
    x=np.linspace(lo,hi,samples,dtype=float)
    y=x-theta0+beta*np.sin(x)
    roots=[]
    if beta==0: return [{'theta':theta0,'A_tau':0.,'stability':'MARGINAL','n_approx':round(theta0/TAU)}]
    for i in range(samples-1):
        if y[i]*y[i+1]<0:
            r=float(brentq(lambda z: z-theta0+beta*math.sin(z),x[i],x[i+1],xtol=1e-13))
            roots.append(r)
        elif y[i]==0:
            roots.append(float(x[i]))
    if y[-1]==0: roots.append(float(x[-1]))
    roots=sorted(set(round(r,12) for r in roots))
    ret=[]
    for r in roots:
        a=beta*math.cos(r)
        # Certification only for the sufficient statements proved in SST-60.
        stability='STABLE_SUFFICIENT' if a>1e-9 else ('UNSTABLE_SUFFICIENT' if a < -1.-1e-9 else 'UNRESOLVED')
        ret.append({'theta':r,'A_tau':a,'stability':stability,
                    'n_approx':round(r/TAU),
                    'root_residual':abs(r-theta0+beta*math.sin(r))})
    return ret

def harmonic_action(mass:float,amp:float,omega:float,npoints:int=4001) -> dict:
    """J=integral m*qdot^2 dt over one harmonic period, and closed form."""
    if min(mass,amp,omega)<=0: raise ValueError('positive mass, amp, omega required')
    period=TAU/omega
    s=np.linspace(0.,TAU,npoints)
    qdot=-amp*omega*np.sin(s)
    j=float(mass*period/(TAU)*np.trapezoid(qdot*qdot,s))
    ja=math.pi*mass*omega*amp*amp
    return {'J_num_Js':j,'J_analytic_Js':ja,'relative_error':abs(j-ja)/ja}

def rotor_action(inertia:float,omega:float)->float:
    if inertia<=0:raise ValueError('inertia must be positive')
    return TAU*inertia*omega

def euler_scaling_check(mass:float,velocity:float,radius:float,lam:float)->dict:
    if min(mass,velocity,radius,lam)<=0: raise ValueError('positive inputs')
    j0=TAU*mass*velocity*radius
    j1=TAU*mass*(velocity*lam)*radius
    return {'initial_J_Js':j0,'scaled_J_Js':j1,'predicted_ratio':lam,'measured_ratio':j1/j0}

def integrate_phase(theta0:float,beta:float,target_theta:float,step:float=0.005,duration:float=50.0,perturb:float=0.03):
    """Explicit method of steps for dphi/ds=theta0+beta*sin(phi(s-1)-phi(s)).
    s is time normalized by delay. Delayed sample lands on grid.
    This is a numerical control, not an Euler solver.
    """
    lag=int(round(1./step)); step=1./lag
    count=int(round(duration/step))
    s=(np.arange(-lag,count+1)*step).astype(float)
    phi=np.empty_like(s)
    history=s[:lag+1]
    phi[:lag+1]=target_theta*history + perturb*np.sin(TAU*history*.73)
    for i in range(lag, len(s)-1):
        # delayed state is exact at s-1; explicit Euler for current state
        phi[i+1]=phi[i]+step*(theta0+beta*math.sin(phi[i-lag]-phi[i]))
    tail=s>=duration*.65
    fit=np.polyfit(s[tail],phi[tail],1)
    theta_est=float(fit[0]); slope_std=float(np.std(np.diff(phi[tail])/step))
    return {'theta_est':theta_est,'abs_error':abs(theta_est-target_theta),'slope_std':slope_std,
            'dt_over_delay':step,'n_steps':count}

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path:Path,obj)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
