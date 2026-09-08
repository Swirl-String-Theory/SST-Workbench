from __future__ import annotations
import math
from collections import defaultdict
import numpy as np


def exact_sign_p_ge(k:int,n:int)->float:
    """One-sided exact Binomial(n, 1/2) upper tail."""
    if n <= 0:
        return 1.0
    k = int(k); n = int(n)
    return float(sum(math.comb(n,j) for j in range(k,n+1))/(2**n))


def carrier_cluster(values, carrier_ids, favorable_negative=True):
    """Aggregate repeated within-carrier conditions before inference.

    Returns one median per carrier and an exact sign test across carriers.  This
    deliberately prevents multiple beta/pitch/thread settings of one geometry
    from masquerading as independent knot samples.
    """
    groups=defaultdict(list)
    for cid,val in zip(carrier_ids,values):
        if np.isfinite(val): groups[str(cid)].append(float(val))
    meds={k:float(np.median(v)) for k,v in groups.items() if v}
    if favorable_negative:
        wins=sum(v<0 for v in meds.values()); losses=sum(v>0 for v in meds.values())
    else:
        wins=sum(v>0 for v in meds.values()); losses=sum(v<0 for v in meds.values())
    n=wins+losses
    return {
        'carrier_medians':meds,
        'n_carriers':len(meds),
        'n_nonzero_carriers':n,
        'favorable_carriers':wins,
        'unfavorable_carriers':losses,
        'one_sided_exact_sign_p':exact_sign_p_ge(wins,n),
        'median_of_carrier_medians':float(np.median(list(meds.values()))) if meds else float('nan'),
    }


def polynomial_pressure_law(beta, delta_p, degree=4):
    """Fit delta p = c1*b + ... + c_degree*b^degree (zero intercept)."""
    b=np.asarray(beta,float); y=np.asarray(delta_p,float)
    m=np.isfinite(b)&np.isfinite(y)&(np.abs(b)>1e-14)
    b=b[m];y=y[m]
    if len(b)<max(2,degree):
        return {'n':int(len(b)),'degree':degree,'coefficients':[],'r2':float('nan')}
    X=np.column_stack([b**k for k in range(1,degree+1)])
    q=np.linalg.lstsq(X,y,rcond=None)[0];pred=X@q
    ss=float(np.sum((y-pred)**2)); st=float(np.sum((y-y.mean())**2))
    r2=float(1-ss/max(st,1e-30))
    return {'n':int(len(b)),'degree':degree,'coefficients':[float(x) for x in q],'r2':r2}


def symmetric_even_odd(beta,delta_p,tol=1e-9):
    """Estimate even quadratic and odd linear responses from +/-beta pairs.

    even(+/-b)/b^2 estimates B when delta p = A b + B b^2 + ...
    odd(+/-b)/b estimates A at low order.
    """
    vals={round(float(b),12):float(y) for b,y in zip(beta,delta_p) if np.isfinite(b) and np.isfinite(y)}
    even=[];odd=[];pairs=[]
    for b,y in sorted(vals.items()):
        if b<=tol: continue
        yneg=vals.get(round(-b,12))
        if yneg is None: continue
        ev=.5*(y+yneg)/(b*b); od=.5*(y-yneg)/b
        even.append(ev);odd.append(od);pairs.append(b)
    return {
        'n_symmetric_pairs':len(pairs),
        'abs_beta_values':pairs,
        'even_quadratic_coefficients':even,
        'odd_linear_coefficients':odd,
        'median_even_quadratic_B':float(np.median(even)) if even else float('nan'),
        'median_odd_linear_A':float(np.median(odd)) if odd else float('nan'),
    }
