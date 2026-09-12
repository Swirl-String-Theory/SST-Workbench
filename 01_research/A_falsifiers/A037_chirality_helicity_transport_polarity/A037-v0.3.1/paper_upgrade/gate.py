from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    def _default(o):
        if hasattr(o, "tolist"):
            return o.tolist()
        if hasattr(o, "item"):
            return o.item()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    text=json.dumps(obj, indent=2, sort_keys=True, default=_default)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def response_tensor(q_plus, q_minus, delta):
    qp, qm = _arr(q_plus), _arr(q_minus)
    d=_arr(delta)
    if qp.shape != qm.shape or qp.ndim != 2: raise ValueError("q_plus/q_minus must be [n_observable,n_drive]")
    if d.shape != (qp.shape[1],): raise ValueError("delta must have one step per drive")
    chi=(qp-qm)/(2.0*d[None,:])
    return chi, 0.5*(chi+chi.T) if chi.shape[0]==chi.shape[1] else None, 0.5*(chi-chi.T) if chi.shape[0]==chi.shape[1] else None

def transform_response(chi, R_out, R_drive, axial_out=False, axial_drive=False):
    chi=_arr(chi); A=_arr(R_out); B=_arr(R_drive)
    so=np.linalg.det(A) if axial_out else 1.0
    sd=np.linalg.det(B) if axial_drive else 1.0
    return (so*A) @ chi @ (sd*B).T

def selection_matrix(R_out,R_drive,axial_out=False,axial_drive=False,tol=1e-12):
    A=_arr(R_out); B=_arr(R_drive); n=A.shape[0]; m=B.shape[0]
    allowed=np.zeros((n,m),bool)
    for i in range(n):
        for j in range(m):
            E=np.zeros((n,m)); E[i,j]=1.0
            T=transform_response(E,A,B,axial_out,axial_drive)
            allowed[i,j]=np.linalg.norm(T-E)<=tol
    return allowed

def covariance_error(chi,chi_transformed,R_out,R_drive,axial_out=False,axial_drive=False):
    pred=transform_response(chi,R_out,R_drive,axial_out,axial_drive)
    den=max(np.linalg.norm(pred),1e-30)
    return float(np.linalg.norm(_arr(chi_transformed)-pred)/den)

def selftest():
    # mirror x->-x, polar output+drive: diagonal allowed, xy/yx forbidden
    R=np.diag([-1.,1.,1.])
    M=selection_matrix(R,R)
    assert M[0,0] and M[1,1] and not M[0,1] and not M[1,0]
    qp=np.array([[.2,.6],[-.6,.4]]); qm=-qp; d=np.ones(2)
    chi,_,anti=response_tensor(qp,qm,d)
    assert abs(anti[0,1]-0.6)<1e-12
    return {"status":"PASS","selection_allowed":M.astype(int).tolist(),"antisymmetric_norm":float(np.linalg.norm(anti))}

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
