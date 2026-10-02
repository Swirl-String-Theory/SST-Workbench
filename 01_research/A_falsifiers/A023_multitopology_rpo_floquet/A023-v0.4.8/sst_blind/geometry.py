from __future__ import annotations
import math
import numpy as np

def segment_lengths(x): return np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
def arclength(x): return float(segment_lengths(np.asarray(x,float)).sum())

def resample_closed(x, n: int, target_length: float|None=None, center: bool=True):
    x=np.asarray(x,float)
    if len(x)<4: raise ValueError('need >=4 points')
    if np.linalg.norm(x[0]-x[-1])<1e-14: x=x[:-1]
    y=np.vstack([x,x[0]])
    ds=np.linalg.norm(np.diff(y,axis=0),axis=1)
    s=np.r_[0.0,np.cumsum(ds)]
    if s[-1]<=0: raise ValueError('zero arclength')
    u=np.linspace(0,s[-1],int(n)+1)[:-1]
    out=np.column_stack([np.interp(u,s,y[:,k]) for k in range(3)])
    if center: out-=out.mean(axis=0)
    if target_length is not None:
        L=arclength(out)
        out*=float(target_length)/L
    return out

def tangents(x):
    x=np.asarray(x,float); t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0); n=np.linalg.norm(t,axis=1); n[n==0]=1; return t/n[:,None]

def normal_component(x, field):
    t=tangents(x); f=np.asarray(field,float); return f-t*np.einsum('ij,ij->i',f,t)[:,None]

def rigid_fit(x, v):
    x=np.asarray(x,float); v=np.asarray(v,float); c=x.mean(axis=0); r=x-c
    A=np.zeros((3*len(x),6)); b=v.reshape(-1)
    for i,(rx,ry,rz) in enumerate(r):
        A[3*i:3*i+3,:3]=np.eye(3)
        A[3*i:3*i+3,3:]=np.array([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]],float)
    sol,*_=np.linalg.lstsq(A,b,rcond=None); U=sol[:3]; Om=sol[3:]
    pred=U+np.cross(np.repeat(Om[None,:],len(x),axis=0),r)
    return U,Om,pred,v-pred

def shape_field(x,v):
    U,Om,pred,res=rigid_fit(x,v)
    nr=normal_component(x,res)
    return nr,dict(U=U,Omega=Om,rigid=pred,residual=res)

def circular_smooth(a, width):
    a=np.asarray(a,float); w=max(1,int(width));
    if w<=1:return a.copy()
    k=np.ones(2*w+1)/(2*w+1); ext=np.r_[a[-w:],a,a[:w]]; return np.convolve(ext,k,mode='same')[w:-w]

