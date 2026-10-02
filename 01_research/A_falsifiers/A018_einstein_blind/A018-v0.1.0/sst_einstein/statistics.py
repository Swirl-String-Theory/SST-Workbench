from __future__ import annotations
import numpy as np


def acf(x: np.ndarray, max_lag: int) -> np.ndarray:
    x=np.asarray(x,float); x=x-np.mean(x)
    var=float(np.dot(x,x))
    if var<=0: return np.full(max_lag+1,np.nan)
    out=np.empty(max_lag+1,float);out[0]=1.0
    for k in range(1,max_lag+1): out[k]=float(np.dot(x[:-k],x[k:])/var)
    return out


def decorrelation_lag(ac: np.ndarray, tol: float, consecutive: int=5) -> int|None:
    for k in range(1,max(1,len(ac)-consecutive+1)):
        w=np.abs(ac[k:k+consecutive])
        if len(w)==consecutive and np.all(np.isfinite(w)) and np.all(w<tol): return k
    return None


def msd(signal: np.ndarray, max_lag: int) -> tuple[np.ndarray,np.ndarray]:
    x=np.asarray(signal,float)
    lags=[];vals=[]
    for k in range(1,max_lag+1):
        d=x[k:]-x[:-k]
        if len(d): lags.append(k);vals.append(float(np.mean(d*d)))
    return np.asarray(lags,float),np.asarray(vals,float)


def robust_mad(x: np.ndarray) -> float:
    x=np.asarray(x,float); med=np.median(x)
    return float(1.4826*np.median(np.abs(x-med)))


def detect_positive_events(series: np.ndarray, z: float=4.0) -> np.ndarray:
    x=np.asarray(series,float)
    dx=np.diff(x)
    med=float(np.median(dx)); mad=robust_mad(dx)
    if not np.isfinite(mad) or mad<=0: return np.array([],float)
    thr=med+z*mad
    mask=dx>thr
    events=[]; i=0
    while i<len(dx):
        if not mask[i]: i+=1; continue
        s=0.0
        while i<len(dx) and mask[i]: s+=max(0.0,float(dx[i])); i+=1
        if s>0: events.append(s)
    return np.asarray(events,float)


def _quant_score(events: np.ndarray, q: float) -> float:
    r=events/q
    n=np.maximum(1.0,np.rint(r))
    return float(np.sqrt(np.mean((r-n)**2)))


def fit_quantum(events: np.ndarray, q_grid: int=300) -> tuple[float,float]:
    e=np.asarray(events,float); e=e[np.isfinite(e)&(e>0)]
    if len(e)<3: return float("nan"),float("nan")
    med=float(np.median(e)); lo=med/8.0; hi=med*1.25
    qs=np.geomspace(lo,hi,q_grid)
    scores=np.array([_quant_score(e,q) for q in qs])
    j=int(np.argmin(scores)); return float(qs[j]),float(scores[j])


def quantization_cross_validation(events: np.ndarray, rng: np.random.Generator, n_surrogates: int=200) -> dict:
    e=np.asarray(events,float); e=e[np.isfinite(e)&(e>0)]
    if len(e)<8: return {"ok":False,"reason":"too few events"}
    perm=rng.permutation(len(e)); cut=len(e)//2
    train=e[perm[:cut]]; test=e[perm[cut:]]
    q,train_score=fit_quantum(train)
    test_score=_quant_score(test,q)
    # Continuous positive null matched in log-space. The q is refit on each null training set.
    loge=np.log(e); mu=float(np.mean(loge)); sig=max(float(np.std(loge,ddof=1)),1e-12)
    null_scores=[]
    for _ in range(n_surrogates):
        s=rng.lognormal(mu,sig,size=len(e)); pp=rng.permutation(len(s)); tr=s[pp[:cut]]; te=s[pp[cut:]]
        qn,_=fit_quantum(tr); null_scores.append(_quant_score(te,qn))
    null=np.asarray(null_scores,float)
    p=(1.0+float(np.sum(null<=test_score)))/(1.0+len(null))
    return {"ok":True,"q":float(q),"train_score":float(train_score),"test_score":float(test_score),
            "surrogate_p":float(p),"null_median_score":float(np.median(null))}
