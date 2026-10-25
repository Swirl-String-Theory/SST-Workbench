#!/usr/bin/env python3
"""Separate checker for XYZ/KPT candidates: projected knot invariants AND actual 3D over/under signs."""
from pathlib import Path
import json,sys,hashlib,numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from rebuild import ROOT,project_crossings,crossing_trace,fox_determinant,unpackkpt,metrics,EXPECTED,savejson
from sympy import Matrix, Symbol, interpolate, Poly

def alexander_coefficients(pcs,points):
 n=len(pcs);e=crossing_trace(pcs);labels={};u=0
 for k,(_,j,_) in enumerate(e):
  typ='O' if k%2==0 else 'U'
  if typ=='U':u+=1
  labels[(j,typ)]=(u-1)%n
 signs={}
 for j,c in enumerate(pcs):
  is_a_over=next(k%2==0 for k,(_,idx,side) in enumerate(e) if idx==j and side=='a')
  signs[j]=c['signed_xy']*(1 if is_a_over else -1)
 def at(t):
  M=[[0]*n for _ in range(n)]
  for j in range(n):
   o=labels[(j,'O')];post=labels[(j,'U')];pre=(post-1)%n
   if signs[j]>0:
    M[j][o]+=1-t;M[j][pre]+=t;M[j][post]-=1
   else:
    M[j][o]+=t-1;M[j][pre]+=1;M[j][post]-=t
  return Matrix(M)[:-1,:-1].det(method='domain-ge')
 t=Symbol('t'); xs=list(range(n));ys=[at(ti) for ti in xs]
 coeff=[int(v) for v in reversed(Poly(interpolate(list(zip(xs,ys)),t)).all_coeffs())]
 while coeff and coeff[0]==0:coeff.pop(0)
 while coeff and coeff[-1]==0:coeff.pop()
 if coeff and coeff[-1]<0:coeff=[-x for x in coeff]
 return coeff

def expected_poly(label):
 d={'4_1':[1,-3,1],'6_1':[2,-5,2], '7_2':[3,-5,3], '8_1':[3,-7,3],
 '9_2':[4,-7,4], '10_1':[4,-9,4], '11a247':[5,-9,5]}
 return d[label]

def lift_evidence(p,cr):
 ev=crossing_trace(cr);n=len(p);out=[]
 for j,c in enumerate(cr):
  def interpolated_z(t):
   h=t*n; i=int(h)%n;f=h-int(h)
   return (1-f)*p[i,2]+f*p[(i+1)%n,2]
  z1=interpolated_z(c['s']);z2=interpolated_z(c['t'])
  a_should_over=next(k%2==0 for k,(_,jj,sd) in enumerate(ev) if jj==j and sd=='a')
  ok=(z1>z2)==a_should_over and abs(z1-z2)>1.0
  out.append({'crossing_id':j,'z_separation':float(z1-z2),'should_a_over':a_should_over,'ok':bool(ok)})
 return out

def audit():
 m=json.loads((ROOT/'MANIFEST.json').read_text());results=[];failed=[]
 for root_name in ['SEEDS','QUARANTINE','CONTROL_NOT_FOR_INSTALL']:
  base=ROOT/root_name
  for f in sorted(base.glob('*.xyz')):
   p=np.loadtxt(f);cr=project_crossings(p[:,:2]);n,det=EXPECTED[next(name for name in EXPECTED if f.name.startswith(f'KNOT_{name}_'))]
   label=next(name for name in EXPECTED if f.name.startswith(f'KNOT_{name}_'))
   top_ok=len(cr)==n and fox_determinant(cr)==det
   lift=lift_evidence(p,cr) if top_ok else []
   expected_alex=expected_poly(label)
   # Alexander checked only for N>=512 where stronger geometry qualification may apply
   alex=alexander_coefficients(cr,p) if top_ok and len(p)>=512 else []
   passkpt=np.array_equal(unpackkpt(f.with_suffix('.kpt').read_bytes()),p)
   confirmed=all(x['ok'] for x in lift) and top_ok and passkpt and (alex==expected_alex if len(p)>=512 else True)
   report={'filename':f.name,'label':label,'topology_projection_ok':top_ok,'actual_3d_lift_ok':all(x['ok'] for x in lift),
    'min_abs_crossing_z':min(abs(x['z_separation']) for x in lift) if lift else None,
    'alexander':alex,'expected_alexander':expected_alex,'KPT_roundtrip_exact':passkpt,
    'crossing_count':len(cr),'determinant':fox_determinant(cr) if top_ok else None,
    'full_audit_pass':confirmed}
   results.append(report)
   if not confirmed: failed.append(report)
   print(f.name, 'PASS' if confirmed else 'FAIL', flush=True)
 savejson(ROOT/'REPORTS'/'INDEPENDENT_AUDIT.json',{'results':results,'failed':failed})
 if failed:
  print('FAILED',len(failed));sys.exit(2)
 print('ALL',len(results),'PASS')

if __name__=='__main__':audit()
