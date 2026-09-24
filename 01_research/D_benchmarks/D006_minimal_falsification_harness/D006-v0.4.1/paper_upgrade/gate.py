from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def central_difference(f,x,h):
    x=np.asarray(x,float); g=np.empty_like(x)
    for i in range(len(x)):
        d=np.zeros_like(x); d[i]=h; g[i]=(f(x+d)-f(x-d))/(2*h)
    return g

def rotation_matrix(axis,theta):
    a=np.asarray(axis,float); a=a/np.linalg.norm(a); x,y,z=a; c=np.cos(theta); s=np.sin(theta); C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])

def convergence_order(errors,hs):
    e=np.asarray(errors,float); h=np.asarray(hs,float)
    return np.log(e[:-1]/e[1:])/np.log(h[:-1]/h[1:])

def selftest():
    f=lambda x: np.sum(x*x); g=central_difference(f,[1.,2.,3.],1e-5); assert np.linalg.norm(g-[2.,4.,6.])<1e-8
    R=rotation_matrix([0,0,1],np.pi/2); assert np.linalg.norm(R@np.array([1.,0.,0.])-[0.,1.,0.])<1e-12
    return {"status":"PASS","gradient":g.tolist()}

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
