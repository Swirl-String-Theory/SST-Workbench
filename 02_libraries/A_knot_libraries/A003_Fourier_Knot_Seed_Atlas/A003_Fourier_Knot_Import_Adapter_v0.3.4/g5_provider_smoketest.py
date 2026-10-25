#!/usr/bin/env python3
"""Single 3_1 Knot pyknotid compatibility smoke check (not G5 certification)."""
import importlib.metadata
import json
import sys
import numpy as np
from gates_g4_g5 import _independent_determinant


def main():
    report = {'test':'pyknotid_numpy2_compat_smoke_not_certification',
              'python_executable':sys.executable, 'numpy_version':np.__version__,
              'expected_determinant':3, 'topology_certified':False,
              'chirality_certified':False}
    try:
        report['pyknotid_version']=importlib.metadata.version('pyknotid')
    except importlib.metadata.PackageNotFoundError:
        report['pyknotid_version']='not_installed'
    t=np.linspace(0.0,2*np.pi,240,endpoint=False)
    knot=np.column_stack(((2+np.cos(3*t))*np.cos(2*t),
                          (2+np.cos(3*t))*np.sin(2*t),
                          np.sin(3*t)))
    try:
        det=_independent_determinant(knot)
        report['observed_determinant']=det
        report['status']='PASS_SOFTWARE_SMOKE' if det==3 else 'FAIL_PROVIDER_MISMATCH'
    except Exception as exc:
        report['status']='FAIL_PROVIDER_RUNTIME'
        report['exception_type']=type(exc).__name__
        report['exception_message']=str(exc)
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report['status']=='PASS_SOFTWARE_SMOKE' else 2

if __name__=='__main__':
    raise SystemExit(main())
