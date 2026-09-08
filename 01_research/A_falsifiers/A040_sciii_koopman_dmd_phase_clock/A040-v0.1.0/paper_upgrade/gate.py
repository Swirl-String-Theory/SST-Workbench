from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

REQUIRED_SCHEMA='SST-GEOMETRIC-PHASE-1.0'
def dependency_guard(a030_certificate):
    ok=isinstance(a030_certificate,dict) and a030_certificate.get('family')=='A030' and a030_certificate.get('schema')==REQUIRED_SCHEMA and a030_certificate.get('status') in ('PASS','QUALIFIED')
    return {"migration_authorized":bool(ok),"required_schema":REQUIRED_SCHEMA}
def selftest():
    good={'family':'A030','schema':REQUIRED_SCHEMA,'status':'PASS'}; assert dependency_guard(good)['migration_authorized']; assert not dependency_guard({})['migration_authorized']
    return {"status":"PASS","policy":"DEFERRED_UNTIL_A030_CERTIFIED"}

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
