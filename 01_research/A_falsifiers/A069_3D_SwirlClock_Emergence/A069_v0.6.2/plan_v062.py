"""Offline deterministic v0.6.2 grid and readiness plan (no solver allocation)."""
from __future__ import annotations
import json,sys
from dataclasses import asdict
from pathlib import Path
from a069_v061.campaign_v062 import CASES,screening,resource_forecast
import psutil

cases=[]
for c in CASES.values():
    cases.append({'case':asdict(c),'screening':screening(c.kind,c.n,c.xi,c.box),
                  'resource_forecast':resource_forecast(c.n,psutil.virtual_memory().available)})
out={'schema':'A069-V062-CAMPAIGN-PLAN-1','status':'DEVELOPMENT_NOT_FROZEN_NOT_CERTIFIED',
     'scientific_blindness':'NO PROSPECTIVE PHYSICAL HOLDOUT',
     'framework':'v1.0.9 EXTERNAL TARGET, NOT EXECUTED',
     'cases':cases,'no_reconnection_or_clock_claims':True}
if '--json' in sys.argv:
    print(json.dumps(out,indent=2))
else:
    for x in cases:
        c=x['case'];s=x['screening'];r=x['resource_forecast']
        print(f"{c['case_id']:5} {c['n']:3}^3 xi={c['xi']:.2f} G32={s['status']:28} RAM~{r['conservative_peak_gib']:6.1f}GiB fits_here={r['fits_budget']}")
