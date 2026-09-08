from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def polar_transform(v,R): return _arr(R)@_arr(v)
def axial_transform(v,R):
    R=_arr(R); return np.linalg.det(R)*R@_arr(v)
def body_frame_covariance_error(q,q_rot,R,kind='polar'):
    pred=polar_transform(q,R) if kind=='polar' else axial_transform(q,R)
    return float(np.linalg.norm(_arr(q_rot)-pred)/max(np.linalg.norm(pred),1e-30))
def mirror_pair_error(q_left,q_right,sign=-1):
    a=_arr(q_left); b=_arr(q_right); return float(np.linalg.norm(b-sign*a)/max(np.linalg.norm(a),1e-30))
def selftest():
    R=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    q=np.array([1.,2.,3.]); assert body_frame_covariance_error(q,R@q,R)<1e-12
    assert mirror_pair_error([1.,2.],[-1.,-2.])<1e-12
    return {"status":"PASS"}

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
