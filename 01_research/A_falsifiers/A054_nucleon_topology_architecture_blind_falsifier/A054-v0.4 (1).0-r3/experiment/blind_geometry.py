from __future__ import annotations
import numpy as np

Array=np.ndarray

def close_curve(x:Array)->Array:
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or x.shape[1]!=3 or len(x)<8: raise ValueError('curve must be Nx3 with N>=8')
    if np.linalg.norm(x[0]-x[-1])<1e-12: x=x[:-1]
    return x.copy()

def resample_closed_curve(x:Array,n:int)->Array:
    x=close_curve(x); y=np.vstack([x,x[0]])
    seg=np.linalg.norm(np.diff(y,axis=0),axis=1)
    if np.any(seg<=0):
        keep=np.r_[True,seg[:-1]>1e-14]; x=x[keep]; y=np.vstack([x,x[0]]); seg=np.linalg.norm(np.diff(y,axis=0),axis=1)
    s=np.r_[0.,np.cumsum(seg)]; target=np.linspace(0.,s[-1],n,endpoint=False); out=np.empty((n,3))
    for j in range(3): out[:,j]=np.interp(target,s,y[:,j])
    return out

def rotate_components(components:list[Array],R:Array)->list[Array]:
    R=np.asarray(R,float); return [np.asarray(c)@R.T for c in components]

def _segments(x:Array):
    a=close_curve(x); b=np.roll(a,-1,axis=0); return a,b,b-a,0.5*(a+b)

def gauss_linking_number(c1:Array,c2:Array)->float:
    _,_,dl1,m1=_segments(c1); _,_,dl2,m2=_segments(c2)
    diff=m1[:,None,:]-m2[None,:,:]; cross=np.cross(dl1[:,None,:],dl2[None,:,:]); den=np.linalg.norm(diff,axis=2)**3
    return float(np.sum(np.einsum('ijk,ijk->ij',cross,diff)/np.maximum(den,1e-18))/(4*np.pi))

def pairwise_link_matrix(components:list[Array])->Array:
    k=len(components); M=np.zeros((k,k))
    for i in range(k):
        for j in range(i+1,k): M[i,j]=M[j,i]=gauss_linking_number(components[i],components[j])
    return M

def load_components_npz(path)->list[Array]:
    z=np.load(path); keys=sorted(z.files,key=lambda s:int(s[1:]) if s.startswith('c') and s[1:].isdigit() else 999)
    return [close_curve(z[k]) for k in keys]
