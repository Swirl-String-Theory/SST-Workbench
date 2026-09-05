from __future__ import annotations
import argparse,json,math
import numpy as np

def q(z,q0,q1,n):
    L=np.log1p(z); return q0+q1*L/(1+n*L)
def E(z,q0,q1,n):
    return (1+z)**(1+q0+q1/n)*(1+n*np.log1p(z))**(-q1/n**2)
def age_gyr(H0,q0,q1,n):
    # x=ln(1+z); adaptive-enough trapezoid over x∈[0,80]
    x=np.linspace(0,80,400000); y=np.exp(-(1+q0+q1/n)*x)*(1+n*x)**(q1/n**2)
    integ=np.trapezoid(y,x); mpc_km=3.0856775814913673e19; sec=integ*mpc_km/H0
    return sec/(365.25*86400*1e9)

a=argparse.ArgumentParser(); a.add_argument('json_file'); ns=a.parse_args(); d=json.load(open(ns.json_file,encoding='utf-8'))
H0,q0,q1,n=(float(d[k]) for k in ('H0','q0','q1','n'))
zs=math.exp(-1/n)-1 if n!=0 else None
qinf=q0+q1/n if n!=0 else None
den=q1+n*q0
zt=math.exp(-q0/den)-1 if den!=0 else None
out={'q_infinity':qinf,'future_pole_z':zs,'transition_z':zt,'age_Gyr':age_gyr(H0,q0,q1,n),'regular_on_minus1_to_0':not(-1<zs<0) if zs is not None else True}
if 'declared' in d:
    out['declared']=d['declared']; out['differences']={k:out[k]-float(v) for k,v in d['declared'].items() if k in out and isinstance(out[k],(int,float))}
print(json.dumps(out,indent=2))