def detect_lobes(x, k=3):
    x=np.asarray(x,float); n=len(x); c=x.mean(axis=0); r=np.linalg.norm(x-c,axis=1); rs=circular_smooth(r,max(2,n//100))
    loc=[i for i in range(n) if rs[i]>=rs[(i-1)%n] and rs[i]>=rs[(i+1)%n]]
    loc=sorted(loc,key=lambda i:rs[i],reverse=True); peaks=[]; sep=max(2,n//5)
    for i in loc:
        if all(min((i-j)%n,(j-i)%n)>=sep for j in peaks):
            peaks.append(i)
            if len(peaks)==k: break
    if len(peaks)<k:
        p0=int(np.argmax(rs)); peaks=[(p0+j*n//k)%n for j in range(k)]
    peaks=sorted(peaks)
    idx=np.arange(n); labels=np.zeros(n,dtype=np.int32)
    for i in range(n): labels[i]=int(np.argmin([min((i-p)%n,(p-i)%n) for p in peaks]))
    return np.asarray(peaks,int),labels,rs

def lobe_windows(x, peaks, labels):
    n=len(x); W=[]
    for k,p in enumerate(peaks):
        inds=np.where(labels==k)[0]; d=np.array([min((i-p)%n,(p-i)%n) for i in range(n)],float); dmax=max(1.0,float(d[inds].max()))
        w=np.zeros(n); z=np.clip(d[inds]/dmax,0,1); w[inds]=np.cos(0.5*np.pi*z)**2; W.append(w)
    return np.asarray(W)

def _orthonormalize_modes(x, named):
    out=[]; names=[]
    for name,f in named:
        g=normal_component(x,np.asarray(f,float)); _,_,_,g=rigid_fit(x,g); g=normal_component(x,g)
        for q in out: g-=q*np.mean(np.einsum('ij,ij->i',g,q))
        rms=math.sqrt(max(0.0,float(np.mean(np.sum(g*g,axis=1)))))
        if rms>1e-10: out.append(g/rms); names.append(name)
    return names,np.asarray(out)

def build_lobe_modes(x, peaks=None, labels=None):
    x=np.asarray(x,float); n=len(x); c=x.mean(axis=0)
    if peaks is None or labels is None: peaks,labels,_=detect_lobes(x)
    W=lobe_windows(x,peaks,labels); axes=[]; centers=[]
    for k in range(3):
        wk=W[k]; s=max(1e-30,wk.sum()); ck=(x*wk[:,None]).sum(axis=0)/s; a=ck-c; an=np.linalg.norm(a)
        if an<1e-12:
            pts=x[labels==k]-x[labels==k].mean(axis=0); _,_,vh=np.linalg.svd(pts,full_matrices=False); a=vh[0]; an=1
        axes.append(a/an); centers.append(ck)
    P=np.array([[1,1,1],[2,-1,-1],[0,1,-1]],float); P/=np.linalg.norm(P,axis=1)[:,None]
    named=[]
    for m,pat in enumerate(P):
        f=np.zeros_like(x)
        for k in range(3): f += pat[k]*W[k][:,None]*np.cross(np.repeat(axes[k][None,:],n,axis=0),x-centers[k])
        named.append((f"tilt_{m}",f))
    for m,pat in enumerate(P):
        f=np.zeros_like(x)
        for k in range(3): f += pat[k]*W[k][:,None]*axes[k]
        named.append((f"breathe_{m}",f))
    names,modes=_orthonormalize_modes(x,named)
    return dict(names=names,modes=modes,peaks=np.asarray(peaks),labels=np.asarray(labels),windows=W,axes=np.asarray(axes),centers=np.asarray(centers))

def apply_mode(x,mode,amp,target_length=2*np.pi): return resample_closed(np.asarray(x)+float(amp)*np.asarray(mode),len(x),target_length=target_length)

def kabsch_align(reference, mobile):
    A=np.asarray(reference,float); B=np.asarray(mobile,float); ca=A.mean(0);cb=B.mean(0); A0=A-ca;B0=B-cb; H=B0.T@A0; U,S,Vt=np.linalg.svd(H); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1;R=U@Vt
    return (B0@R)+ca

def nearest_cross_lobe_pair(x,labels,skip=8):
    x=np.asarray(x,float); labels=np.asarray(labels); n=len(x); best=(float('inf'),-1,-1)
    for i in range(n):
        js=np.arange(i+1,n); cyc=np.minimum(js-i,n-(js-i)); mask=(cyc>skip)&(labels[js]!=labels[i])
        if not np.any(mask): continue
        jj=js[mask]; d=np.linalg.norm(x[jj]-x[i],axis=1); z=int(np.argmin(d))
        if d[z]<best[0]:best=(float(d[z]),i,int(jj[z]))
    return dict(distance=best[0],i=best[1],j=best[2])

def distance_rate(x,v,i,j):
    d=x[i]-x[j]; n=np.linalg.norm(d)
    return float(np.dot(d/n,v[i]-v[j])) if n>0 else float('nan')

def circle(n,target_length=2*np.pi):
    R=target_length/(2*np.pi); t=np.linspace(0,2*np.pi,n,endpoint=False); return np.c_[R*np.cos(t),R*np.sin(t),np.zeros(n)]

def estimate_tube_thickness(x, *, stride=2, dcsc_tangent_tol=0.10, min_separation_fraction=0.08, curvature_quantile=0.01):
    """Robust polygon estimate of smooth-knot thickness = min(curvature radius, 1/2 doubly-critical self distance)."""
    x=np.asarray(x,float); n=len(x); h=max(1,int(stride))
    pm=np.roll(x,h,axis=0); pp=np.roll(x,-h,axis=0)
    a=np.linalg.norm(x-pm,axis=1); b=np.linalg.norm(pp-x,axis=1); c=np.linalg.norm(pp-pm,axis=1)
    cr=np.linalg.norm(np.cross(x-pm,pp-x),axis=1)
    R=a*b*c/(2*np.maximum(cr,1e-30))
    R=R[np.isfinite(R)&(R>0)]
    rcurv=float(np.quantile(R,float(curvature_quantile))) if len(R) else float('inf')
    t=(pp-pm); tn=np.linalg.norm(t,axis=1);tn[tn==0]=1;t=t/tn[:,None]
    skip=max(3,int(round(n*float(min_separation_fraction)))); best=float('inf'); bi=bj=-1; ca=cb=float('nan')
    for i in range(n):
        js=np.arange(i+1,n); cyc=np.minimum(js-i,n-(js-i)); js=js[cyc>skip]
        if not len(js): continue
        dv=x[js]-x[i]; dist=np.linalg.norm(dv,axis=1); good=dist>1e-14
        u=np.zeros_like(dv);u[good]=dv[good]/dist[good,None]
        c1=np.abs(u@t[i]); c2=np.abs(np.einsum('ij,ij->i',u,t[js])); mask=good&(c1<=dcsc_tangent_tol)&(c2<=dcsc_tangent_tol)
        if np.any(mask):
            ids=np.where(mask)[0]; z=ids[int(np.argmin(dist[ids]))]
            if dist[z]<best: best=float(dist[z]);bi=i;bj=int(js[z]);ca=float(c1[z]);cb=float(c2[z])
    pair_half=0.5*best if np.isfinite(best) else float('inf'); thick=min(rcurv,pair_half)
    return dict(thickness=float(thick),curvature_radius=float(rcurv),doubly_critical_distance=float(best),pair_half_distance=float(pair_half),pair_i=int(bi),pair_j=int(bj),pair_tangent_cos_i=ca,pair_tangent_cos_j=cb,stride=h,dcsc_tangent_tol=float(dcsc_tangent_tol),min_separation_fraction=float(min_separation_fraction),curvature_quantile=float(curvature_quantile))
