from __future__ import annotations
import math
from typing import Iterable, Sequence

def mean(xs):
    xs=list(xs)
    return sum(xs)/len(xs) if xs else float("nan")

def fraction(preds):
    xs=list(preds)
    return sum(bool(x) for x in xs)/len(xs) if xs else 0.0

def circular_order(phases: Sequence[float], weights: Sequence[float] | None=None) -> float:
    if not phases:
        return float("nan")
    if weights is None:
        weights=[1.0]*len(phases)
    z=0j; sw=0.0
    for p,w in zip(phases,weights):
        if w is None or not math.isfinite(float(w)) or float(w)<=0: continue
        z += float(w)*complex(math.cos(float(p)),math.sin(float(p)))
        sw += float(w)
    return abs(z/sw) if sw>0 else float("nan")

def rel_residual(series: Sequence[float]) -> float:
    vals=[float(x) for x in series if x is not None and math.isfinite(float(x))]
    if len(vals)<2: return float("nan")
    scale=max(abs(vals[0]),1e-15)
    return max(abs(v-vals[0]) for v in vals)/scale

def closest_link_class(x: float, tol: float=0.2):
    ax=abs(float(x))
    if abs(ax-1.0)<=tol: return "L2a1_like"
    if abs(ax-2.0)<=tol: return "L4a1_like"
    return "other"

def window_indices(times, config):
    pre_end=config['windows']['pre_end']; pulse_end=config['windows']['pulse_end']; post_start=config['windows']['post_start']
    pre=[i for i,t in enumerate(times) if float(t)<=pre_end]
    pulse=[i for i,t in enumerate(times) if pre_end < float(t) <= pulse_end]
    post=[i for i,t in enumerate(times) if float(t)>=post_start]
    return pre,pulse,post

def subset(xs, idx):
    return [xs[i] for i in idx]
