from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def normalize_modes(U,W=None):
    U=np.asarray(U,complex); W=np.eye(U.shape[1]) if W is None else np.asarray(W,complex)
    out=[]
    for u in U:
        n=np.sqrt(np.real(np.vdot(u,W@u))); out.append(u/max(n,1e-30))
    return np.asarray(out)

def parallel_transport(U,W=None):
    U=normalize_modes(U,W); W=np.eye(U.shape[1]) if W is None else np.asarray(W,complex)
    V=U.copy()
    for k in range(1,len(V)):
        ov=np.vdot(V[k-1],W@V[k])
        if abs(ov)>0: V[k]*=np.exp(-1j*np.angle(ov))
    return V

def geometric_phase(U,W=None,closed=True):
    V=parallel_transport(U,W); W=np.eye(V.shape[1]) if W is None else np.asarray(W,complex)
    if not closed: return 0.0
    ov=np.vdot(V[-1],W@V[0])
    return float(np.angle(ov))

def plaquette_curvature(u00,u10,u11,u01,W=None):
    us=[np.asarray(x,complex) for x in (u00,u10,u11,u01)]
    W=np.eye(len(us[0])) if W is None else np.asarray(W,complex)
    prod=1+0j
    for a,b in zip(us,us[1:]+us[:1]):
        ov=np.vdot(a,W@b); prod*=ov/max(abs(ov),1e-30)
    return float(np.angle(prod))

def selftest():
    # gauge-invariance: arbitrary phase factors do not change plaquette curvature.
    us=[np.array([1.,0.],complex),np.array([1.,1j])/np.sqrt(2),np.array([0.,1.],complex),np.array([1.,1.])/np.sqrt(2)]
    f1=plaquette_curvature(*us)
    phases=np.exp(1j*np.array([.2,-.7,1.1,2.3])); us2=[p*u for p,u in zip(phases,us)]
    f2=plaquette_curvature(*us2); assert abs(np.angle(np.exp(1j*(f1-f2))))<1e-12
    return {"status":"PASS","plaquette_curvature":f1,"gauge_shift_error":abs(f1-f2)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--selftest',action='store_true'); ap.add_argument('--input'); ap.add_argument('--output')
    ns=ap.parse_args()
    if ns.selftest: return _write(selftest(),ns.output)
    if not ns.input: ap.error('--input required unless --selftest')
    data=json.loads(Path(ns.input).read_text(encoding='utf-8'))
    # Generic dispatch: JSON may specify operation and args.
    op=data.pop('operation',None)
    if not op or op not in globals() or not callable(globals()[op]): raise SystemExit(f'unknown operation: {op}')
    _write(globals()[op](**data),ns.output)
if __name__=='__main__': main()
