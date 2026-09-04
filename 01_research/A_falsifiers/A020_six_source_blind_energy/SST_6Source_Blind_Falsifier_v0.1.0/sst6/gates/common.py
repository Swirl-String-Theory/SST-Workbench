from __future__ import annotations
import math
import numpy as np
from native_ext import load_backend
from sst6.geometry import pack_components, normalize_to_core, resample_components


def result(source:int, gate_id:str, hypothesis:str, tier:str, verdict:str, values:dict, thresholds:dict|None=None, notes:list[str]|None=None):
    return {
        "source": source,
        "gate_id": gate_id,
        "hypothesis": hypothesis,
        "tier": tier,
        "verdict": verdict,
        "values": values,
        "thresholds": thresholds or {},
        "notes": notes or [],
    }


def prepared(dataset, n_per_component:int):
    comps=resample_components(dataset.components,n_per_component)
    comps,core_dimless=normalize_to_core(dataset,comps)
    vertices,offsets=pack_components(comps)
    return comps,vertices,offsets,core_dimless


def native(config):
    return load_backend(force_python=bool(config.get("force_python",False)), force_build=False, build_verbose=False)


def fit_log_slope(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float)
    m=(x>0)&(y>0)&np.isfinite(x)&np.isfinite(y)
    if m.sum()<3: return float("nan"),float("nan")
    lx=np.log(x[m]); ly=np.log(y[m]); coef=np.polyfit(lx,ly,1); pred=np.polyval(coef,lx)
    ssr=float(np.sum((ly-pred)**2)); sst=float(np.sum((ly-ly.mean())**2))
    r2=1.0-ssr/sst if sst>0 else 1.0
    return float(coef[0]),float(r2)


def perturb_components(comps, perturbations):
    return [p+d for p,d in zip(comps,perturbations)]
