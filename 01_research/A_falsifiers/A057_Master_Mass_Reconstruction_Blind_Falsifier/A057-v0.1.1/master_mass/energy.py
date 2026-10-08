from __future__ import annotations
import numpy as np
from .geometry import as_closed

def segment_data(points):
    p=as_closed(points); q=np.roll(p,-1,axis=0); return .5*(p+q),q-p

def energy_matrix(components, core=1.0, dtype=np.float64):
    comps=[np.asarray(as_closed(c),dtype=dtype) for c in components]; m=len(comps); E=np.zeros((m,m),dtype=np.float64)
    dat=[segment_data(c) for c in comps]
    a2=float(core)**2
    for i in range(m):
        mi,di=dat[i]
        for j in range(i,m):
            mj,dj=dat[j]; val=0.0
            for k in range(len(mi)):
                r=mi[k]-mj; den=np.sqrt(np.einsum('ij,ij->i',r,r)+a2); num=dj@di[k]; val+=float(np.sum(num/np.maximum(den,1e-15)))
            E[i,j]=E[j,i]=val
    return E

def total_kernel(E): return float(np.asarray(E,dtype=float).sum())
def decomposition(E):
    E=np.asarray(E,dtype=float); diag=float(np.trace(E)); mutual=float(E.sum()-np.trace(E)); return {"self":diag,"mutual":mutual,"total":diag+mutual,"closure_error":abs((diag+mutual)-E.sum())/max(abs(E.sum()),1e-30)}
def coherence_matrix(E):
    E=np.asarray(E,dtype=float); d=np.sqrt(np.maximum(np.abs(np.diag(E)),1e-30)); return E/(d[:,None]*d[None,:])
def coherence_metrics(E):
    C=coherence_matrix(E); vals=np.linalg.eigvalsh(.5*(C+C.T)); absvals=np.abs(vals); s=absvals.sum(); p=absvals/s if s>0 else absvals
    entropy=float(-np.sum(np.where(p>0,p*np.log(p),0.0))) if p.size else 0.0
    pr=float((absvals.sum()**2)/max(np.sum(absvals**2),1e-30)) if p.size else 0.0
    return {"matrix":C.tolist(),"eigenvalues":vals.tolist(),"participation_ratio":pr,"spectral_entropy":entropy,"lambda_max":float(vals.max()) if vals.size else None}
def relative_l2(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-30))
