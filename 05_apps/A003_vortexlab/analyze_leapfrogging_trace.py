#!/usr/bin/env python3
import argparse,csv,json,math
from pathlib import Path

def analyze(path, min_dz=0.0002):
    with Path(path).open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)<3: raise ValueError('Need >=3 time-ordered measurements')
    data=[]
    for r in rows:
        x={k:float(r[k]) for k in ('t','RA','RB','zA','zB')}
        if not all(math.isfinite(v) for v in x.values()):raise ValueError('nonfinite sample')
        if data and x['t']<=data[-1]['t']:raise ValueError('non-monotonic time axis')
        data.append(x)
    first=0;events=[]
    for r in data:
        d=r['zB']-r['zA'];s=1 if d>min_dz else -1 if d < -min_dz else 0
        if s and first and s!=first:
            events.append({'t_approx_s':r['t'],'zA_m':r['zA'],'zB_m':r['zB'],'R_A_m':r['RA'],'R_B_m':r['RB']})
        if s:first=s
    return {
        'schema':'leapfrog-trajectory-diagnostic/1.0',
        'samples':len(data), 't_start_s':data[0]['t'],'t_end_s':data[-1]['t'],
        'axial_order_swaps':len(events),'events':events,
        'radial_exchange_sign_swaps':sum((a['RA']-a['RB'])*(b['RA']-b['RB'])<0 for a,b in zip(data,data[1:])),
        'status':'ORDER_SWAPS_OBSERVED_NOT_STABILITY_CERTIFIED' if events else 'NO_ORDER_SWAPS_OBSERVED',
        'qualification':'Requires spatial/temporal/finite-core convergence, sustained exchange and conservation diagnostics.'
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('trace_csv');ap.add_argument('--hysteresis-m',type=float,default=.0002)
    a=ap.parse_args();print(json.dumps(analyze(a.trace_csv,a.hysteresis_m),indent=2))
