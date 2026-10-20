"""v0.3.6: stdlib implementation of 2015 analytic XYZ regeneration.

Same analytic equations/derivatives and 2**18 trapezoidal arc-length grid as
historical regenerate.py; deterministic monotone linear inversion in place of
optional scipy PCHIP. Pure geometric seed generator, NEVER a physical source.
"""
from __future__ import annotations
import bisect, math

SEEDS=('A_Fourier_2015_p32','B_Torus_2015_p66')
PERIOD=2*math.pi
GRID_N=262144

def coordinate(name,t):
    if name==SEEDS[0]:
        return (math.cos(t)+1.5*math.cos(2*t),math.sin(t)-1.5*math.sin(2*t),.35*math.sin(3*t))
    if name==SEEDS[1]:
        r=2+math.cos(3*t)
        return (r*math.cos(2*t),r*math.sin(2*t),math.sin(3*t))
    raise ValueError('UNKNOWN_HISTORICAL_TREFOIL')

def derivative(name,t):
    if name==SEEDS[0]:
        return (-math.sin(t)-3*math.sin(2*t),math.cos(t)-3*math.cos(2*t),1.05*math.cos(3*t))
    if name==SEEDS[1]:
        r=2+math.cos(3*t);rp=-3*math.sin(3*t)
        return (rp*math.cos(2*t)-2*r*math.sin(2*t),rp*math.sin(2*t)+2*r*math.cos(2*t),3*math.cos(3*t))
    raise ValueError('UNKNOWN_HISTORICAL_TREFOIL')

def prepare(name,grid_n=GRID_N):
    if name not in SEEDS or grid_n!=GRID_N:raise ValueError('UNREGISTERED_SEED_OR_GRID')
    h=PERIOD/grid_n
    table=[0.0]*(grid_n+1)
    prev=math.sqrt(sum(v*v for v in derivative(name,0.)))
    total=0.
    for j in range(1,grid_n+1):
        t=j*h
        v=math.sqrt(sum(x*x for x in derivative(name,t)))
        total+=h*(v+prev)/2
        table[j]=total;prev=v
    if not math.isfinite(total) or total<=0:raise ValueError('UNPHYSICAL_ARCLENGTH')
    return {'name':name,'grid_n':grid_n,'arclength':total,'cumulative':table}

def sample(prepared,n):
    if n<16 or n>9600 or n%2:raise ValueError('INVALID_RESOLUTION')
    tstep=PERIOD/prepared['grid_n']
    arclength=prepared['arclength'];table=prepared['cumulative']
    points=[]
    for k in range(n):
        s=arclength*k/n
        i=bisect.bisect_right(table,s)-1
        i=min(max(0,i),len(table)-2)
        frac=(s-table[i])/(table[i+1]-table[i])
        t=(i+frac)*tstep
        points.append(coordinate(prepared['name'],t))
    return points
