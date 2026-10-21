from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tools'))
from build_v040 import ALL,RES,TORUS,TWIST,torus_poly_check,geometry_report
from knotplot_io import decode
from run_campaign import MODE_KNOTS,HORIZON,ticks,make_script
issues=[];ncheck=0
for knot in ALL:
 for n in RES:
  d=ROOT/'output'/'seeds'/f'{knot}_N{n}'
  try:
   p=np.loadtxt(str(d)+'.xyz');q=decode(Path(str(d)+'.kpt').read_bytes())[0]
   assert p.shape==(n,3) and np.array_equal(p,q)
   rec=json.loads(Path(str(d)+'_REPORT.json').read_text())
   assert rec['geometry']['minimum_nonlocal_centerline_distance']>.22
   if knot in TORUS: assert torus_poly_check(p,TORUS[knot])['determinant']==TORUS[knot]
   else: assert rec['m']==TWIST[knot]
   ncheck+=1
  except Exception as e:issues.append(f'{knot} N{n} : {e}')
scount=0
for mode,ks in MODE_KNOTS.items():
 for knot in ks:
  for n in RES:
   for arm in ['ON','OFF']:
    p=make_script(knot,n,mode,arm)
    s=p.read_text()
    required=ticks(HORIZON[mode]);steps=[b-a for a,b in zip(required,required[1:])]
    if s.count('reset all')!=1 or s.count('ago ')!=len(steps) or any(f'ago {k}\n' not in s for k in steps):issues.append('script invalid '+str(p))
    if 'fitto' in s.split('load ')[0] and not s.split('load ')[0].lstrip().startswith('%'):issues.append('unexpected fitto')
    scount+=1
print(json.dumps({'version':'0.4.0','static_seeds':ncheck,'expected_static_seeds':len(ALL)*len(RES),
   'atomic_scripts':scount,'expected_scripts':sum(len(k)*len(RES)*2 for k in MODE_KNOTS.values()),
   'checkpoints_full':len(ticks(32000)),
   'status':'STATIC_TEST_PASS' if not issues and ncheck==26 else 'FAIL',
   'issues':issues,'KnotPlot_runtime':'NOT_EXECUTED','physical_Euler':'NOT_EXECUTED'},indent=2))
raise SystemExit(0 if not issues and ncheck==26 else 1)
