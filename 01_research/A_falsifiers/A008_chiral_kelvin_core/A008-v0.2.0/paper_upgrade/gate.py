from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def channel_signature(R, polar_vector, axial_vector):
    R=_arr(R); p=_arr(polar_vector); a=_arr(axial_vector)
    return {"polar":(R@p).tolist(),"axial":(np.linalg.det(R)*R@a).tolist()}

def allowed_scalar_coupling(parities):
    # product parity +1 is mirror-even and may enter a scalar constitutive channel.
    prod=1
    for p in parities: prod*=int(p)
    return prod==1

def selftest():
    R=np.diag([-1.,1.,1.]); s=channel_signature(R,[1,0,0],[1,0,0])
    assert s['polar'][0]==-1 and s['axial'][0]==1
    assert allowed_scalar_coupling([-1,-1]) and not allowed_scalar_coupling([-1,1])
    return {"status":"PASS","signature":s}

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
