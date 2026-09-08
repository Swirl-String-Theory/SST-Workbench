from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def pair_mirror_modes(eval_a,eval_b):
    a=np.asarray(eval_a,complex); b=np.asarray(eval_b,complex); used=set(); out=[]
    for i,z in enumerate(np.conj(a)):
        js=[j for j in range(len(b)) if j not in used]; j=min(js,key=lambda k:abs(b[k]-z)); used.add(j); out.append((i,j,float(abs(b[j]-z))))
    return out

def soft_modes(evals, absolute_tol=1e-5, relative_tol=1e-3):
    e=np.asarray(evals,complex); scale=max(float(np.max(np.abs(e))),1e-30); thresh=max(absolute_tol,relative_tol*scale)
    idx=np.where(np.abs(e)<=thresh)[0]
    return {"threshold":thresh,"indices":idx.tolist(),"values":[str(e[i]) for i in idx]}

def reduced_manifold_breakdown(evals, projection_fraction, projection_min=0.2, **kw):
    s=soft_modes(evals,**kw)
    return {**s,"projection_fraction":float(projection_fraction),"reduced_manifold_breakdown":bool(s['indices'] and projection_fraction<projection_min)}

def selftest():
    s=reduced_manifold_breakdown([1+0j,1e-8+0j,-2j],.05); assert s['reduced_manifold_breakdown']
    p=pair_mirror_modes([1+2j],[1-2j]); assert p[0][2]<1e-12
    return {"status":"PASS","soft":s,"pair":p}

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
