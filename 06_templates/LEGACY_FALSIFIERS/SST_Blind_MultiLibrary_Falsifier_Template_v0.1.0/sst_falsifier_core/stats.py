from __future__ import annotations
import math, random
from fractions import Fraction
import numpy as np

def nearest_rational(x:float, qmax:int=12):
    f=Fraction(float(x)).limit_denominator(qmax)
    err=abs(float(x)-float(f))
    return {"p":f.numerator,"q":f.denominator,"value":float(f),"abs_error":err,
            "scaled_error":err*max(1,f.denominator)}

def benjamini_hochberg(pvals):
    p=np.asarray(pvals,float); n=len(p)
    if n==0:return np.array([])
    order=np.argsort(p); ranked=p[order]; q=np.minimum.accumulate((ranked*n/np.arange(1,n+1))[::-1])[::-1]
    out=np.empty(n); out[order]=np.clip(q,0,1); return out

def permutation_pvalue(observed, null_values, lower_is_better=True):
    arr=np.asarray(null_values,float)
    if len(arr)==0:return 1.0
    if lower_is_better: k=int(np.sum(arr<=observed))
    else: k=int(np.sum(arr>=observed))
    return (k+1)/(len(arr)+1)

def exact_sign_test(k,n):
    if n<=0:return 1.0
    # two-sided binomial p at p=1/2
    from math import comb
    lo=min(k,n-k)
    return min(1.0,2*sum(comb(n,i) for i in range(lo+1))/(2**n))
