from pathlib import Path
import importlib.util, json, math, numpy as np, sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rpo',ROOT/'rpo_falsifier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# unique positive-imag oscillatory pair extraction
J=np.array([[0,-2,0,0],[2,0,0,0],[0,0,0.1,-3],[0,0,3,0.1]],float)
e=m.oscillatory_pairs(J,5)
assert len(e)==2
assert all(x['im']>0 for x in e)
assert abs(sorted(x['period_pred'] for x in e)[0]-2*math.pi/3)<1e-10
# period-aware return gate: excursion then true return
T=1.0
h=[]
for i in range(101):
 t=i/100; rec=0.05*abs(math.sin(math.pi*t/T)); h.append({'t':t,'step':i,'recurrence':rec})
cert={'excursion_min':0.0075,'recurrence_max':0.025,'return_ratio_max':0.5,'return_window_start_periods':0.5}
r=m.return_metrics(h,T,cert)
assert r['excursion_reached'] and r['direct_pass'] and r['best_recurrence']<1e-10
# non-return must fail
h2=[{'t':i/100,'step':i,'recurrence':0.001+0.05*i/100} for i in range(101)]
r2=m.return_metrics(h2,T,cert);assert not r2['direct_pass']
assert m.split_steps(10,3)==[4,3,3]
print('UNIT SELFTEST PASS: eigen-period predictor + excursion/return gate + segment ledger')
