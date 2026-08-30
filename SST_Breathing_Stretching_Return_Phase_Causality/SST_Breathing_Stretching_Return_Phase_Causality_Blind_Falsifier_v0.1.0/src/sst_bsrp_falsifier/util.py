import math
import numpy as np

def clean_json(x):
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)):
        return [clean_json(v) for v in x]
    if isinstance(x, np.generic):
        x=x.item()
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x
