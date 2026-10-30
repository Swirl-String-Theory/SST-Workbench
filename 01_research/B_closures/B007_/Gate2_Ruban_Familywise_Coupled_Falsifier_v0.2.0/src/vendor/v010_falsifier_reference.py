"""One four-stage, audit-tracked Ruban-family screening and coupled Euler falsifier.

Science boundary: reduced-core filament dynamics is NOT 3D Euler; stage 4 is
periodic Fourier Euler with smooth Gaussian vortex cores, not a steady solution.
All experiments operate in dimensionless R0=GammaK=1 units unless declared.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,sys,time,zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
try:
 from numba import njit
except ImportError:
 def njit(*args,**kwargs):
  def wrap(f):return f
  return wrap

ROOT=Path(__file__).resolve().parents[1]
E010=ROOT/'data'/'E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs.zip'
VERSION='v0.1.0'
PREFIX='Gate2_Ruban_Familywise_Coupled_Falsifier'
OUTPUT=ROOT/f'{PREFIX}_{VERSION}-outputs'
LAMBDAS=(3.4,4.,5.,6.)


def sha(data):return hashlib.sha256(data).hexdigest()
def write_json(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def write_csv(path,rows):
 rows=list(rows);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if not rows:return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def read_csv(path):
 with Path(path).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def load_catalog():
 with zipfile.ZipFile(E010) as z:
  root='E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs/'
  idx=json.loads(z.read(root+'FAMILY_INDEX.json'))
  summary=json.loads(z.read(root+'BUILD_SUMMARY.json'))
  source_entries=[]
  for r in idx['seeds']:
   a=z.read(root+r['xyz_path']);b=z.read(root+r['perturbed_xyz_path'])
   if sha(a)!=r['sha256'] or sha(b)!=r['perturbed_sha256']:
    raise ValueError('E010 source seed hash mismatch: '+r['seed_id'])
   pts=np.loadtxt(a.decode().splitlines());per=np.loadtxt(b.decode().splitlines())
   if pts.shape!=(512,3) or per.shape!=(512,3):raise ValueError('Invalid XYZ shapes')
   source_entries.append((r,pts,per))
 return summary,source_entries

def length(P):return float(np.linalg.norm(np.roll(P,-1,axis=0)-P,axis=1).sum())
def resample(P,n):
 P=np.asarray(P,dtype=float);Q=np.concatenate([P,P[:1]])
 edge=np.linalg.norm(np.diff(Q,axis=0),axis=1)
 s=np.concatenate([[0.],np.cumsum(edge)]);t=np.arange(n)*s[-1]/n
 return np.column_stack([np.interp(t,s,Q[:,j]) for j in range(3)])
def geometry(P):
 P=np.asarray(P);N=len(P);edge=np.roll(P,-1,axis=0)-P
 ds=np.linalg.norm(edge,axis=1);L=float(np.sum(ds));rxy=np.hypot(P[:,0],P[:,1])
 # Curvature from symmetric polygon tangent, diagnostic not a certified reach bound.
 prev=P-np.roll(P,1,axis=0);nxt=np.roll(P,-1,axis=0)-P
 tl=prev/np.linalg.norm(prev,axis=1)[:,None];tr=nxt/np.linalg.norm(nxt,axis=1)[:,None]
 c=np.linalg.norm(tr-tl,axis=1)/(0.5*(np.linalg.norm(prev,axis=1)+ds))
 # non-neighbor proxy excludes 10 closest arclength indices, NOT continuum reach.
 tree=cKDTree(P);pairs=tree.query_pairs(r=.7)
 best=np.inf
 for i,j in pairs:
  k=min(abs(i-j),N-abs(i-j))
  if k>10:best=min(best,float(np.linalg.norm(P[i]-P[j])))
 return {'length':L,'min_segment':float(ds.min()),'max_segment':float(ds.max()),
   'segment_cv':float(ds.std()/ds.mean()),'max_curvature_polygon':float(c.max()),
   'radial_min':float(rxy.min()),'radial_max':float(rxy.max()),
   'min_nonlocal_distance_proxy':float(best) if np.isfinite(best) else None,
   'proxy_warning':'Adjacent-index exclusion is not a geometric reach certificate'}

@njit(cache=True)
def induced_velocity(P,sigma,gamma=1.0):
 """Regularized MIDPOINT segment induction; reduced filament model only."""
 N=len(P);out=np.zeros((N,3));sig2=sigma*sigma
 for i in range(N):
  xi,yi,zi=P[i,0],P[i,1],P[i,2]
  for j in range(N):
   h=(j+1)%N
   dx=P[h,0]-P[j,0];dy=P[h,1]-P[j,1];dz=P[h,2]-P[j,2]
   rx=xi-(P[j,0]+0.5*dx);ry=yi-(P[j,1]+0.5*dy);rz=zi-(P[j,2]+0.5*dz)
   inv=(rx*rx+ry*ry+rz*rz+sig2)**(-1.5)
   out[i,0]+=(dy*rz-dz*ry)*inv
   out[i,1]+=(dz*rx-dx*rz)*inv
   out[i,2]+=(dx*ry-dy*rx)*inv
 return out*(gamma/(4*math.pi))

def rigid_fit(P,v):
 X=P[:,0];Y=P[:,1]
 # admissible continuous z-translation and z-axis rotation in FREE SPACE filament model
 t=np.column_stack((np.tile([0.,0.,1.],(len(P),1)).reshape(-1),
                   np.column_stack((-Y,X,np.zeros_like(X))).reshape(-1)))
 y=v.reshape(-1);params=np.linalg.lstsq(t,y,rcond=None)[0]
 residual=(y-t@params).reshape(-1,3)
 return {'U_z':float(params[0]),'Omega_z':float(params[1]),
  'rigid_rms':float(np.sqrt(np.mean(np.sum(residual**2,axis=1)))),
  'velocity_rms':float(np.sqrt(np.mean(np.sum(v*v,axis=1)))),
  'relative_rigid_residual':float(np.linalg.norm(residual)/max(1e-30,np.linalg.norm(v)))}

def scan_filament(P,lambda_,n=192,dt_star=.002):
 A=resample(P,n);sigma=math.exp(-lambda_)
 v=induced_velocity(A,sigma);fit=rigid_fit(A,v)
 # Two RHS evaluations (Heun); Eulerian knot geometry reduced model, not 3D Euler.
 pred=A+dt_star*v
 w=induced_velocity(pred,sigma)
 fin=A+0.5*dt_star*(v+w)
 vf=rigid_fit(fin,induced_velocity(fin,sigma))
 return {'lambda':float(lambda_),'sigma_over_R0':float(sigma),
  'n_filament':n,'dt_star':dt_star,
  **{'initial_'+k:float(vv) for k,vv in fit.items()},
  'final_relative_rigid_residual':vf['relative_rigid_residual'],
  'relative_length_change':float((length(fin)-length(A))/length(A)),
  'numerical_model':'REGULARIZED_MIDPOINT_FILAMENT_HEUN_NOT_FULL_EULER'}

def stage1(entries,out):
 rows=[]
 for info,P,per in entries:
  g=geometry(P)
  rows.append({'seed_id':info['seed_id'],'embedding':info['parametric_embedding'],
   'topology_id':info['topology_id'],'B0':info['B0'],
   'sha256':info['sha256'],'perturbed_sha256':info['perturbed_sha256'],
   'count':len(P),**g,
   'gate':'GEOMETRY_SCREENED_NOT_TOPOLOGY_CERTIFIED'})
 write_csv(out/'G1_geometry_all_84.csv',rows)
 write_json(out/'G1_GATE.json',{'status':'PASS_GEOMETRY_SCHEMA_ONLY',
  'seed_count':len(rows),'family_count':len(set(x['embedding'] for x in rows)),
  'limitations':['No exact reach', 'No sampled-perturbation knot isotopy certificate',
     'No finite-core Euler field qualification'],
  'e010_archive_sha256':sha(E010.read_bytes())})
 return rows

def stage2(entries,out,extended=False):
 rows=[];lambdas=LAMBDAS if extended else (4.,)
 for i,(info,P,pert) in enumerate(entries):
  for lam in lambdas:
   a=scan_filament(P,lam);b=scan_filament(pert,lam)
   rows.append({'seed_id':info['seed_id'],'embedding':info['parametric_embedding'],
    'topology_id':info['topology_id'],'B0':info['B0'],'lambda':lam,
    'nominal_rigid_resid':a['initial_relative_rigid_residual'],
    'perturbed_rigid_resid':b['initial_relative_rigid_residual'],
    'nominal_final_rigid_resid':a['final_relative_rigid_residual'],
    'perturbed_final_rigid_resid':b['final_relative_rigid_residual'],
    'nominal_delta_length':a['relative_length_change'],
    'perturbed_delta_length':b['relative_length_change'],
    'stability_proxy':max(a['initial_relative_rigid_residual'],b['initial_relative_rigid_residual']),
    'method':'FILAMENT_HEUN_NOT_3D_EULER','status':'DEVELOPMENT_SCREEN'})
  if (i+1)%14==0:print(f'  G2: {i+1}/{len(entries)} seeds completed',flush=True)
 write_csv(out/'G2_filament_familywise.csv',rows)
 write_json(out/'G2_GATE.json',{'status':'PASS_SCREEN_EXECUTED_NOT_EQUILIBRIUM',
 'scenario_count':len(rows)*2,'lambda_count':len(lambdas),'seed_count':len(entries),
 'warning':'Regularized filament finite-time proxy does not certify Euler equilibrium or dynamical stability'})
 return rows

def stage3(entries,s2,out):
 byid={info['seed_id']:(info,P,per) for info,P,per in entries}
 # Rank WITHIN each family using Lambda=4 to make 12 like-for-like representatives
 filtered=[r for r in s2 if float(r['lambda'])==4.]
 groups={}
 for row in filtered:groups.setdefault(row['embedding'],[]).append(row)
 winners=[]
 for emb,ls in sorted(groups.items()):
  best=min(ls,key=lambda v:(float(v['stability_proxy']),float(v['B0'])))
  winners.append(best)
 hold=[]
 for winner in winners:
  info,P,pert=byid[winner['seed_id']]
  scores={}
  for n in (128,256,512):
   r=scan_filament(P,4.,n=n)
   scores[str(n)]=r['initial_relative_rigid_residual']
  # Independently evaluate at two point counts NOT used in G2 (n=192).
  delta=abs(scores['512']-scores['256'])
  row={'seed_id':info['seed_id'],'embedding':info['parametric_embedding'],
   'topology_id':info['topology_id'],'B0':info['B0'],
   'g2_stability_proxy':winner['stability_proxy'],
   'n128_shape_resid':scores['128'],'n256_shape_resid':scores['256'],
   'n512_shape_resid':scores['512'],'n256_to_512_absolute_difference':float(delta),
   'qualified_as_full_euler_equilibrium':False,
   'holdout_status':'FILAMENT_DISCRETIZATION_DIAGNOSTIC_ONLY'}
  hold.append(row)
 hold.sort(key=lambda r:(float(r['g2_stability_proxy']),float(r['n256_to_512_absolute_difference'])))
 for rank,row in enumerate(hold,1):row['ranking_by_filament_proxy']=rank
 write_csv(out/'G3_family_winners_holdout.csv',hold)
 write_json(out/'G3_GATE.json',{'status':'PASS_COMPARATIVE_RANKING_ONLY',
  'family_winners':len(hold),'full_euler_equilibria_certified':0,
  'note':'Holdout is independent n, NOT a validated separate physical Biot-Savart method'})
 return hold


def bg_grid_centres(style):
 if style=='single':return [(0.,0.)]
 if style=='triple':return [(.28*math.cos(2*math.pi*j/3),.28*math.sin(2*math.pi*j/3)) for j in range(3)]
 if style=='3x3':return [(i*.36,j*.36) for i in (-1,0,1) for j in (-1,0,1)]
 if style=='5x5':return [(i*.32,j*.32) for i in (-2,-1,0,1,2) for j in (-2,-1,0,1,2)]
 raise ValueError(style)
def bg_curve(base,x,y):
 # Rotate each racetrack so return limb generally runs radially outward.
 direction=np.array([x,y]);radius=np.linalg.norm(direction)
 if radius>1e-9: direction=direction/radius
 else:direction=np.array([1.,0.])
 points=np.empty_like(base)
 points[:,0]=x+direction[0]*base[:,0]
 points[:,1]=y+direction[1]*base[:,0]
 points[:,2]=base[:,2]
 return points

def sampled_component_separation(curves):
 """Conservative vertex-proximity PRECHECK, not an exact segment-to-segment collision proof."""
 best=float('inf');which=None
 for i in range(len(curves)):
  tree=cKDTree(curves[i])
  for j in range(i+1,len(curves)):
   d=float(np.min(tree.query(curves[j])[0]))
   if d<best:best=d;which=[i,j]
 return {'closest_sampled_curve_pair':which,'minimum_sampled_vertex_distance':best,
  'warning':'A sampled-vertex test cannot certify continuum segment separation'}

def evaluate_fixed(g,fields,U,L0):
 rhs=g.rhs(fields)
 dz_hat=1j*g.K[2][None,None,:,:,:]*fields
 RR=g.inv(rhs+U*dz_hat)
 div=[];rms=[]
 for j in range(len(fields)):
  div.append(float(np.max(np.abs(g.inv(1j*np.einsum('ixyz,ixyz->xyz',g.K,fields[j]))))))
  rms.append(float(np.sqrt(np.mean(np.sum(RR[j]**2,axis=0)))))
 return {'max_Rstar_fixedU':max(rms)*L0**4,'max_Dstar':max(div)*L0**3,
         'Rstar_each':[r*L0**4 for r in rms], 'fixed_U_z':float(U)}

def stage4(entries,winners,out,extended=False,heavy=False):
 # No topological ranking promotion. Always evaluate one candidate for each trefoil embedding.
 byid={info['seed_id']:(info,P,per) for info,P,per in entries}
 trefoils=[]
 for family in ('T_2_3','T_3_2'):
  found=next((r for r in winners if r['embedding']==family),None)
  if found:trefoils.append(found)
 if not trefoils:raise RuntimeError('Both required trefoil families missing')
 from reference_euler import EulerGrid,racetrack
 styles=['single','triple'] + (['3x3','5x5'] if extended else [])
 # scientific scope: periodic box only admits exact continuous z-translation, not arbitrary z rotation
 results=[]
 for r in trefoils:
  info,P,_=byid[r['seed_id']];L0=length(P)
  for style in styles:
   record={'seed_id':info['seed_id'],'topology_id':info['topology_id'],
           'B0':info['B0'],'bg_style':style,'bg_count':len(bg_grid_centres(style)),'gamma_bg_each':.05,
           'box':6.,'sigma':.12,'Omega_fit':'NOT_ALLOWED_PERIODIC_CUBE',
           'run_mode':'PERIODIC_FOURIER_GAUSSIAN_FINITE_TIME_NOT_EQUILIBRIUM'}
   def build(n):
    g=EulerGrid(n,6.);knot,kinfo=g.seed(P,sigma=.12)
    rac=racetrack(return_x=1.65,straight_halfheight=1.3,n_straight=48,n_arc=48)
    loops=[];corrections=[]
    for x,y in bg_grid_centres(style):
     W,m=g.seed(bg_curve(rac,x,y),gamma=.05,sigma=.12)
     loops.append(W);corrections.append(m['spectral_projection_correction_ratio'])
    return g,knot,loops,kinfo['spectral_projection_correction_ratio'],max(corrections)
   raw_loop=racetrack(return_x=1.65,straight_halfheight=1.3,n_straight=48,n_arc=48)
   raw_components=[P]+[bg_curve(raw_loop,x,y) for x,y in bg_grid_centres(style)]
   geom_check=sampled_component_separation(raw_components)
   collision_risk=geom_check['minimum_sampled_vertex_distance']<2*.12
   g,k,loops,kc,bc=build(20)
   alone=np.stack([k]);bg=np.stack(loops);all_=np.concatenate((alone,bg),axis=0)
   # independent background-only control; one shared velocity for FULL coupled system
   d_free=g.diagnostics(alone,L0);d_bg=g.diagnostics(bg,L0);d_coup=g.diagnostics(all_,L0)
   U=d_coup['U_z_fitted']
   base=evaluate_fixed(g,all_,U,L0)
   # RK4 evolution of entire coupled vector vorticity for one step at fixed physical dt
   end=g.rk4(all_,.001)
   drift=float(np.linalg.norm((end-all_).ravel())/max(np.linalg.norm(all_.ravel()),1e-30))
   # Controlled fixed-U holdout (do not fit U again at finer mesh).
   hold_n=24 if not heavy else 32
   h,K,backs,kh,bh=build(hold_n)
   hold=evaluate_fixed(h,np.concatenate((np.stack([K]),np.stack(backs))),U,L0)
   record.update({'n_training':20,'n_holdout':hold_n,
    'sampled_component_geometry_preflight':geom_check,
    'sampled_intertube_collision_risk':collision_risk,
    'projection_filter_change_training_max':max(kc,bc),
    'projection_filter_change_holdout_max':max(kh,bh),
    'free_knot_Rstar_fittedU':d_free['component_residuals'][0]['R_star_L0'],
    'bg_alone_Rstar_fittedU':d_bg['max_R_star'],
    'full_coupled_Rstar_fittedU':d_coup['max_R_star'],
    'coupled_vs_free_knot_Rstar_delta':d_coup['component_residuals'][0]['R_star_L0']-d_free['component_residuals'][0]['R_star_L0'],
    'U_train':U,'train_fixedU':base,'holdout_fixedU':hold,
    'relative_field_change_one_RK4_step':drift,
    'stage4_status':'INVALID_GEOMETRY_OVERLAP_RISK' if collision_risk else ('NUMERIC_PRECHECK_FAIL_FILTERING' if max(kc,bc,kh,bh)>.1 else 'UNRESOLVED_NOT_AN_EULER_EQUILIBRIUM')})
   print(f"  G4 {r['seed_id']} {style}: R* {base['max_Rstar_fixedU']:.3g} -> holdout {hold['max_Rstar_fixedU']:.3g}",flush=True)
   results.append(record)
 write_json(out/'G4_coupled_euler_runs.json',results)
 summary=[{'seed_id':r['seed_id'],'background':r['bg_style'],'nbackground':r['bg_count'],
  'U_train':r['U_train'],'Rstar_training':r['train_fixedU']['max_Rstar_fixedU'],
  'Rstar_holdout':r['holdout_fixedU']['max_Rstar_fixedU'],
  'projection_error_training':r['projection_filter_change_training_max'],
  'min_sampled_component_distance':r['sampled_component_geometry_preflight']['minimum_sampled_vertex_distance'],
  'sampled_component_overlap_risk':r['sampled_intertube_collision_risk'],
  'RK4_field_change':r['relative_field_change_one_RK4_step'],
  'gate':r['stage4_status']} for r in results]
 write_csv(out/'G4_coupled_summary.csv',summary)
 write_json(out/'G4_GATE.json',{'status':'UNRESOLVED_NOT_AN_EULER_EQUILIBRIUM',
 'completed_runs':len(results),'background_styles':styles,
 'numeric_preflight_failed_runs':sum(r['stage4_status']=='NUMERIC_PRECHECK_FAIL_FILTERING' for r in results),
 'geometry_overlap_risk_runs':sum(r['sampled_intertube_collision_risk'] for r in results),
 'max_acceptable_projection_filter_change_screen':.1,
 'Omega_z':'FORBIDDEN_CONTINUOUS_SYMMETRY_ON_PERIODIC_CUBE',
 'coupling':'Fully coupled 3D periodic incompressible Euler Fourier evolution; background components live',
 'topology':'No material knot-isotopy certificate: Fourier evolution may introduce spectral mixing; multi-background loops may intersect',
 'holdout':'Fixed U on independent spatial grid, but operator implementation shared',
 'inference':'No zero-residual continuum convergence, no stability certification'})
 return results

def run(extended=False,heavy=False,output=None):
 out=Path(output or (OUTPUT/'extended' if extended else OUTPUT)).resolve();out.mkdir(parents=True,exist_ok=True)
 if E010.resolve()==out.resolve():raise ValueError('Output cannot be input')
 start=time.time()
 print('E010 source archive:',sha(E010.read_bytes()),flush=True)
 summ,entries=load_catalog()
 if len(entries)!=84 or len(set(i['parametric_embedding'] for i,_,_ in entries))!=12:raise ValueError('Unexpected E010 family structure')
 print('G1: geometry of 84 seeds',flush=True);geo=stage1(entries,out)
 print('G2: reduced filament screening, all B per family',flush=True);dyn=stage2(entries,out,extended)
 print('G3: 12 family representatives and independent filament resolution holdout',flush=True);win=stage3(entries,dyn,out)
 print('G4: fully coupled 3D Euler pilot on trefoil winners',flush=True);coupled=stage4(entries,win,out,extended,heavy)
 total={'schema':'GATE2-FOUR-STAGE-LEDGER-1','version':VERSION,'scientific_status':'G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM',
   'implementation_status':'FOUR_STAGES_EXECUTED_WITH_G4_NUMERIC_PREFLIGHT_BLOCKER','G1':len(geo),'G2':len(dyn),'G3':len(win),'G4':len(coupled),
   'published_E010_dynamics_present':False,'metadata_source':'One analytic Ruban family, not 12 independent providers',
   'source_sha256':sha(E010.read_bytes()),
   'caveats':['Filament is a reduced model','3D Euler seed is mollified periodic, not compact support',
      'No genuine relative equilibrium found or claimed','Fixed U only on periodic cube',
      'True topological isotopy during spectral evolution unverified',
      'Holdout shares Euler code; independent code/backend parity still required'],
   'elapsed_seconds':round(time.time()-start,3)}
 write_json(out/'G0_G4_ASSESSMENT.json',total)
 md=f'''# Falsifier report - {PREFIX} {VERSION}\n\nScientific verdict: **G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM**.\n\n## Falsifier question\nCan a fully back-reacting grid of initially parallel vortex cores form a genuine relative Euler equilibrium with a finite-core trefoil?\n\n## Executed gates\n- G1: {len(geo)} geometry seeds; 12 embeddings, 7 B values each. Geometric screening only, no exact reach certificate.\n- G2: {len(dyn)} nominal scans and {len(dyn)} perturbed scans via regularized filament induction. NOT full Euler.\n- G3: {len(win)} independent filament-resolution comparisons at 128,256,512 points; ranking is provisional.\n- G4: {len(coupled)} fully coupled Fourier Euler pilot cases, frozen-U holdout at 24 cubed; periodic Gaussian vorticity; no U/Omega continuum root.\n\n## Primary falsification gates\n1. Full residual for every material vortex component tends to zero under independent spatial refinement, with solution fields converging in sufficient norm. **NOT MET**.\n2. Divergence tends to zero independently of projection and alias-filter artifacts. **PARTIALLY DIAGNOSTIC ONLY**.\n3. Circulation and material knot/link topology preserved for a nonzero finite-core tube. **NOT CERTIFIED**.\n4. Spatial and temporal convergence at common final physical time and independent solvers. **NOT CERTIFIED**.\n5. Periodic boundary/return-limb independence and true z-axis rotational symmetry when Omega is used. **NOT TESTED / OMEGA NOT PERMITTED**.\n\n## Provenance\n- E010 source archive SHA256: `{total['source_sha256']}`\n- All E010 seed and perturbed-shape SHA256 values verified against FAMILY_INDEX.\n- Catalog family ID: UNASSIGNED pending current SST-Workbench catalog audit.\n\n## Scientific interpretation\nNo seed ranking and no decrease in a coarse numerical proxy may be promoted to Euler equilibrium or physical stability.\nThe present stage 4 is an initial direct-dynamics test, **not** an equilibrium optimizer.\n\n## Execution / artifacts\nSource configurations and exact per-seed output records are in G1, G2, G3, G4 files.\nRun tests before producing results and then invoke `run_all.cmd` or `run_all.sh`.\n'''
 (out/'FALSIFIER_REPORT.md').write_text(md,encoding='utf-8')
 # Self-contained outputs integrity excluding ephemeral ledger itself
 manifest={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
 write_json(out/'MANIFEST_SHA256.json',manifest)
 print('FINAL:',total['scientific_status'],f"G1={len(geo)} G2={len(dyn)} G3={len(win)} G4={len(coupled)}",flush=True)
 return total

if __name__=='__main__':
 os.environ.setdefault('NUMBA_NUM_THREADS','1')
 p=argparse.ArgumentParser()
 p.add_argument('--extended',action='store_true',help='All 4 Lambda values + 3x3 and 5x5 background styles')
 p.add_argument('--heavy',action='store_true',help='Stage-4 holdout to n32; may be costly')
 p.add_argument('--out',default=None)
 args=p.parse_args();run(args.extended,args.heavy,args.out)
