import math, numpy as np
from .geometry import frenet_geometry,resample_arclength
EPS=1e-14
def _rot(v,axis,angle):
    axis=axis/max(np.linalg.norm(axis),EPS); c=math.cos(angle); s=math.sin(angle); return v*c+np.cross(axis,v)*s+axis*np.dot(axis,v)*(1-c)
def _transport(v,ta,tb):
    ta=ta/max(np.linalg.norm(ta),EPS); tb=tb/max(np.linalg.norm(tb),EPS); c=float(np.clip(np.dot(ta,tb),-1,1)); ax=np.cross(ta,tb); s=float(np.linalg.norm(ax))
    if s<1e-12:
        if c>0: return v
        q=np.array([1.,0.,0.]) if abs(ta[0])<.9 else np.array([0.,1.,0.]); return _rot(v,np.cross(ta,q),math.pi)
    return _rot(v,ax,math.atan2(s,c))
def bishop_frame(x):
    _,t,_,_=frenet_geometry(x); n=len(x); axes=np.eye(3); a=axes[np.argmin(np.abs(axes@t[0]))]; e=a-np.dot(a,t[0])*t[0]; e/=max(np.linalg.norm(e),EPS); e1=np.empty_like(x); e2=np.empty_like(x); e1[0]=e; e2[0]=np.cross(t[0],e)
    for i in range(1,n):
        v=_transport(e1[i-1],t[i-1],t[i]); v-=np.dot(v,t[i])*t[i]; v/=max(np.linalg.norm(v),EPS); e1[i]=v; e2[i]=np.cross(t[i],v)
    return t,e1,e2
def holonomy(x):
    t,e1,e2=bishop_frame(x); v=_transport(e1[-1],t[-1],t[0]); v-=np.dot(v,t[0])*t[0]; v/=max(np.linalg.norm(v),EPS); return math.atan2(float(np.dot(e2[0],v)),float(np.dot(e1[0],v)))
def wrapped_angle_diff(a,b): return math.atan2(math.sin(a-b),math.cos(a-b))
def gauge_invariance_residual(x,gauge_amplitude=.7,harmonic=3):
    H=holonomy(x); n=len(x); u=np.arange(n+1)/n; psi=H*u; f=gauge_amplitude*np.sin(2*np.pi*harmonic*u); return abs(wrapped_angle_diff(psi[-1]-psi[0],(psi+f)[-1]-(psi+f)[0])),H
def holonomy_convergence(x,n1,n2):
    a=holonomy(resample_arclength(x,n1)); b=holonomy(resample_arclength(x,n2)); return a,b,abs(wrapped_angle_diff(a,b))
