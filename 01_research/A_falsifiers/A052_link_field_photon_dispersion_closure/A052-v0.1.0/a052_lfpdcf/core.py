from __future__ import annotations
import math

def centered_group_velocity(k, omega):
    if len(k)!=len(omega) or len(k)<3: raise ValueError('need >=3 aligned samples')
    out=[]
    for i in range(1,len(k)-1):
        dk=k[i+1]-k[i-1]
        if dk==0: raise ValueError('duplicate k')
        out.append((omega[i+1]-omega[i-1])/dk)
    return out

def log_slope(x,y):
    pts=[(math.log(a),math.log(b)) for a,b in zip(x,y) if a>0 and b>0]
    if len(pts)<2: return None
    xm=sum(a for a,b in pts)/len(pts); ym=sum(b for a,b in pts)/len(pts)
    sxx=sum((a-xm)**2 for a,b in pts); sxy=sum((a-xm)*(b-ym) for a,b in pts)
    if sxx==0:return None
    n=sxy/sxx; a=ym-n*xm
    ssr=sum((b-(a+n*x))**2 for x,b in pts); sst=sum((b-ym)**2 for x,b in pts)
    return {'slope':n,'intercept':a,'r2':1.0-ssr/sst if sst else 1.0}
