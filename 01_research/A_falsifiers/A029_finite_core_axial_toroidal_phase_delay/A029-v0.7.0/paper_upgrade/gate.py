from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def pair_modes(eval_a, eval_b, parity='conjugate'):
    a=np.asarray(eval_a,complex); b=np.asarray(eval_b,complex)
    target=np.conj(a) if parity=='conjugate' else (-a if parity=='odd' else a)
    used=set(); pairs=[]
    for i,z in enumerate(target):
        js=[j for j in range(len(b)) if j not in used]
        if not js: break
        j=min(js,key=lambda k:abs(b[k]-z)); used.add(j)
        pairs.append((i,j,float(abs(b[j]-z))))
    return pairs

def branch_parity_error(vec_a, vec_b, R, sign=1):
    a=_arr(vec_a); b=_arr(vec_b); R=_arr(R)
    pred=sign*(a@R.T if a.ndim==2 else R@a)
    return float(np.linalg.norm(b-pred)/max(np.linalg.norm(pred),1e-30))

def selftest():
    a=np.array([1+2j,3-1j]); b=np.conj(a)[::-1]
    p=pair_modes(a,b,'conjugate'); assert max(x[2] for x in p)<1e-12
    R=np.diag([-1.,1.,1.]); v=np.array([1.,2.,3.]); e=branch_parity_error(v,R@v,R,1); assert e<1e-12
    return {"status":"PASS","pairs":p}

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
