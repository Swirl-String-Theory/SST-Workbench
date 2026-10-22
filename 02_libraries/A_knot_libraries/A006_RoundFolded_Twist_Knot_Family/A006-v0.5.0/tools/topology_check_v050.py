"""Independent projected Alexander determinant & crossing-signature smoke gates.

Not a proof of ambient isotopy or Milnor Borromean invariant.
"""
import sys, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from measure import projection_crossings
from tikz_roundfold import assigned_events,alexander
EXPECTED={'3_1':(3,3),'4_1':(4,5),'5_1':(5,5),'5_2':(5,7),'6_1':(6,9),'7_1':(7,7),
          '7_2':(7,11),'8_1':(8,13),'9_1':(9,9),'9_2':(9,15),'10_1':(10,17),
          '11a247':(11,19),'11a367':(11,11)}

def evaluate(p):
 n=len(p);cr=projection_crossings(p);rr=[]
 for d in cr:
  i,j=int(d['segment_a']),int(d['segment_b'])
  va=p[(i+1)%n]-p[i];vb=p[(j+1)%n]-p[j];xy=np.array([d['x'],d['y']])
  fa=float(np.dot(xy-p[i,:2],va[:2])/np.dot(va[:2],va[:2]));fb=float(np.dot(xy-p[j,:2],vb[:2])/np.dot(vb[:2],vb[:2]))
  sg=int(np.sign(np.linalg.det(np.stack([va[:2],vb[:2]]))))
  rr.append({'i':i,'j':j,'s':(i+fa)/n,'t':(j+fb)/n,'signed_xy':sg,'dz':float(d['dz'])})
 ev,tr=assigned_events(rr);coeff,det=alexander(tr,rr)
 return {'projection_crossings':len(rr),'alexander_determinant':int(det),'coefficients':coeff}

def run():
 result={}
 for label,expected in EXPECTED.items():
  try:
   src=np.loadtxt(ROOT/'Input/original_frozen'/f'{label}_N2048.xyz')
   dst=np.loadtxt(ROOT/'Output/v050/masters'/f'{label}_N2048.xyz')
   a=evaluate(src);b=evaluate(dst)
   status='PASS' if (a['projection_crossings'],a['alexander_determinant'])==(b['projection_crossings'],b['alexander_determinant'])==expected else 'FAIL'
   result[label]={'expected_crossings_determinant':list(expected),'source':a,'v050':b,'status':status}
  except Exception as e:result[label]={'status':'ERROR','error':str(e)}
 result['NOTE']='This tests only the selected projection and Alexander determinant; not full knot equivalence or isotopy.'
 out=ROOT/'Output/v050/TOPOLOGY_PRECHECK.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v.get('status') for k,v in result.items() if isinstance(v,dict)},indent=2))
 return 0 if all(v.get('status')=='PASS' for v in result.values() if isinstance(v,dict)) else 4
if __name__=='__main__':raise SystemExit(run())
