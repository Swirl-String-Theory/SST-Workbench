from __future__ import annotations
import math

def _reldiff(a,b):
    if a is None or b is None: return None
    try: a=float(a); b=float(b)
    except Exception: return None
    if not (math.isfinite(a) and math.isfinite(b)): return None
    scale=max(abs(a),abs(b),1e-14)
    return abs(a-b)/scale

def classify(values_by_resolution, resolved_tol=5e-3, converging_tol=5e-2, min_levels=3):
    pairs=sorted((int(k),v) for k,v in values_by_resolution.items() if v is not None)
    if len(pairs)<2:
        return {'status':'UNRESOLVED','relative_deltas':{},'finest_value':pairs[-1][1] if pairs else None}
    deltas={str(pairs[i][0]):_reldiff(pairs[i-1][1],pairs[i][1]) for i in range(1,len(pairs))}
    finite=[x for x in deltas.values() if x is not None and math.isfinite(x)]
    if len(pairs)<min_levels or not finite:
        status='COARSE'
    else:
        last=finite[-1]; prev=finite[-2] if len(finite)>=2 else None
        if last<=resolved_tol and (prev is None or prev<=max(converging_tol,4*resolved_tol)):
            status='RESOLVED'
        elif last<=converging_tol and (prev is None or last<=1.25*prev):
            status='CONVERGING'
        elif last<=converging_tol:
            status='COARSE'
        else:
            status='UNRESOLVED'
    return {'status':status,'relative_deltas':deltas,'finest_resolution':pairs[-1][0],'finest_value':pairs[-1][1]}

def classify_metric_table(levels, metric_names, **kwargs):
    out={}
    for m in metric_names:
        vals={str(level['resolution']):level['metrics'].get(m) for level in levels}
        out[m]=classify(vals,**kwargs)
    return out
