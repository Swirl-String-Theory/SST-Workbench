"""RoundFolded NearUnknot v0.3.0 -- extended twist ladder.

Source branches:
 m=1 historical Fourier trefoil, m=3/4 TikZ SmoothClasp, others validated 4-plat.
 `11_2` is a legacy/user nickname, not validated standard KnotInfo identifier.
 Geometry is STATIC_CANDIDATE; no automatic physical promotion.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from scipy.interpolate import CubicSpline
from roundfold import fourplat, alexander_coefficients as braid_alexander, fox_determinant
from tikz_roundfold import dense_xyz, assigned_events, alexander
from smooth_clasp import fold_map, resample_periodic_c2, PROFILES
from measure import projection_crossings, lengths
from clearance import global_min_nonlocal
from near_unknot import approximate_curvature, winding_number_xy, params, area_vector
from knotplot_io import encode,decode
ROOT=Path(__file__).resolve().parents[1]
LADDER={1:'3_1',2:'4_1',3:'5_2',4:'6_1',5:'7_2',6:'8_1',7:'9_2',8:'10_1',9:'11cross_T9'}
TICKS=[0,1,8,32,128,512,2048,8192,32000]
PILOT=TICKS[:6]
CLOSE=.20
MAX_DR=.02

def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def expected_polynomial(m):
  k=(m+1)//2 if m%2 else m//2
  return [k, -(2*k-1 if m%2 else 2*k+1), k]

def source(m):
  if m==1:
    t=np.arange(2400)*2*np.pi/2400
    p=np.column_stack([np.cos(t)+1.5*np.cos(2*t),np.sin(t)-1.5*np.sin(2*t),.35*np.sin(3*t)])
    return p,{'type':'historical_2015_Fourier_model_A','source':'user-supplied historical notebook model','original_mirror':'not asserted'}
  if m in (3,4):
    p,c=dense_xyz(LADDER[m],width=.020,height=.10)
    return p,{'type':'TikZ_Hobby_approximation_SmoothClasp_v0.2.3', 'source':c['label'],
              'source_regularization':c['regularization_P10_dy'],'exact_Hobby_equivalence':'UNRESOLVED'}
  p,c=fourplat(m,density=180)
  theoretical=braid_alexander(c)
  if theoretical!=expected_polynomial(m) or fox_determinant(c['traversal'],m+2)!=(2*m+1):
    raise ValueError('4-plat combinatorial mismatch')
  return p,{'type':'4plat_annular_v0.2.0_extended','word':c['word'],
            'source_certification':'independent exported-polyline invariant required',
            'morphology':'ROUND_BRAID_CANDIDATE_not_TikZ_exact'}

def check_actual(p,m):
  n=len(p); records=[]
  for c in projection_crossings(p):
    i,j=int(c['segment_a']),int(c['segment_b']);
    va=p[(i+1)%n]-p[i];vb=p[(j+1)%n]-p[j];xy=np.array([c['x'],c['y']]);
    aa=float(np.dot(xy-p[i,:2],va[:2])/np.dot(va[:2],va[:2]))
    bb=float(np.dot(xy-p[j,:2],vb[:2])/np.dot(vb[:2],vb[:2]))
    sign=int(np.sign(np.linalg.det(np.stack((va[:2],vb[:2])))))
    if not sign:raise ValueError('degenerate crossing')
    records.append({'i':i,'j':j,'s':(i+aa)/n,'t':(j+bb)/n,'signed_xy':sign,'dz':float(c['dz'])})
  if len(records)!=m+2:raise ValueError(f'm={m}: polygon crossings {len(records)} != {m+2}')
  ev,trace=assigned_events(records)
  if not all(((records[j]['dz']>0) if side=='a' else (records[j]['dz']<0)) == (i%2==0) for i,(_,j,side) in enumerate(ev)):
    raise ValueError('3D over/under assignment mismatched')
  pol,det=alexander(trace,records)
  if pol!=expected_polynomial(m) or det !=2*m+1:
    raise ValueError(f'invariant mismatch m={m} -> {(pol,det)} != {(expected_polynomial(m),2*m+1)}')
  return {'crossings':len(records),'alexander_coefficients':pol,'determinant':det,
          'min_crossing_z':min(abs(c['dz']) for c in records),'actual_3d_alternating':True}

def resample_phase_optimized(dense,n):
  """Exact polygonal arc-length resampling + cyclic phase optimization.
  This avoids new small overshoot loops from periodic cubic spline interpolation.
  """
  d=np.linalg.norm(np.roll(dense,-1,axis=0)-dense,axis=1)
  s=np.r_[0.,np.cumsum(d)];L=s[-1]
  best=None
  for off in np.arange(32)/32:
    t=(np.arange(n)+off)*L/n
    candidate=np.column_stack([np.interp(t,s,np.r_[dense[:,j],dense[0,j]]) for j in range(3)])
    e=np.linalg.norm(np.roll(candidate,-1,axis=0)-candidate,axis=1)
    ratio=e.min()/e.mean(); cv=e.std()/e.mean()
    quality=(ratio,-cv)
    if best is None or quality>best[0]:best=(quality,candidate,float(off))
  return best[1],best[2]

def kpc_header(tanf='on'):
 return '\n'.join(['reset all','show backdrop','mode cb','bradius = 0.2','cradius = 0.1',
 'stusplit = 0','dstep = 1','collision fast','energy model MD','close = 0.20','max-dr = 0.02',
 'mechforce = on','elecforce = on','amechforce = off','aelecforce = off',
 'thermalforce = off','bendforce = off','extforce = off','velforce = off','gravity = off','drag = off',
 'spring-length = 1.4','hooke = 1','power = 5','charge = 15','tinc = 15','tanmag = 9',f'tanforce = {tanf}',''])

def make_script(m,n,tier):
 label=LADDER[m];k=f'Tm{m:02d}_{label}';base=f'{k}_BALANCED_N{n:04d}'
 blocks=[];checkpoint_times=PILOT if tier=='PILOT' else TICKS
 for arm in ('ON','OFF'):
  tag=f'{k}_N{n:04d}_{arm}_{tier}'
  rel=f'output/individual/{base}/{base}.kpt'
  b=[f'% {tag}  ATOMIC CHECKPOINTS -- no fitto, no asynchronous go',
     kpc_header('on' if arm=='ON' else 'off'),f'load {rel}',
     'information','length','parameters close','parameters max-dr',f'echo START_{tag}']
  previous=0
  for it in checkpoint_times:
   dest=f'checkpoints/{tier}/{k}/N{n:04d}/TANF_{arm}/i{it:05d}'
   if it: b+= [f'ago {it-previous}']
   b+= [f'echo CHECKPOINT_{tag}_i{it:05d}','safe','length','distance','angle',
         f'save {dest}.k float',f'coords {dest}.xyz']
   if it in (0,512,32000):b+=['dowker','lnknum','acn']
   previous=it
  b.append(f'echo COMPLETE_{tag}')
  blocks+='\n'.join(b).splitlines()
  d=ROOT/'checkpoints'/tier/k/f'N{n:04d}'/f'TANF_{arm}';d.mkdir(parents=True,exist_ok=True)
  (d/'PLACEHOLDER.txt').write_text('This folder is reserved for real KnotPlot outputs.\n')
 scripts=ROOT/'scripts'/tier;scripts.mkdir(parents=True,exist_ok=True)
 (scripts/f'AGO_AB_{tier}_{k}_N{n:04d}.kpc').write_text('\n'.join(blocks)+'\n',encoding='ascii')

def build(m,n,profile):
 label=LADDER[m];raw,src=source(m)
 dense,transform=fold_map(raw,profile)
 if m in (1,3,4):
  pts=resample_periodic_c2(dense,n)
  phase=0.0
 else:
  pts,phase=resample_phase_optimized(dense,n)
  pts*=0.30
 topo=check_actual(pts,m)
 dist=global_min_nonlocal(pts)
 L=lengths(pts);curve=approximate_curvature(pts)
 if dist['distance']<=CLOSE*1.1: raise ValueError(f'{m},N={n} collision clearance failed: {dist["distance"]}')
 if L['edge_cv']>0.05:raise ValueError('arclength CV failed')
 base=f'Tm{m:02d}_{label}_{profile}_N{n:04d}'
 dest=ROOT/'output'/'individual'/base;dest.mkdir(parents=True,exist_ok=True)
 blob=encode([pts]);assert np.array_equal(decode(blob)[0],pts)
 (dest/(base+'.kpt')).write_bytes(blob)
 np.savetxt(dest/(base+'.xyz'),pts,fmt='%.17g')
 rel=f'output/individual/{base}/{base}'
 (dest/(base+'_LOAD.kpc')).write_text(kpc_header()+f'load {rel}.kpt\ninformation\nlength\nparameters close\nparameters max-dr\n',encoding='ascii')
 record={'release':'v0.3.0','identifier':f'T_{m}','knot_name':label,'crossings_expected':m+2,
 'name_note':'11cross_T9 has NO confirmed 11a_N catalogue ID; user shorthand 11_2 not promoted' if m==9 else '',
 'source':src,'profile':profile,'n':n,'resampling_phase_fraction':phase,'fourplat_isotropic_output_factor':0.30 if m not in (1,3,4) else 1.0,'topology_from_exported_xyz':topo,'geometry':{
 'length':L,'clearance':dist,'max_polygonal_curvature':float(curve.max()),'radius_of_curvature_min':1./float(curve.max()),
 'winding_xy':int(winding_number_xy(pts,np.asarray(transform['center_source'])*transform['scale']*12*(0.30 if m not in (1,3,4) else 1.0)))},
 'sha256_kpt':hashlib.sha256(blob).hexdigest(), 'scope':'STATIC_CANDIDATE',
 'gates':{'source_derived_polygon_invariant':'PASS','arclength':'PASS','nonlocal_clearance':'PASS',
  'kpt_roundtrip':'PASS','physical_Euler':'NOT_TESTED','KnotPlot_runtime':'NOT_TESTED',
  'equivalent_TikZ_roundfold_morphology': 'PARTIAL_UNRESOLVED' if m not in (3,4) else 'TIKZ_APPROX',
  'topology_during_go':'UNRESOLVED'}}
 dump(dest/'REPORT.json',record)
 return record

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resolutions',nargs='+',type=int,default=[1024,2048]);ap.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['BALANCED']);ap.add_argument('--only-m',nargs='+',type=int)
 opt=ap.parse_args();ms=opt.only_m or list(LADDER)
 assert all(1<=m<=9 for m in ms)
 results=[]
 for m in ms:
  for profile in opt.profiles:
   for n in opt.resolutions:
    r=build(m,n,profile);results.append(r)
    print(f'm={m} {LADDER[m]} {profile} N{n}: det={r["topology_from_exported_xyz"]["determinant"]} dmin={r["geometry"]["clearance"]["distance"]:.4f} L={r["geometry"]["length"]["total"]:.3f}',flush=True)
 for m in ms:
  if 'BALANCED' in opt.profiles and set([1024,2048]).issubset(set(opt.resolutions)):
   for n in [1024,2048]:
    for tier in ['PILOT','FULL']:make_script(m,n,tier)
 manifest={'version':'v0.3.0','status':'DEVELOPMENT_STATIC_CANDIDATE','m_values':ms,'profiles':opt.profiles,'n_values':opt.resolutions,'count':len(results),'cases':[{k:r[k] for k in ('identifier','knot_name','profile','n')} for r in results],
 'all_static_pass':True,'tanf_armed_scripts':'only when BALANCED N1024/N2048 both built','local_runtime':'NOT_EXECUTED',
 '11_crossing_alias_status':'11_2 shorthand unresolved as catalog nomenclature'}
 dump(ROOT/'LATEST_BUILD.json',manifest)
if __name__=='__main__':main()
