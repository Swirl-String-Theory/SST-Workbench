from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def floquet_multipliers(M): return np.linalg.eigvals(np.asarray(M,complex))

def mirror_monodromy(M,R,conjugate=False):
    M=np.asarray(M,complex); R=np.asarray(R,complex); Ri=np.linalg.inv(R)
    X=R@M@Ri
    return np.conj(X) if conjugate else X

def spectrum_match(a,b,conjugate=False):
    a=np.asarray(a,complex); b=np.asarray(b,complex); target=np.conj(a) if conjugate else a
    used=set(); errs=[]
    for z in target:
        js=[j for j in range(len(b)) if j not in used]; j=min(js,key=lambda k:abs(b[k]-z)); used.add(j); errs.append(abs(b[j]-z))
    return float(max(errs,default=0.0))

def require_admissibility(cert):
    return bool(isinstance(cert,dict) and cert.get('status') in ('PASS','QUALIFIED') and cert.get('provenance_sha256'))

def selftest():
    M=np.array([[1.1,.2],[0.,.8]],complex); R=np.diag([-1.,1.])
    Mm=mirror_monodromy(M,R)
    e=spectrum_match(floquet_multipliers(M),floquet_multipliers(Mm)); assert e<1e-12
    assert require_admissibility({'status':'PASS','provenance_sha256':'a'*64})
    return {"status":"PASS","spectrum_match_error":e}

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
