#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sst_hopf_native import load_native
import sst_hopf_common as hc


def max_abs(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def main() -> int:
    native = load_native(force_build=False, verbose=True)
    if native is None:
        print("Native extension unavailable")
        return 2
    ref = hc._PYTHON_REFERENCE
    results = []
    rng = np.random.default_rng(20260807)

    phi = rng.normal(size=(8, 7, 6, 2)) + 1j*rng.normal(size=(8, 7, 6, 2))
    ppsi, pnorm, pdef = ref["normalize_spinor"](phi)
    cpsi, cnorm, cdef = native.normalize_spinor(phi, 1e-14)
    results.append(("normalize_spinor.psi", max_abs(ppsi,cpsi), 2e-14))
    results.append(("normalize_spinor.norm2", max_abs(pnorm,cnorm), 2e-14))
    results.append(("normalize_spinor.defects", float(np.count_nonzero(pdef != cdef)), 0.0))

    pn = ref["hopf_map"](ppsi); cn = native.hopf_map(cpsi)
    results.append(("hopf_map", max_abs(pn,cn), 2e-14))

    h=0.17
    pa=ref["connection_from_spinor"](ppsi,h); ca=native.connection_from_spinor(cpsi,h)
    results.append(("connection", max_abs(pa,ca), 2e-12))
    pb=ref["curl"](pa,h); cb=native.curl(ca,h)
    results.append(("curl", max_abs(pb,cb), 2e-11))

    pbc=ref["director_curvature_b"](pn,h); cbc=native.director_curvature_b(cn,h)
    results.append(("director_curvature_b", max_abs(pbc,cbc), 2e-11))
    pbc4=ref["director_curvature_b_fourth_order"](pn,h); cbc4=native.director_curvature_b_fourth_order(cn,h)
    results.append(("director_curvature_b4", max_abs(pbc4,cbc4), 3e-11))

    pq=ref["hopf_charge"](pa,pb,h); cq=float(native.hopf_charge(ca,cb,h))
    results.append(("hopf_charge", abs(pq-cq), 2e-12))

    ca_curve=ref["torus_knot_centerline"](2,3,180,2.0,0.7)
    c_curve=native.torus_knot_centerline(2,3,180,2.0,0.7)
    results.append(("torus_knot", max_abs(ca_curve,c_curve), 2e-14))

    pt,pe1,pe2=ref["bishop_frame"](ca_curve)
    ct,ce1,ce2=native.bishop_frame(c_curve)
    results.append(("bishop.tangent", max_abs(pt,ct), 2e-13))
    results.append(("bishop.e1", max_abs(pe1,ce1), 2e-11))

    pwr=ref["polygonal_writhe"](ca_curve); cwr=float(native.polygonal_writhe(c_curve,2))
    results.append(("writhe", abs(pwr-cwr), 2e-11))
    ptw=ref["frame_twist"](pt,pe1); ctw=float(native.frame_twist(ct,ce1))
    results.append(("twist", abs(ptw-ctw), 2e-11))

    f1=hc.hopf_fiber_curve([0,0,1],240); f2=hc.hopf_fiber_curve([1,0,0],240)
    pl=ref["gauss_linking_number"](f1,f2); cl=float(native.gauss_linking_number(f1,f2,1e-14))
    results.append(("gauss_linking", abs(pl-cl), 2e-11))

    rows=[]; ok=True
    for name,err,tol in results:
        passed = err <= tol
        ok &= passed
        rows.append({"name":name,"error":err,"tolerance":tol,"ok":passed})
        print(f"{'PASS' if passed else 'FAIL'} {name:28s} err={err:.3e} tol={tol:.3e}")
    payload={"backend":dict(native.backend_info()),"ok":ok,"checks":rows}
    out=ROOT/"results"/"native_selfcheck.json"; out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(out)
    return 0 if ok else 2

if __name__ == '__main__':
    raise SystemExit(main())
