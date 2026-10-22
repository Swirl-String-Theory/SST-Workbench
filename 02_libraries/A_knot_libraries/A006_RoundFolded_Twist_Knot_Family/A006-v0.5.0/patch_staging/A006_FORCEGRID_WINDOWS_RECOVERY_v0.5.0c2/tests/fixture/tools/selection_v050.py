#!/usr/bin/env python3
"""A006 v0.4.3b cumulative: selector, mirror, atomic KnotPlot campaigns and symmetry audit.

Additive extension. Neither source seeds nor existing runs are overwritten.
Mirroring is a 3-D reflection; no isotopy/achirality claims follow from it.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, math, os, re, subprocess, sys, shutil
from dataclasses import dataclass
from pathlib import Path
import numpy as np

KNOTS = ('3_1','4_1','5_1','5_2','6_1','7_1','7_2','8_1','9_1','9_2','10_1','11a247','11a367')
ALIASES = {'11_1':'11a367','11_2':'11a247','K11a367':'11a367','K11a247':'11a247'}
LINKS = ('5_5_6','6_6_5')
PROFILES = ('FLAT','SOFT','BALANCED','TIGHT')
EARLY=(0,1,8,32,128,512)
# Fremlin's table is an external topological classification, not something obtained
# from the new numerical experiments. Only annotate values actually listed there.
REFERENCE_SYMMETRY = {
 '3_1':('CHIRAL','REVERSIBLE'), '4_1':('AMPHICHIRAL','REVERSIBLE'),
 '5_1':('CHIRAL','REVERSIBLE'),'5_2':('CHIRAL','REVERSIBLE'),
 '6_1':('CHIRAL','REVERSIBLE'),'7_1':('CHIRAL','REVERSIBLE'),
 '7_2':('CHIRAL','REVERSIBLE'),'8_1':('CHIRAL','REVERSIBLE'),
}
PARAMS = ('reset all','show backdrop','mode cb','bradius = 0.20','cradius = 0.10',
 'collision fast','energy model MD','close = 0.20','max-dr = 0.02','dstep = 1',
 'stusplit = 0','mechforce = on','elecforce = on','amechforce = off',
 'aelecforce = off','thermalforce = off','bendforce = off','extforce = off',
 'velforce = off','gravity = off','drag = off','tanmag = 9','spring-length = 1.4',
 'hooke = 1','power = 5','charge = 15','tinc = 15')

# All generated files are contained here, without modifying old releases.
REL = Path('Output/v050')

def hbytes(b):return hashlib.sha256(b).hexdigest()
def hfile(p):return hbytes(Path(p).read_bytes())
def dump(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def canonical_filesystem_dir(root,*names):
 """Support uploaded archives containing Windows-case Output/Seeds."""
 cur=Path(root)
 for name in names:
  target=cur/name
  if target.exists():cur=target;continue
  matches=[a for a in cur.iterdir() if a.is_dir() and a.name.casefold()==name.casefold()] if cur.is_dir() else []
  if not matches:raise FileNotFoundError(f'Missing folder {name} under {cur}')
  cur=matches[0]
 return cur

def select_names(raw,options):
 if raw is None or str(raw).strip().upper() in ('NONE','-',''):return []
 if str(raw).strip().upper()=='ALL':return list(options)
 out=[]
 for s in str(raw).split(','):
  s=s.strip();s=ALIASES.get(s,s)
  if s not in options:raise ValueError(f'Unknown selection {s}; options: {options}')
  if s not in out:out.append(s)
 return out

def bead_grid(lo,hi):
 if lo<32 or hi<lo or hi>8192:raise ValueError('Require 32<=minN<=maxN<=8192')
 # Native A006 matrix uses binary refinements; do not silently add an extra resolution.
 if lo & (lo-1) or hi & (hi-1):raise ValueError('minN and maxN must be powers of two; use --beads=... otherwise')
 result=[];i=lo
 while i<=hi:result.append(i);i*=2
 return result

def checkpoints(maxiter,every,include_early=True):
 if maxiter<1 or maxiter>1_000_000 or every<1:raise ValueError('Invalid iteration horizon or checkpoint interval')
 ints={0,maxiter}|{t for t in range(every,maxiter+1,every)}
 if include_early:ints.update(t for t in EARLY if t<=maxiter)
 return sorted(ints)

def edge_stats(points):
 edges=np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1)
 if len(points)<32 or not np.isfinite(points).all() or not np.isfinite(edges).all() or np.min(edges)<=1e-12:
  raise ValueError('Degenerate or non-finite closed polygon')
 return {'n':len(points),'length':float(edges.sum()),'median_edge':float(np.median(edges)),
         'min_over_median':float(edges.min()/np.median(edges)),
         'max_over_median':float(edges.max()/np.median(edges)),
         'closing_edge_over_median':float(edges[-1]/np.median(edges))}

def sample_closed(p,n):
 """Periodic piecewise-linear resample, cyclic endpoint and seam included."""
 p=np.asarray(p,float);seg=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
 if not np.isfinite(seg).all() or np.min(seg)<1.e-12:raise ValueError('Degenerate source')
 s=np.r_[0,np.cumsum(seg)];ext=np.vstack([p,p[0]]);best=None
 for phase in np.arange(32)/32:
  targets=(np.arange(n)+phase)*s[-1]/n
  q=np.column_stack([np.interp(targets,s,ext[:,k]) for k in range(3)])
  st=edge_stats(q);score=st['min_over_median']
  if best is None or score>best[0]:best=(score,q,phase)
 return best[1],best[2]

def components_from_xyz(path,expected=None,strict=True):
 txt=Path(path).read_text(encoding='utf-8-sig');rows=txt.splitlines()
 if strict and (not txt.endswith('\n') or txt.endswith('\n\n')):raise ValueError('Invalid trailing newline')
 groups=[];group=[]
 for ln in rows:
  if not ln.strip():
   if not group:raise ValueError('Unexpected blank line or repeated separator')
   groups.append(group);group=[];continue
  parts=ln.split()
  if len(parts)!=3:raise ValueError(f'Header or invalid xyz row: {ln[:100]}')
  xyz=list(map(float,parts))
  if not all(map(math.isfinite,xyz)):raise ValueError('Nonfinite XYZ')
  group.append(xyz)
 if group:groups.append(group)
 if len(groups)!=3:raise ValueError(f'Expected exactly 3 numeric blocks, got {len(groups)}')
 a=[np.asarray(b,float) for b in groups]
 if expected is not None and [len(z) for z in a]!=list(expected):raise ValueError('Unexpected point count in multicomponent xyz')
 for p in a:edge_stats(p)
 return a

def write_xyz3(path,parts):
 txt='\n\n'.join('\n'.join('%.17g %.17g %.17g'%tuple(pt) for pt in p) for p in parts)+'\n'
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  if path.read_text(encoding='ascii')!=txt:raise FileExistsError(f'Conflicting prior generated geometry: {path}')
 else:path.write_text(txt,encoding='ascii',newline='\n')
 assert len(components_from_xyz(path))==3
 return path

def reflected(parts):
 return [np.column_stack((-p[:,0],p[:,1],p[:,2])) for p in parts]

def legacy_output_subdir(root,subdir):
 root=Path(root)
 for casing in ('Output','output'):
  base=root/casing
  if not base.is_dir():continue
  candidates=[p for p in base.iterdir() if p.is_dir() and p.name.casefold()==subdir.casefold()]
  if len(candidates)==1:return candidates[0]
 return canonical_filesystem_dir(root,'output',subdir)

def nearest_matching_link(root,link,profile,n,scale):
 original=legacy_output_subdir(root,'borromean')
 code=link.replace('_','_')
 stem=f'Borromean_{code}_{profile}_MIN{n:04d}_S{int(round(scale*1000)):04d}_'
 found=[p for p in original.glob('*.xyz') if p.name.startswith(stem) and re.search(r'_v042[cd]\.xyz$',p.name)]
 return sorted(found,key=lambda p:p.name,reverse=True)[0] if found else None

def source_seed(root,knot,n):
 seeds=legacy_output_subdir(root,'seeds')
 # Prefer frozen source at exact resolution; 256/512 derived from 2048.
 target=seeds/f'{knot}_N{n}.xyz'
 if target.exists():return target
 higher=seeds/f'{knot}_N2048.xyz'
 if not higher.is_file():higher=seeds/f'{knot}_N1024.xyz'
 if not higher.is_file():raise FileNotFoundError(f'Missing frozen A006 source {knot}')
 return higher

def existing_seed_array(path):
 p=np.loadtxt(path);p=np.asarray(p,float)
 if p.ndim!=2 or p.shape[1]!=3:raise ValueError(f'Invalid source {path}')
 edge_stats(p)
 return p

@dataclass(frozen=True)
class Case:
 kind:str
 label:str
 n:int
 orientation:str
 arm:str
 profile:str=''
 def slug(self):
  return f'{self.kind}_{self.label}_{self.profile+"_" if self.profile else ""}N{self.n:04d}_{self.orientation}_TANF_{self.arm}'

def expected_cases(knots,links,profiles,ns,mirrors,arms):
 return ([Case('KNOT',k,n,mi,arm) for k in knots for n in ns for mi in mirrors for arm in arms]
         +[Case('LINK',l,n,mi,arm,profile) for l in links for profile in profiles for n in ns for mi in mirrors for arm in arms])

def build_geometry(root,case,scale,closure_policy='FIXED61',closure_angles=(0.,0.,180.),generate_missing_link=True):
 """Build NEW v0.5.0 geometry, cache same geometry across TANF arms."""
 from geometry_v050 import individual,link,sha
 from orientation_v043b import orientation_key
 geom=Path(root)/REL/'geometry'
 if case.kind=='KNOT':
  name=f'KNOT_{case.label}_N{case.n:04d}_{case.orientation}'
 else:
  name=f'LINK_{case.label}_{case.profile}_N{case.n:04d}_{case.orientation}_{orientation_key(closure_policy,closure_angles)}'
 output=geom/(name+'.xyz')
 if output.exists() and output.with_suffix('.json').exists():
  raw=json.loads(output.with_suffix('.json').read_text())
  if case.kind=='KNOT':parts=[np.loadtxt(output)]
  else:parts=components_from_xyz(output)
 else:
  if case.kind=='KNOT':output,p=individual(case.label,case.n,case.orientation=='MIRROR');parts=[p]
  else:
   output,parts=link(case.label,case.profile,case.n,scale,closure_policy,case.orientation=='MIRROR',closure_angles)
  raw=json.loads(output.with_suffix('.json').read_text())
 cp={'policy':closure_policy,'angles_deg':raw['orientation']['angles_deg']} if case.kind=='LINK' else None
 report={'status':raw['status'],'kind':case.kind,'label':case.label,'profile':case.profile,
  'n_requested':case.n,'n_actual':[len(x) for x in parts],
  'orientation':case.orientation,'reflection':'(x,y,z)->(-x,y,z)' if case.orientation=='MIRROR' else 'identity',
  'geometry_sha256':sha(output),'bead_statistics':[edge_stats(x) for x in parts],
  'closure_placement':cp,'isotopy_status':'UNRESOLVED','milnor_status':'UNRESOLVED','source':str(output.relative_to(root))}
 return output,report

def settings_for(case):
 return PARAMS+(f'tanforce = {case.arm.lower()}',)

def required_beadlimit(actual):
 """Return command limit from actual loaded beads, not requested MIN N.

 KnotPlot defaults to 3000. Use an explicit, deterministic safe limit of
 4000, 8000, 16000, ... whenever the total exceeds 3000. The limit is
 a runtime allocation setting; it does not change coordinates or bead counts.
 """
 total=sum(int(n) for n in actual)
 if total<1 or any(int(n)<1 for n in actual):
  raise ValueError('Invalid bead counts for KnotPlot beadlimit')
 if total<=3000:return None
 limit=4000
 while limit<=total:limit*=2
 return limit

def protocol(root,case,geometry,ticks,actual):
 limit=required_beadlimit(actual)
 conf={'protocol':'A006_SELECTOR_v0.5.0a_FIXED61_REBUILD',
       'case':case.__dict__,'geometry_sha256':hfile(geometry),
       'settings':settings_for(case),'ticks':ticks,'atomic':'ago','force_model':'KnotPlot MD, NOT Euler','run_family':'NEW_v050a_NONREUSABLE'}
 if limit is not None:conf.update({'loaded_bead_count':sum(map(int,actual)),'go_beadlimit':limit})
 return hbytes(json.dumps(conf,sort_keys=True).encode())

def script_and_dir(root,case,geometry,ticks,actual):
 root=Path(root);key=protocol(root,case,geometry,ticks,actual);dir=root/REL/'runs'/case.slug()/key[:16]
 dir.mkdir(parents=True,exist_ok=True)
 src=geometry.relative_to(root).as_posix()
 rel=dir.relative_to(root).as_posix()
 limit=required_beadlimit(actual)
 lines=['% AUTO-GENERATED A006 selection v0.5.0, requires KnotPlot atomic ago' if limit is None
        else '% AUTO-GENERATED A006 selection v0.5.0; KnotPlot atomic ago',*settings_for(case),
        f'load {src}']
 if limit is not None:lines.append(f'go beadlimit {limit}')
 lines.extend(['information','length','safe',
        f'data open {rel}/native.csv','data format "/I,/N,/l,/g,/s"',
        'data header "iteration,nbeads,length,rog,safe"'])
 prev=0
 for it in ticks:
  if it:lines.append(f'ago {it-prev}')
  lines.extend([f'echo A006_CHECKPOINT_{it:07d}','length','rog','safe',
      f'coords {rel}/i{it:07d}.xyz','data'])
  if it in (0,ticks[-1]):lines.extend(['lnknum'] if case.kind=='LINK' else ['alex -1'])
  prev=it
 lines.extend(['data close',f'echo A006_COMPLETE_{case.slug()}','stop'])
 name=dir/'campaign.kpc'
 text='\n'.join(lines)+'\n'
 if name.exists() and name.read_text('ascii')!=text:raise FileExistsError('Conflicting campaign script: '+str(name))
 if not name.exists():name.write_text(text,encoding='ascii',newline='\n')
 return name,dir,key

def check_snapshot(path,case,actual):
 path=Path(path)
 if not path.is_file() or not path.stat().st_size:return False
 try:
  lines=path.read_text(encoding='utf-8-sig').splitlines()
  # KnotPlot's own coords format may include Component # headers.
  a=[];group=[]
  for line in lines:
   v=line.strip()
   if not v or re.fullmatch(r'(?:Comp(?:onent)?\s*#?\d+:)',v,re.I):
    if group:a.append(group);group=[]
    continue
   row=list(map(float,v.split()))
   if len(row)!=3 or not all(map(math.isfinite,row)):return False
   group.append(row)
  if group:a.append(group)
  if [len(b) for b in a]!=actual:return False
  return a
 except Exception:return False

def read_native_csv(path,ticks):
 with Path(path).open(encoding='utf-8-sig',newline='') as fh:
  reader=csv.DictReader(fh); cols=[v.strip() for v in (reader.fieldnames or [])]
  if cols!=['iteration','nbeads','length','rog','safe']:raise ValueError(f'Bad CSV schema {cols}')
  data=[]
  for v in reader:
   values={k:float(x) for k,x in v.items()}
   if not all(map(math.isfinite,values.values())):raise ValueError('Nonfinite CSV')
   data.append(values)
 if [round(v['iteration']) for v in data]!=ticks:return None
 return data

def verify_run(dir,case,ticks,actual):
 snapshots=[]
 for t in ticks:
  a=check_snapshot(dir/f'i{t:07d}.xyz',case,actual)
  if a is False:return None
  snapshots.append(a)
 if all(np.array_equal(x,y) for x,y in zip(snapshots[0],snapshots[-1])):return None
 csvpath=dir/'native.csv'
 if not csvpath.is_file():return None
 try:data=read_native_csv(csvpath,ticks)
 except Exception:return None
 return data

def locate_executable(root):
 vals=[]
 if os.environ.get('KNOTPLOT_EXE'):vals.append(Path(os.environ['KNOTPLOT_EXE'].strip('"')))
 p=Path(root)/'config'/'knotplot_exe.txt'
 if p.exists():vals.append(Path(p.read_text().strip().strip('"')))
 for x in vals:
  if x.is_file():return x
 raise FileNotFoundError('Set KNOTPLOT_EXE or config/knotplot_exe.txt to KnotPlot.exe')

def headless_preflight(root,exe):
 p=Path(root)/'preflight'/'PREFLIGHT_PASS.json'
 if not p.is_file():raise RuntimeError('Run legacy run_all.cmd PREFLIGHT first; no independent KnotPlot headless certification')
 d=json.loads(p.read_text())
 if (d.get('status')!='LOCAL_ATOMIC_ONE_STEP_PASS' or Path(d.get('exe',''))!=exe or
     d.get('exe_size')!=exe.stat().st_size or d.get('exe_mtime_ns')!=exe.stat().st_mtime_ns):
  raise RuntimeError('Headless preflight no longer matches KnotPlot.exe; repeat PREFLIGHT')

def run_one(root,case,dir,script,key,ticks,actual,timeout):
 done=dir/'DONE.json'
 if done.exists():
  old=json.loads(done.read_text());rows=verify_run(dir,case,ticks,actual)
  if old.get('protocol_sha256')==key and old.get('status')=='RUNTIME_CHECKPOINTS_COMPLETE' and rows is not None:return 'SKIP_VERIFIED'
  raise RuntimeError('DONE file conflicts with new protocol or invalid outputs; manual audit required: '+str(done))
 if any(dir.glob('i*.xyz')) or (dir/'native.csv').exists():
  raise RuntimeError('Partial output exists without certified DONE; refuse overwrite: '+str(dir))
 exe=locate_executable(root);headless_preflight(root,exe)
 cmd=[str(exe),'-stdin','-nographics']; relative=script.relative_to(root).as_posix()
 with (dir/'stdout.log').open('wb') as log:
  cp=subprocess.run(cmd,input=f'read {relative}\n'.encode('ascii'),cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
 if cp.returncode:raise RuntimeError(f'KnotPlot runtime failed exit={cp.returncode}; see {dir}/stdout.log')
 rows=verify_run(dir,case,ticks,actual)
 if rows is None:raise RuntimeError(f'Incomplete/invalid checkpoints or CSV; see {dir}')
 dump(done,{'status':'RUNTIME_CHECKPOINTS_COMPLETE','release':'v0.5.0','protocol_sha256':key,'kind':case.kind,
            'label':case.label,'profile':case.profile,'resolution':case.n,'orientation':case.orientation,
            'tanf':case.arm,'max_iteration':ticks[-1],'checkpoints':ticks,
            'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'claim':'KnotPlot MD coordinates, not Euler; topology NOT CERTIFIED'})
 return 'COMPLETE'

def orientation_key_for_report(d):
 cp=d.get('closure_placement')
 if not cp:return 'NOT_APPLICABLE'
 return cp['policy']+'_'+','.join(str(v) for v in cp['angles_deg'])

def geometry_pair_csv(root):
 """Compare original/mirror static geometry in this v0.5.0 geometry folder.
 The generator's JSON schema is deliberately independent of older v043 JSON.
 """
 from geometry_v050 import sha
 geom=Path(root)/REL/'geometry';entries={}
 for j in geom.glob('*.json'):
  d=json.loads(j.read_text());name=j.stem
  orient=('MIRROR' if '_MIRROR' in name else 'ORIG' if '_ORIG' in name else None)
  if orient is None:continue
  key=name.replace('_MIRROR','_ORIG')
  entries.setdefault(key,{})[orient]=(d,j.with_suffix('.xyz'))
 rows=[]
 for key,pair in sorted(entries.items()):
  if not {'ORIG','MIRROR'}<=set(pair):continue
  a,afile=pair['ORIG'];b,bfile=pair['MIRROR']
  if a['kind']=='KNOT':
   kn=a['name'].removeprefix('KNOT_').split('_N')[0]
   profile=''
  else:
   kn=a['composition'];profile=a['profile']
  n=a.get('n',a.get('minN'))
  statdiff=max(abs(x['length']-y['length']) for x,y in zip(a['metrics'],b['metrics']))
  # Reflected coordinates must match exactly to within float text precision.
  import numpy as np
  from selection_v050 import components_from_xyz
  if a['kind']=='KNOT':pa=[np.loadtxt(afile)];pb=[np.loadtxt(bfile)]
  else:pa=components_from_xyz(afile);pb=components_from_xyz(bfile)
  err=max(float(np.max(np.abs(np.column_stack((-p[:,0],p[:,1],p[:,2]))-q))) for p,q in zip(pa,pb))
  known=REFERENCE_SYMMETRY.get(kn,('NOT_IN_REFERENCE','NOT_IN_REFERENCE'))
  rows.append({'kind':a['kind'],'name':kn,'profile':profile,'N':n,
   'closure_signature':'CPCENTER' if a['kind']=='LINK' else 'NA',
   'parity_mirror_verified_from_generation':err<=1e-9,
   'mirror_max_coordinate_error':err,'length_delta_max':statdiff,
   'mirror_reference_chirality':known[0],'mirror_reference_reversibility':known[1],
   'isotopy_equivalence':'UNRESOLVED','dynamics_parity':'UNRESOLVED'})
 dst=Path(root)/REL/'symmetry_geometry.csv';dst.parent.mkdir(parents=True,exist_ok=True)
 import csv
 cols=['kind','name','profile','N','closure_signature','parity_mirror_verified_from_generation',
       'mirror_max_coordinate_error','length_delta_max','mirror_reference_chirality',
       'mirror_reference_reversibility','isotopy_equivalence','dynamics_parity']
 with dst.open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows(rows)
 return len(rows)

def parse(argv=None):
 # Accept user's original 'minN=256' spellings as well as '--minN=256'.
 argv=sys.argv[1:] if argv is None else list(argv)
 argv=[(''.join(['--',s]) if re.match(r'^(minN|maxN|maxIteration|checkpointsEvery|mirrored|knots|links|tanf|linkProfiles|linkScale|closurePolicy|closureAngles)=',s,re.I) else s) for s in argv]
 argv=[v for v in argv if v.upper() not in ('SELECT','RUN')]
 p=argparse.ArgumentParser(description='A006 v0.5.0 clean campaign selection and closure qualification')
 p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
 p.add_argument('--knots',default='NONE');p.add_argument('--links',default='NONE')
 p.add_argument('--minN',type=int,default=256);p.add_argument('--maxN',type=int,default=2048)
 p.add_argument('--beads',default=None,help='Explicit comma list instead of power-of-two grid')
 p.add_argument('--maxIteration',type=int,default=8000);p.add_argument('--checkpointsEvery',type=int,default=500)
 p.add_argument('--mirrored',choices=['OFF','ON','BOTH'],default='BOTH',type=str.upper)
 p.add_argument('--tanf',choices=['OFF','ON','BOTH'],default='OFF',type=str.upper)
 p.add_argument('--linkProfiles',default='ALL');p.add_argument('--linkScale',type=float,default=.80)
 p.add_argument('--closurePolicy',choices=['LEGACY','CENTER','MANUAL','FIXED61'],default='FIXED61',type=str.upper)
 p.add_argument('--closureAngles',default='0,0,180',help='manual in-plane component rotations in degrees, component0,1,2')
 p.add_argument('--plan',action='store_true');p.add_argument('--prepare',action='store_true')
 p.add_argument('--execute',action='store_true');p.add_argument('--analyze',action='store_true')
 p.add_argument('--timeout',type=int,default=21600);p.add_argument('--noEarlyCheckpoints',action='store_true')
 p.add_argument('--selftest',action='store_true')
 p.add_argument('--unsafeRelaxation',action='store_true',help='allow explicitly flagged SHARP_TURN_WARNING cases to execute')
 return p.parse_args(argv)

def main(argv=None):
 args=parse(argv)
 if args.selftest:return selftest()
 root=args.root.resolve()
 if args.analyze:
  n=geometry_pair_csv(root);print('Symmetry geometry comparison pairs:',n)
  from analysis_v050 import run as analyze_native
  return analyze_native(root)
 ks=select_names(args.knots,KNOTS);ls=select_names(args.links,LINKS)
 if not ks and not ls:raise ValueError('Select --knots=ALL|name,... and/or --links=ALL|5_5_6,6_6_5')
 ps=select_names(args.linkProfiles,PROFILES)
 if ls and not ps:raise ValueError('Link profiles cannot be NONE for a link selection')
 closure_angles=tuple(float(v.strip()) for v in args.closureAngles.split(','))
 if len(closure_angles)!=3 or not all(map(math.isfinite,closure_angles)):
  raise ValueError('Expected exactly three finite closure angles')
 if args.beads:
  ns=sorted(set(map(int,args.beads.split(','))))
  if min(ns)<32 or max(ns)>8192:raise ValueError('Bad bead list')
 else:ns=bead_grid(args.minN,args.maxN)
 if not (0.1<=args.linkScale<=2.0):raise ValueError('linkScale must be in [0.1,2.0]')
 ticks=checkpoints(args.maxIteration,args.checkpointsEvery,not args.noEarlyCheckpoints)
 orientations={'OFF':['ORIG'],'ON':['MIRROR'],'BOTH':['ORIG','MIRROR']}[args.mirrored]
 arms={'OFF':['OFF'],'ON':['ON'],'BOTH':['OFF','ON']}[args.tanf]
 cases=expected_cases(ks,ls,ps,ns,orientations,arms)
 planned={'release':'A006 v0.5.0a fixed 6_1 180deg links+bounded closure+beadlimit','timestamp_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
          'selection':vars(args)|{'root':'.'},'count':len(cases),'checkpoint_count':len(ticks),
          'checkpoints':ticks,'runs':[c.__dict__ for c in cases],
          'status':'PLANNED_ONLY','topological_and_Euler_certification':'UNRESOLVED'}
 plan_file=root/REL/'PLAN.json';dump(plan_file,planned)
 print('PLAN:',len(cases),'arms,',len(ticks),'checkpoints each,',len(cases)*len(ticks),'records')
 print('Output:',plan_file)
 if args.plan:return 0
 if not args.prepare and not args.execute:
  # No flag means execution as user requested. Does NOT run without preflight.
  args.execute=True
 sys.path.insert(0,str(root/'src'))
 results=[]
 for idx,case in enumerate(cases,1):
  try:
   geom,report=build_geometry(root,case,args.linkScale,args.closurePolicy,closure_angles)
   script,dir,key=script_and_dir(root,case,geom,ticks,report['n_actual'])
   if args.execute and report['status']!='STATIC_CANDIDATE' and not args.unsafeRelaxation:
    raise RuntimeError(f"Unqualified sharp closure: {case.slug()} {report['status']}; use --prepare for inspection")
   if args.execute:
    state=run_one(root,case,dir,script,key,ticks,report['n_actual'],args.timeout)
   else:state='PREPARED_NOT_EXECUTED'
   results.append({'case':case.slug(),'status':state,'file':str(geom.relative_to(root)),
                   'script':str(script.relative_to(root))})
   print(idx,'/',len(cases),case.slug(),state,flush=True)
  except Exception as exc:
   results.append({'case':case.slug(),'status':'FAIL_CLOSED','error':str(exc)})
   dump(root/REL/'PROGRESS.json',{'results':results,'complete':False})
   print('FAIL_CLOSED',case.slug(),exc,file=sys.stderr)
   return 4
 dump(root/REL/'PROGRESS.json',{'results':results,'complete':True})
 geometry_pair_csv(root)
 print('COMPLETE:',len(results),'cases. Scientific topology and parity dynamics require independent qualification.')
 return 0

def selftest():
 assert checkpoints(8000,500)[:6]==[0,1,8,32,128,500]
 assert checkpoints(8000,500)[-1]==8000
 assert bead_grid(256,2048)==[256,512,1024,2048]
 assert select_names('11_1,11_2',KNOTS)==['11a367','11a247']
 assert select_names('ALL',LINKS)==list(LINKS)
 assert required_beadlimit([1024,1024,1024])==4000
 assert required_beadlimit([2048,2048,2048])==8000
 assert required_beadlimit([1000,1000,1000]) is None
 assert required_beadlimit([128,256,512]) is None
 assert required_beadlimit([8192,8192,8192])==32000
 p=np.column_stack((3*np.cos(np.arange(128)*2*np.pi/128),3*np.sin(np.arange(128)*2*np.pi/128),np.zeros(128)))
 q,phase=sample_closed(p,256);assert len(q)==256
 m=reflected([q])[0];assert np.array_equal(m[:,0],-q[:,0])
 assert np.allclose(np.linalg.norm(np.roll(m,-1,axis=0)-m,axis=1),np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1))
 import tempfile
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'three.xyz';write_xyz3(path,[q,q,m])
  assert [len(a) for a in components_from_xyz(path)]==[256]*3
  assert path.read_text().count('\n\n')==2
  # Strictly reject KnotPlot console component headers in geometry source.
  bad=Path(d)/'bad.xyz';bad.write_text('Component 0:\n'+path.read_text())
  try:components_from_xyz(bad)
  except ValueError:pass
  else:raise AssertionError('Accepted XYZ component header')
 print('PASS: v0.5.0 selection, grid, beadlimit, atomic ticks, mirror parity, strict 3-block XYZ')
 return 0

if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,FileNotFoundError,RuntimeError) as exc:
  print('ERROR:',exc,file=sys.stderr);raise SystemExit(2)
