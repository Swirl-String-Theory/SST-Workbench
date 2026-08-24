import numpy as np
EPS=1e-15
def segment_lengths(x): return np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
def curve_length(x): return float(segment_lengths(x).sum())
def resample_arclength(x,n):
    x=np.asarray(x,float); seg=segment_lengths(x); s=np.concatenate([[0.0],np.cumsum(seg)]); L=s[-1]; xx=np.vstack([x,x[0]]); st=np.arange(n)*L/n
    out=np.empty((n,3))
    for j in range(3): out[:,j]=np.interp(st,s,xx[:,j])
    return out
def periodic_interp(x,u_new):
    n=len(x); u=np.arange(n+1)/n; xx=np.vstack([x,x[0]]); uu=np.mod(u_new,1.0); out=np.empty((len(uu),3))
    for j in range(3): out[:,j]=np.interp(uu,u,xx[:,j])
    return out
def periodic_derivative(f,ds,order=1):
    f=np.asarray(f)
    if order==1: return (np.roll(f,-1,axis=0)-np.roll(f,1,axis=0))/(2*ds)
    if order==2: return (np.roll(f,-1,axis=0)-2*f+np.roll(f,1,axis=0))/(ds*ds)
    if order==3: return (np.roll(f,-2,axis=0)-2*np.roll(f,-1,axis=0)+2*np.roll(f,1,axis=0)-np.roll(f,2,axis=0))/(2*ds**3)
    raise ValueError(order)
def frenet_geometry(x):
    L=curve_length(x); ds=L/len(x); r1=periodic_derivative(x,ds,1); r2=periodic_derivative(x,ds,2); r3=periodic_derivative(x,ds,3)
    cr=np.cross(r1,r2); sp=np.linalg.norm(r1,axis=1); cn=np.linalg.norm(cr,axis=1); k=cn/np.maximum(sp**3,EPS); tau=np.sum(cr*r3,axis=1)/np.maximum(cn**2,1e-20); t=r1/np.maximum(sp[:,None],EPS)
    return ds,t,k,tau
def estimate_thickness(x,exclude_fraction=0.03):
    n=len(x); _,_,k,_=frenet_geometry(x); rho_curv=np.inf if np.max(k)<=1e-14 else 1.0/np.max(k); skip=max(3,int(round(exclude_fraction*n))); idx=np.arange(n); md=np.inf
    for i in range(n):
        cyc=np.minimum((idx-i)%n,(i-idx)%n); mask=cyc>skip
        if np.any(mask): md=min(md,float(np.linalg.norm(x[mask]-x[i],axis=1).min()))
    rho_self=0.5*md if np.isfinite(md) else np.inf
    return float(min(rho_curv,rho_self)),float(rho_curv),float(rho_self)
def gauss_writhe_midpoint(x):
    n=len(x); p2=np.roll(x,-1,axis=0); dl=p2-x; mid=.5*(x+p2); total=0.0
    for i in range(n):
        r=mid[i]-mid; d2=np.sum(r*r,axis=1); mask=d2>1e-20; num=np.einsum("ij,ij->i",np.cross(dl[i],dl),r); total+=np.sum(num[mask]/np.power(d2[mask],1.5))
    return float(total/(4*np.pi))
def observables(x):
    L=curve_length(x); ds,_,k,tau=frenet_geometry(x); th,_,_=estimate_thickness(x); wr=gauss_writhe_midpoint(x) if len(x)<=768 else float("nan")
    return {"length":L,"thickness":th,"ropelength":L/max(th,EPS),"int_kappa2":float(np.sum(k*k)*ds),"int_tau2":float(np.sum(tau*tau)*ds),"writhe":wr}
def scale_to_core_units(x,thickness=None):
    if thickness is None: thickness=estimate_thickness(x)[0]
    if not np.isfinite(thickness) or thickness<=0: raise ValueError("invalid thickness")
    return x/thickness,thickness
def kabsch_align(P,Q):
    Pc=P-P.mean(axis=0); Qc=Q-Q.mean(axis=0); U,S,Vt=np.linalg.svd(Pc.T@Qc); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1,:]*=-1; R=Vt.T@U.T
    return Pc@R+Q.mean(axis=0)
def distorted_reparameterization(x,alpha=0.18,harmonic=2):
    n=len(x); u=np.arange(n)/n; ud=u+alpha/(2*np.pi*harmonic)*np.sin(2*np.pi*harmonic*u); return resample_arclength(periodic_interp(x,ud),n)
