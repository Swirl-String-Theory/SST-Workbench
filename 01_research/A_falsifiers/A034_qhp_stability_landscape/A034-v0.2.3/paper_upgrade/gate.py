from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def constrained_projector(C, rtol=1e-12):
    C=_arr(C)
    if C.size==0: return np.eye(C.shape[1] if C.ndim==2 else 0)
    # rows of C are constraint gradients; tangent space is null(C)
    U,s,Vt=np.linalg.svd(C, full_matrices=True)
    rank=int(np.sum(s > rtol*(s[0] if len(s) else 1.0)))
    Z=Vt[rank:].T
    return Z@Z.T

def constrained_gradient(g,C):
    P=constrained_projector(C); return P@_arr(g)

def constrained_hessian(H,C):
    P=constrained_projector(C); H=_arr(H)
    return P@H@P

def directional_no_go(g,C,directions,tol=0.0):
    gc=constrained_gradient(g,C)
    vals=[float(_arr(d)@gc) for d in directions]
    same_pos=all(v>tol for v in vals); same_neg=all(v<-tol for v in vals)
    return {"derivatives":vals,"no_stationary_directional_bracket":bool(same_pos or same_neg)}

def classify(g,H,C,grad_tol=1e-8,soft_tol=1e-6):
    gc=constrained_gradient(g,C); Hc=constrained_hessian(H,C)
    P=constrained_projector(C)
    # restrict to tangent subspace to avoid zero eigenvalues from constraints
    w,V=np.linalg.eigh(P)
    Z=V[:,w>0.5]
    ev=np.linalg.eigvalsh(Z.T@Hc@Z) if Z.size else np.array([])
    stationary=float(np.linalg.norm(gc))<=grad_tol
    emin=float(ev.min()) if len(ev) else float('nan')
    soft=bool(len(ev) and np.min(np.abs(ev))<=soft_tol)
    if not stationary: label='NONSTATIONARY'
    elif len(ev) and emin < -soft_tol: label='ENERGETIC_SADDLE'
    elif soft: label='SOFT_MODE'
    else: label='ENERGETICALLY_ADMISSIBLE'
    return {"label":label,"constrained_gradient_norm":float(np.linalg.norm(gc)),"tangent_hessian_eigenvalues":ev.tolist(),"soft_mode":soft}

def emit_modal_bridge(out):
    import sys
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from sst_qhp_falsifier.modal_bridge import emit_bridge
    return emit_bridge(out)

def selftest():
    # x constrained fixed, energy y^2+z^2 has positive tangent Hessian.
    C=np.array([[1.,0.,0.]])
    r=classify([7.,0.,0.],np.diag([-3.,2.,4.]),C)
    assert r['label']=='ENERGETICALLY_ADMISSIBLE' and r['constrained_gradient_norm']<1e-12
    r2=classify([0.,0.,0.],np.diag([1.,-2.,4.]),C)
    assert r2['label']=='ENERGETIC_SADDLE'
    return {"status":"PASS","positive_case":r,"saddle_case":r2}

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
