#!/usr/bin/env python3
"""A006 v0.5.0b controlled KnotPlot force qualification; no native KnotPlot execution.

Primary evidence: the EXACT loaded seed and per-checkpoint XYZ coordinates.
Native KnotPlot data (/I,/N,/l,/g) is retained as diagnostic metadata only.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REL = Path('Output/qualification_v050b')
SEED = Path('Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz')
NAMES = ('BEND_OFF','BEND_1','BEND_10','BEND_100','MECH_ONLY','ELEC_ONLY')
CHECKPOINTS = (0,1,8,32,128)
VERSION = 'A006_FORCE_QUALIFICATION_v0.5.0b'


def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):return sha_bytes(Path(p).read_bytes())
def dump(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def read_components(path, *, strict=False):
 """Read canonical three-block XYZ, or KnotPlot coords with Component n headers."""
 components=[];current=[];headers=[]
 for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
  s=line.strip()
  if re.fullmatch(r'Component\s+\d+\s*:',s,re.I):
   headers.append(s)
   if current:components.append(np.array(current,float));current=[]
   continue
  if not s:
   if current:components.append(np.array(current,float));current=[]
   continue
  fields=s.split()
  if len(fields)!=3:raise ValueError(f'{path}: unexpected line {s[:80]}')
  try:row=[float(x) for x in fields]
  except ValueError as e:raise ValueError(f'{path}: nonnumeric line {s[:80]}') from e
  if not all(math.isfinite(v) for v in row):raise ValueError('Nonfinite coordinates')
  current.append(row)
 if current:components.append(np.array(current,float))
 if len(components)!=3 or min(len(p) for p in components)<30:
  raise ValueError(f'Expected exactly three long components, found {[len(x) for x in components]}')
 if strict and headers:raise ValueError('Canonical input XYZ must be headerless')
 return components

def bev(p):
 p=np.asarray(p,float)
 prev=p-np.roll(p,1,axis=0);nxt=np.roll(p,-1,axis=0)-p
 lp=np.linalg.norm(prev,axis=1);ln=np.linalg.norm(nxt,axis=1)
 if not np.isfinite(lp).all() or np.min(lp)<=1e-12:raise ValueError('Zero/invalid edge')
 dot=(prev*nxt).sum(axis=1)/(lp*ln)
 turn=np.arccos(np.clip(dot,-1,1))
 curv=2*np.sin(turn/2)/((lp+ln)/2)
 return dict(n=len(p), length=float(ln.sum()), median_edge=float(np.median(ln)), min_edge=float(np.min(ln)),
     max_edge=float(np.max(ln)), edge_ratio=float(np.max(ln)/np.min(ln)),
     closure_edge_over_median=float(ln[-1]/np.median(ln)),
     max_turn_deg=float(np.degrees(turn.max())),p99_turn_deg=float(np.degrees(np.percentile(turn,99))),
     max_turn_index=int(np.argmax(turn)),max_curvature=float(curv.max()),
     max_curvature_index=int(np.argmax(curv)),centroid=[float(x) for x in p.mean(axis=0)])

def script_lines(name, seed, n_beads, checkpoints, outdir):
 if name not in NAMES:raise ValueError(name)
 bend = name in ('BEND_1','BEND_10','BEND_100')
 bencon = {'BEND_1':1,'BEND_10':10,'BEND_100':100}.get(name,1)
 elec=name!='MECH_ONLY'
 mech=name!='ELEC_ONLY'
 # Explicitly reset first, then load. Do not use aliases that secretly reset all.
 lines=[f'% {VERSION}; independent force arm {name}; GUI SAFE (NO stop)',
  'reset all',f'load {seed.as_posix()}', 'show backdrop','mode cb',
  'bradius = 0.20','cradius = 0.10',
  'collision fast', 'collision', 'energy model MD',
  'close = 0.20','max-dr = 0.02','dstep = 1','stusplit = 0',
  f'mechforce = {"on" if mech else "off"}', f'elecforce = {"on" if elec else "off"}',
  'amechforce = off','aelecforce = off','thermalforce = off',
  f'bendforce = {"on" if bend else "off"}',f'bencon = {bencon}',
  'extforce = off','velforce = off','gravity = off','drag = off','tanforce = off',
  'tanmag = 9','spring-length = 1.4','hooke = 1','power = 5','charge = 15','tinc = 15']
 if n_beads>3000:
  limit=4000
  while limit<=n_beads:limit*=2
  lines.append(f'go beadlimit {limit}')
 lines.extend(['information','length','safe',
  f'data open {(outdir/"native.csv").as_posix()}',
  'data format "/I,/N,/l,/g"',
  'data header "iteration,nbeads,length,rog"'])
 old=0
 for c in checkpoints:
  if c>old:lines.append(f'ago {c-old}')
  lines.extend([f'echo FORCEQUAL_{name}_CHECKPOINT_{c:07d}',
     'length','rog','safe', 'collision',
     f'coords {(outdir/f"i{c:07d}.xyz").as_posix()}','data'])
  old=c
 lines.extend(['data close', 'collision',f'echo FORCEQUAL_{name}_GUI_FINISHED',
  '% Do not add stop/exit/quit to interactive scripts'])
 return '\n'.join(lines)+'\n'

def settings(name):
 return {'bendforce':name.startswith('BEND_') and name!='BEND_OFF',
         'bencon':{'BEND_10':10,'BEND_100':100}.get(name,1),
         'elecforce':name!='MECH_ONLY','mechforce':name!='ELEC_ONLY',
         'tanforce':False,'collision_request':'fast','close':0.2,'max_dr':0.02,
         'tinc':15,'damping_runtime':'RESET_DEFAULT_NOT_INDEPENDENTLY_VERIFIED','energy_model':'MD','collision_runtime_status':'NOT_CAPTURED'}

def prepare(root, maxiter=128, cps=None):
 if cps is None:cps=[x for x in CHECKPOINTS if x<=maxiter]
 cps=sorted(set(cps+[0,maxiter]))
 if min(cps)<0 or max(cps)>maxiter or maxiter<1:raise ValueError('Invalid checkpoints')
 base=root/REL;seed=root/SEED
 if not seed.is_file():raise FileNotFoundError(f'Missing source seed {seed}')
 components=read_components(seed,strict=True)
 n=sum(map(len,components));hash_=sha_file(seed)
 manifest={'protocol':VERSION,'status':'PREPARED_NOT_EXECUTED','seed':SEED.as_posix(),
           'seed_sha256':hash_,'component_n':[len(p) for p in components],
           'checkpoints':cps,'arms':{},'settings':'explicit in scripts; actual collision readback not certified',
           'not_Euler':True,'not_topology_certified':True}
 for name in NAMES:
  outrel=REL/'runs'/name
  s=script_lines(name,SEED,n,cps,outrel)
  script=root/REL/'scripts'/f'FQ_{name}.kps'
  if script.exists() and script.read_text(encoding='utf-8')!=s:
   raise FileExistsError(f'Refusing to overwrite differing script {script}')
  script.parent.mkdir(parents=True,exist_ok=True);script.write_text(s,encoding='utf-8')
  (root/outrel).mkdir(parents=True,exist_ok=True)
  meta={**settings(name),'seed_sha256':hash_,'n_beads':n,
        'checkpoints':cps,'script_sha256':sha_bytes(s.encode()),'script':(REL/'scripts'/script.name).as_posix()}
  manifest['arms'][name]=meta
  # output paths stay separate; no false runtime data created
  dump(root/outrel/'EXPECTED.json',{'protocol':VERSION,'arm':name,**meta})
 manifestpath=base/'PLAN.json'
 if manifestpath.exists():
  previous=json.loads(manifestpath.read_text(encoding='utf-8'))
  if previous['seed_sha256']!=hash_ or previous['checkpoints']!=cps:
   raise FileExistsError('Plan differs: preserve existing results; use a fresh version or output directory')
 dump(manifestpath,manifest)
 print(f'PREPARED: {len(NAMES)} independent GUI-safe arms; bead counts {manifest["component_n"]}; seed SHA256 {hash_}')
 for name in NAMES:print(f'  read {(REL/"scripts"/f"FQ_{name}.kps").as_posix()}')
 return manifest

def get_native(path):
 if not path.exists():return [],'MISSING'
 if path.stat().st_size==0:return [],'EMPTY'
 try:
  with path.open(newline='',encoding='utf-8-sig') as f:rd=list(csv.DictReader(f))
  if not rd:return [],'NO_RECORDS'
  for r in rd:
   if not set(('iteration','nbeads','length','rog')).issubset(r):return [],'INVALID_HEADER'
   float(r['length']);float(r['rog']);int(r['nbeads']);int(r['iteration'])
  return rd,'READABLE'
 except (ValueError,OSError):return [],'PARSE_ERROR'

def analyze(root):
 planpath=root/REL/'PLAN.json'
 if not planpath.exists():raise FileNotFoundError('First run FORCEQUAL BUILD')
 plan=json.loads(planpath.read_text(encoding='utf-8'))
 if sha_file(root/plan['seed']) != plan['seed_sha256']:
  raise ValueError('Seed changed since plan; refuse to interpret runs')
 outroot=root/REL;rows=[];summary=[];start_hashes={}
 for name in NAMES:
  base=outroot/'runs'/name;expected=plan['arms'][name]
  script=root/expected['script']
  if sha_file(script)!=expected['script_sha256']:
   raise ValueError('Script changed since plan: '+str(script))
  native,status=get_native(base/'native.csv')
  points={}
  for c in plan['checkpoints']:
   fp=base/f'i{c:07d}.xyz'
   if not fp.exists():continue
   v=read_components(fp)
   if [len(p) for p in v]!=plan['component_n']:
    raise ValueError(f'Bead count changed {fp}')
   points[c]=v
   if c==0:start_hashes[name]=[sha_bytes(p.tobytes()) for p in v]
   for i,p in enumerate(v):
    d=bev(p)
    rows.append({'arm':name,'iteration':c,'component':i,'knot_type':('5_2','5_2','6_1')[i],**d})
  nc={int(r['iteration']) for r in native}
  csv_n_ok=all(int(r['nbeads'])==sum(plan['component_n']) for r in native)
  if not csv_n_ok: status='BEAD_COUNT_MISMATCH'
  expected_c=set(plan['checkpoints'])
  st=('NOT_EXECUTED' if not points else ('COMPLETE' if set(points)==expected_c and nc==expected_c and csv_n_ok else 'INCOMPLETE'))
  collision_file=base/'COLLISION_RUNTIME.txt'
  collision_status=collision_file.read_text(encoding='utf-8').strip() if collision_file.exists() else 'UNVERIFIED_NO_CONSOLE_RECORD'
  summary.append({'arm':name,'status':st,'xyz_checkpoints':sorted(points),
                  'native_csv':status,'native_checkpoint_count':len(nc),
                  'collision_runtime':collision_status, 'settings':settings(name)})
 # strict equivalence of initial samples, not just same declared seed
 unique={tuple(dig) for dig in start_hashes.values()}
 start_status='MISSING' if not start_hashes else ('PASS' if len(unique)==1 else 'FAIL')
 if start_status=='FAIL':
  raise ValueError('Different initial checkpoints: invalid controlled A/B comparison')
 ana=outroot/'analysis';ana.mkdir(exist_ok=True)
 fields=['arm','iteration','component','knot_type','n','length','median_edge','min_edge','max_edge','edge_ratio',
         'closure_edge_over_median','max_turn_deg','p99_turn_deg','max_turn_index','max_curvature','max_curvature_index','centroid']
 with (ana/'component_metrics.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(r[k]) if isinstance(r[k],list) else r[k] for k in fields})
 report={'protocol':VERSION,'initial_xyz_equal':start_status,'seed_sha256':plan['seed_sha256'],
         'arms':summary,'report_status':'NO_KNOTPLOT_RUNTIME_DATA' if not rows else 'PARTIAL_OR_COMPLETE',
         'native_semantics':'/l reports final component and /g sums component gyration values in observed build; use XYZ for per-component metrics',
         'collision_certification':'REQUIRES copied runtime console collision/safe output; static request is not runtime proof',
         'physical_dynamics':'NOT_EULER'}
 dump(ana/'AUDIT.json',report)
 md=['# A006 Force Qualification v0.5.0b','',f'Initial XYZ identical: **{start_status}**','',
     '| Arm | Status | XYZ checkpoints | native CSV | Collision runtime |','|---|---|---|---|---|']
 for r in summary:
  md.append(f'| {r["arm"]} | {r["status"]} | {r["xyz_checkpoints"]} | {r["native_csv"]} | {r["collision_runtime"]} |')
 md+=['','Collision verification must use the actual `collision` and `safe` command output, not an inferred state.',
      'There is no Euler or Borromean-topology certification from these experiments.']
 (ana/'AUDIT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
 # All graphs are generated ONLY from actually observed checkpoint XYZ.
 if rows:
  try:
   import matplotlib
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt
   for component in range(3):
    for key,ylabel in [('max_turn_deg','Maximum turning angle (degrees)'),('min_edge','Minimum edge length (KnotPlot units)')]:
     fig,ax=plt.subplots(figsize=(8,4.4))
     for name in NAMES:
      subset=sorted((r for r in rows if r['arm']==name and r['component']==component),key=lambda r:r['iteration'])
      if subset:ax.plot([r['iteration'] for r in subset],[r[key] for r in subset],marker='o',label=name)
     ax.set(xlabel='Cumulative KnotPlot iterations',ylabel=ylabel,title=f'Component {component}: {ylabel}')
     ax.grid(alpha=.25)
     ax.legend(fontsize=8)
     fig.tight_layout()
     fig.savefig(ana/f'component{component}_{key}.png',dpi=150)
     plt.close(fig)
  except ImportError:
   print('NOTE: matplotlib unavailable; CSV and JSON analyses generated without charts')
 print(f'ANALYSIS: {len(rows)} per-component records; start={start_status}; see {(REL/"analysis"/"AUDIT.md").as_posix()}')
 return report

def selftest(root):
 p=root/SEED
 if not p.exists():raise FileNotFoundError(p)
 xyz=read_components(p,strict=True);assert len(xyz)==3
 for name in NAMES:
  s=script_lines(name,SEED,sum(map(len,xyz)),CHECKPOINTS,REL/'runs'/name)
  assert 'go beadlimit 4000' in s and 'data format "/I,/N,/l,/g"' in s
  assert 'data close' in s and '\nstop\n' not in s
  assert s.index('load ')<s.index('go beadlimit')<s.index('ago 1')
  assert s.count('coords ') ==len(CHECKPOINTS)
  assert s.count('\ndata\n')==len(CHECKPOINTS)
  assert '\ncollision\n' in s
 for n in [31,32,33]:
  t=np.linspace(0,2*np.pi,n,endpoint=False);q=np.column_stack((np.cos(t),np.sin(t),np.zeros_like(t)))
  assert bev(q)['max_turn_deg']<15
 print('PASS: 6 arms; shared seed; single changed force family; atomic checkpoints; beadlimit; CSV4; GUI-safe; geometry parser')

def main():
 ap=argparse.ArgumentParser(description='A006 v0.5.0b force-isolation GUI-safe qualification')
 ap.add_argument('action',choices=('TEST','PLAN','BUILD','ANALYZE'),type=str.upper)
 ap.add_argument('--maxIteration',type=int,default=128)
 ap.add_argument('--checkpoints',type=str,default='0,1,8,32,128')
 ap.add_argument('--root',type=Path,default=ROOT)
 a=ap.parse_args();root=a.root.resolve()
 if a.action=='TEST':return selftest(root)
 cs=sorted({int(x.strip()) for x in a.checkpoints.split(',') if x.strip() and int(x.strip())<=a.maxIteration})
 if a.action=='PLAN':
  print(f'PLAN ONLY: {NAMES}, seed={SEED.as_posix()}, checkpoints {sorted(set(cs+[0,a.maxIteration]))}; no KnotPlot dynamics')
 elif a.action=='BUILD':prepare(root,maxiter=a.maxIteration,cps=cs)
 elif a.action=='ANALYZE':analyze(root)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,AssertionError) as e:print(f'FAIL: {e}',file=sys.stderr);sys.exit(2)
