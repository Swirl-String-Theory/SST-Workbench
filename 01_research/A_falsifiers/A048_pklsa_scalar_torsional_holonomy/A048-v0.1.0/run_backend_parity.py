from pathlib import Path
import json, os, sys
import numpy as np
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'
try:
    import torsion_native
except Exception as e:
    print(f'native unavailable: {e}', file=sys.stderr); raise
from sst_torsion.models import kelvin_omega,torsion_omega,power_law_fit
k=np.arange(1.0,11.0)
checks={}
for name,py,nat in [
 ('kelvin',kelvin_omega(k,0.17),np.asarray(torsion_native.kelvin_omega(k,0.17))),
 ('torsion',torsion_omega(k,1.1,0.2),np.asarray(torsion_native.torsion_omega(k,1.1,0.2)))]:
    checks[name]=float(np.max(np.abs(py-nat)))
sp=float(torsion_native.loglog_slope(k,kelvin_omega(k,0.17)))
checks['slope_abs_error']=abs(sp-power_law_fit(k,kelvin_omega(k,0.17))['p'])
passed=max(checks.values())<1e-12
summary={'passed':passed,'checks':checks}
(OUT/'BLIND'/'backend_parity_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
if not passed: raise SystemExit(2)
