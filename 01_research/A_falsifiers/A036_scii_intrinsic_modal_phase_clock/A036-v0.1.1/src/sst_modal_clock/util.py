import math
import numpy as np

def clean_json(x):
    if isinstance(x,dict): return {str(k):clean_json(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean_json(v) for v in x]
    if isinstance(x,np.ndarray): return clean_json(x.tolist())
    if isinstance(x,(np.floating,float)):
        v=float(x); return v if math.isfinite(v) else None
    if isinstance(x,(np.integer,)): return int(x)
    if isinstance(x,(np.bool_,)): return bool(x)
    return x
