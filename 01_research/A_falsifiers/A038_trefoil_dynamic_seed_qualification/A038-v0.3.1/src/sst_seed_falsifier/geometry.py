import numpy as np

def segment_lengths(x): return np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
def arclength(x): return float(np.sum(segment_lengths(x)))
def center(x): return np.asarray(x,float)-np.mean(x,axis=0)

def resample_closed(x,n):
    x=np.asarray(x,float); d=segment_lengths(x); s=np.r_[0,np.cumsum(d)]; L=s[-1]
    xp=np.vstack([x,x[0]]); q=np.linspace(0,L,n,endpoint=False); out=np.empty((n,3))
    for j in range(3): out[:,j]=np.interp(q,s,xp[:,j])
    return out

def normalize_length(x,target=2*np.pi):
    x=center(x); L=arclength(x)
    if not np.isfinite(L) or L<=1e-12: raise ValueError('degenerate curve')
    return x*(float(target)/L)

def tangents(x):
    t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0); n=np.linalg.norm(t,axis=1); return t/np.maximum(n[:,None],1e-15)

def normal_frame(x):
    x=center(x); t=tangents(x); r=x-np.sum(x*t,axis=1)[:,None]*t; nr=np.linalg.norm(r,axis=1)
    bad=nr<1e-8
    if np.any(bad):
        axes=np.eye(3)
        for i in np.where(bad)[0]:
            a=axes[np.argmin(np.abs(axes@t[i]))]; r[i]=a-np.dot(a,t[i])*t[i]
    n=r/np.maximum(np.linalg.norm(r,axis=1)[:,None],1e-15); b=np.cross(t,n)
    # continuity repair
    for i in range(1,len(n)):
        if np.dot(n[i],n[i-1])<0: n[i]*=-1; b[i]*=-1
    return t,n,b

def min_nonlocal_vertex_distance(x,skip=3):
    x=np.asarray(x,float); n=len(x); best=np.inf
    for i in range(n):
        j=np.arange(n); cyc=np.minimum((j-i)%n,(i-j)%n); mask=cyc>skip
        if np.any(mask): best=min(best,float(np.min(np.linalg.norm(x[j[mask]]-x[i],axis=1))))
    return best

def kabsch(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); ac=a-a.mean(0); bc=b-b.mean(0); H=ac.T@bc; U,S,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    t=b.mean(0)-a.mean(0)@R.T
    aa=a@R.T+t; d=float(np.sqrt(np.mean(np.sum((aa-b)**2,axis=1))))
    return aa,d,R,t

def align_cyclic(a,b,coarse_stride=4):
    n=len(a); best=None
    coarse=list(range(0,n,max(1,int(coarse_stride))))
    for sh in coarse:
        aa,d,R,t=kabsch(np.roll(a,sh,axis=0),b)
        if best is None or d<best[0]: best=(d,sh,aa,R,t)
    sh0=best[1]
    for sh in sorted(set((sh0+k)%n for k in range(-max(1,coarse_stride),max(1,coarse_stride)+1))):
        aa,d,R,t=kabsch(np.roll(a,sh,axis=0),b)
        if d<best[0]: best=(d,sh,aa,R,t)
    return best[2],best[0],best[1],best[3],best[4]

def high_k_fraction(disp,cut_fraction=.33):
    z=np.fft.rfft(np.asarray(disp,float),axis=0); p=np.sum(np.abs(z)**2,axis=1); k0=max(2,int(np.ceil(cut_fraction*len(p)))); return float(np.sum(p[k0:])/max(np.sum(p[1:]),1e-30))

def rigid_normal_fit(x,u):
    x=np.asarray(x,float); u=np.asarray(u,float); c=x.mean(0); r=x-c; t=tangents(x); I=np.eye(3); rows=[]; rhs=[]
    for ri,ti,ui in zip(r,t,u):
        P=I-np.outer(ti,ti); S=np.array([[0,-ri[2],ri[1]],[ri[2],0,-ri[0]],[-ri[1],ri[0],0]])
        # omega x r = - r x omega = -S omega
        A=P@np.hstack([I,-S]); rows.append(A); rhs.append(P@ui)
    A=np.vstack(rows); y=np.hstack(rhs); q,*_=np.linalg.lstsq(A,y,rcond=None); V=q[:3]; om=q[3:]
    fit=(V[None,:]+np.cross(np.broadcast_to(om,r.shape),r)); un=u-np.sum(u*t,axis=1)[:,None]*t; fn=fit-np.sum(fit*t,axis=1)[:,None]*t
    res=un-fn; rms=lambda z:float(np.sqrt(np.mean(np.sum(z*z,axis=1))))
    rr=rms(res); uu=rms(un); ff=rms(fn); coh=float(max(0.0,1.0-rr/max(uu,1e-15)))
    return {'translation':V,'omega':om,'omega_mag':float(np.linalg.norm(om)),'translation_mag':float(np.linalg.norm(V)),'normal_rms':uu,'fit_rms':ff,'residual_rms':rr,'coherence':coh}

def pod_fraction(displacements,k=3):
    D=np.asarray(displacements,float)
    if D.ndim<3 or len(D)<2: return 0.0
    A=D.reshape(len(D),-1); A=A-A.mean(0,keepdims=True); s=np.linalg.svd(A,compute_uv=False); p=s*s
    return float(np.sum(p[:k])/max(np.sum(p),1e-30))

def fourier_normal_basis(x,kmax=4):
    x=np.asarray(x,float); _,n,b=normal_frame(x); N=len(x); s=np.arange(N)/N; vec=[]; labels=[]
    for k in range(1,kmax+1):
        for trig,name in [(np.cos,'c'),(np.sin,'s')]:
            f=trig(2*np.pi*k*s)[:,None]
            for frame,fn in [(n,'n'),(b,'b')]: vec.append(f*frame); labels.append(f'{fn}{name}{k}')
    # orthonormalize in Euclidean point metric
    Q=[]; qlabels=[]
    for v,l in zip(vec,labels):
        z=v.copy()
        for q in Q: z-=np.sum(z*q)*q
        nz=np.linalg.norm(z)
        if nz>1e-10: Q.append(z/nz); qlabels.append(l)
    return np.asarray(Q),qlabels
