from __future__ import annotations
import math

def relative_error(a,b,floor=1e-30): return abs(float(a)-float(b))/max(abs(float(a)),abs(float(b)),floor)

def compare_scalars(reference,candidate,tolerances):
    rows=[]; ok=True
    for key,tol in tolerances.items():
        if key not in reference or key not in candidate:
            rows.append({"key":key,"status":"MISSING"}); ok=False; continue
        err=relative_error(reference[key],candidate[key]); passed=err<=tol
        rows.append({"key":key,"relative_error":err,"tolerance":tol,"status":"PASS" if passed else "FAIL"}); ok &= passed
    return {"pass":ok,"rows":rows}
