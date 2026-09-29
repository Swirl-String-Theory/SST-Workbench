from pathlib import Path
import hashlib, json, math
import numpy as np
from .geometry import make_curve
from .modes import kabsch_align


def load_direction_manifest(root, relpath):
    return json.loads((Path(root)/relpath).read_text(encoding='utf-8'))


def load_direction(root, entry):
    p=Path(root)/entry['file']
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=entry['sha256']:
        raise RuntimeError(f'direction hash mismatch: {entry["direction_id"]}')
    d=np.asarray(np.load(p)['direction'],float)
    if d.shape!=(56,3) or not np.isfinite(d).all():
        raise RuntimeError(f'invalid direction: {entry["direction_id"]}')
    return d


def perturb_base(base, direction, epsilon):
    p=np.asarray(base,float)+float(epsilon)*np.asarray(direction,float)
    p-=p.mean(axis=0,keepdims=True)
    return p


def measured_perturbation_rms(points, base):
    p=kabsch_align(np.asarray(points,float),np.asarray(base,float))
    d=p-np.asarray(base,float)
    return float(np.sqrt(np.mean(np.sum(d*d,axis=1))))


def wilson_interval(k,n,z=1.959963984540054):
    if n<=0: return (float('nan'),float('nan'))
    p=k/n; den=1+z*z/n
    ctr=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.0,ctr-half),min(1.0,ctr+half)


def aggregate_amplitudes(rows, target_mode=3):
    out=[]
    epsvals=sorted(set(float(r['epsilon']) for r in rows))
    for eps in epsvals:
        rr=[r for r in rows if abs(float(r['epsilon'])-eps)<1e-15]
        strict=[r for r in rr if r['strict_target_pass']]
        anyp=[r for r in rr if r['persistence']['pass']]
        n=len(rr); k=len(strict); lo,hi=wilson_interval(k,n)
        ff=np.asarray([float(r['target_mean_frequency']) for r in strict if r.get('target_mean_frequency') is not None and np.isfinite(float(r['target_mean_frequency']))],float)
        fcv=float(np.std(ff)/max(abs(np.mean(ff)),1e-12)) if len(ff)>=2 else (0.0 if len(ff)==1 else float('inf'))
        modes={}
        for r in rr:
            m=r['persistence']['persistent_mode']
            key='none' if m is None else str(int(m)); modes[key]=modes.get(key,0)+1
        out.append({
            'epsilon':eps,'trajectory_count':n,'strict_target_support':k,'strict_target_fraction':float(k/n) if n else float('nan'),
            'strict_target_wilson_low':lo,'strict_target_wilson_high':hi,'any_persistent_support':len(anyp),
            'cross_direction_frequency_cv':fcv,'persistent_mode_histogram':modes,
            'mean_measured_perturbation_rms':float(np.mean([r['measured_perturbation_rms'] for r in rr])) if rr else float('nan')
        })
    return out
