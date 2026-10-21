#!/usr/bin/env python3
"""KnotPlot atomic runs: versioned tiers, cross-tier DONE reuse, strict evidence.
Never restart a higher-tier run from XYZ: it lacks KnotPlot internal solver state.
"""
from pathlib import Path
import argparse, hashlib,json,os,subprocess,sys,datetime,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from build_v040 import ALL, RES, sha, write_json
MODE_KNOTS={
 'BASIC':['5_2','6_1'],
 'SMALL':['3_1','4_1','5_2','6_1'],
 'MEDIUM':['3_1','4_1','5_1','5_2','6_1','7_1','7_2','8_1'],
 'FULL':ALL,
}
HORIZON={'BASIC':8000,'SMALL':8000,'MEDIUM':16000,'FULL':32000}
EARLY=[0,1,8,32,128,512]
PARAMETERS={
 'mode':'cbf','collision':'fast','energy_model':'MD','bradius':0.20,'cradius':0.06,
 'stusplit':0,'dstep':1,'close':0.20,'max-dr':0.02,'mechforce':'on',
 'elecforce':'on','amechforce':'off','aelecforce':'off','thermalforce':'off',
 'bendforce':'off','extforce':'off','velforce':'off','gravity':'off','drag':'off',
 'spring_length':1.4,'hooke':1,'power':5,'charge':15,'tinc':15,'tanmag':9,
 'visualization_note':'no fitto; radius display only',
}
def ticks(end):return EARLY+list(range(1000,end+1,1000))
def digest(knot,n,arm):
 seed=ROOT/'output'/'seeds'/f'{knot}_N{n}.kpt'
 conf={'seed_sha256':sha(seed),'parameters':PARAMETERS,'tanforce':arm,'atomic':'ago','contract':'v0.4.0'}
 return hashlib.sha256(json.dumps(conf,sort_keys=True).encode()).hexdigest()
def run_dir(knot,n,mode,arm):return ROOT/'runs'/knot/f'N{n:04d}'/mode/f'TANF_{arm}'
def snapshot_name(it):return f'i{it:05d}'
def kpc_header(arm):
 return '\n'.join(['reset all','show labels backdrop','mode cbf',
 'bradius = 0.20','cradius = 0.06','stusplit = 0','dstep = 1',
 'collision fast','energy model MD','close = 0.20','max-dr = 0.02',
 'mechforce = on','elecforce = on','amechforce = off','aelecforce = off',
 'thermalforce = off','bendforce = off','extforce = off','velforce = off',
 'gravity = off','drag = off','spring-length = 1.4','hooke = 1',
 'power = 5','charge = 15','tinc = 15','tanmag = 9',
 f'tanforce = {arm.lower()}'])
def make_script(knot,n,mode,arm):
 name=f'{knot}_N{n:04d}_TANF_{arm}_{mode}'
 directory=run_dir(knot,n,mode,arm);directory.mkdir(parents=True,exist_ok=True)
 lines=[f'% AUTO v0.4.0 {name}: no asynchronous go, starts from baseline seed',
         kpc_header(arm),f'load output/seeds/{knot}_N{n}.kpt',
         'information','parameters close','parameters max-dr',
         'length',f'echo BEGIN_{name}']
 last=0
 for t in ticks(HORIZON[mode]):
  if t:lines.append(f'ago {t-last}')
  rel=(directory.relative_to(ROOT)/snapshot_name(t)).as_posix()
  lines.extend([f'echo CHECKPOINT_{name}_{t:05d}','length',
    f'coords {rel}.xyz',f'save {rel}.k float'])
  if t in (0,1,512,8000,16000,32000):lines.extend(['safe','dowker'])
  last=t
 lines.extend([f'echo COMPLETE_{name}','stop'])
 out=ROOT/'scripts'/mode/f'{name}.kpc';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text('\n'.join(lines)+'\n',encoding='ascii')
 return out

def validate_snapshot(f,n):
 f=Path(f)
 if not f.is_file() or f.stat().st_size==0:return None
 try:
  # KnotPlot coords includes Component 0: headers; NumPy loadtxt alone rejects it.
  rows=[]
  for ln in f.read_text(encoding='utf-8-sig').splitlines():
   z=ln.strip()
   if not z or z.lower().startswith('component'):continue
   fields=z.split()
   if len(fields)!=3:return None
   rows.append([float(a) for a in fields])
  x=np.asarray(rows,dtype=np.float64)
  if x.shape!=(n,3) or not np.isfinite(x).all():return None
  return x
 except Exception:return None

def completed(knot,n,arm,target):
 # Strict check: identical source and params, completion JSON created after verified runtime.
 expected=digest(knot,n,arm)
 for tier in ['FULL','MEDIUM','SMALL','BASIC']:
  d=run_dir(knot,n,tier,arm);info=d/'DONE.json'
  if not info.is_file():continue
  try:
   meta=json.loads(info.read_text())
   if meta['protocol_sha256']!=expected or int(meta['max_iteration'])<target:continue
   if meta.get('status')!='RUNTIME_CHECKPOINTS_COMPLETE':continue
   baseline=validate_snapshot(d/'i00000.xyz',n)
   last=validate_snapshot(d/f'i{int(meta["max_iteration"]):05d}.xyz',n)
   if baseline is None or last is None or np.array_equal(baseline,last):continue
   # verify all required checkpoint files exist, including the requested shorter horizon
   if any(validate_snapshot(d/f'i{t:05d}.xyz',n) is None for t in ticks(target)):continue
   return {'tier':tier,'dir':str(d),'max_iteration':meta['max_iteration']}
  except Exception:continue
 return None

def preflight_exe():
 choices=[]
 env=os.getenv('KNOTPLOT_EXE','').strip()
 if env:choices.append(Path(env))
 cfg=ROOT/'config'/'knotplot_exe.txt'
 if cfg.exists():
  s=cfg.read_text().strip().strip('"');
  if s:choices.append(Path(s))
 lad=os.getenv('LOCALAPPDATA')
 if lad:choices.append(Path(lad)/'Programs'/'KnotPlot'/'KnotPlot.exe')
 for p in choices:
  if p.is_file():return p
 raise FileNotFoundError('KnotPlot.exe niet gevonden. Zet KNOTPLOT_EXE of maak config/knotplot_exe.txt met volledig pad.')

def runtime_run(script,knot,n,arm,mode,exe,timeout):
 directory=run_dir(knot,n,mode,arm)
 # Fail closed on interrupted or stale previous runs: clear this arm's old raw checkpoints before restarting.
 for existing in directory.glob('i*.xyz'):
  existing.unlink()
 for existing in directory.glob('i*.k'):
  existing.unlink()
 (directory/'DONE.json').unlink(missing_ok=True)
 # -stdin and -nographics documented by KnotPlot. Windows executable must be validated locally.
 cmd=[str(exe),'-stdin','-nographics'];stdin=f'read {script.relative_to(ROOT).as_posix()}\n'
 transcript=directory/'knotplot_stdout.log'
 with transcript.open('wb') as log:
  completed_proc=subprocess.run(cmd,input=stdin.encode('ascii'),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,check=False)
 if completed_proc.returncode!=0:raise RuntimeError(f'KnotPlot exit={completed_proc.returncode}; read {transcript}')
 missing=[];all_data=[]
 for it in ticks(HORIZON[mode]):
  f=directory/f'{snapshot_name(it)}.xyz';p=validate_snapshot(f,n)
  if p is None:missing.append(str(f));continue
  k=directory/f'{snapshot_name(it)}.k'
  if not k.is_file() or not k.stat().st_size:missing.append(str(k))
  all_data.append((it,p))
 if missing:raise RuntimeError(f'Missing/invalid outputs ({len(missing)}): '+', '.join(missing[:3]))
 if np.array_equal(all_data[0][1],all_data[-1][1]):raise RuntimeError('Zero recorded displacement; abort DONE, see transcript')
 meta={'status':'RUNTIME_CHECKPOINTS_COMPLETE','run_mode':mode,'knot':knot,'n':n,'tanforce':arm,
  'max_iteration':HORIZON[mode],'protocol_sha256':digest(knot,n,arm),
  'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'runtime_input':'KnotPlot -stdin -nographics',
  'topology_certification':'UNRESOLVED','Euler_dynamics':'NOT_TESTED',
  'postrun_evidence':'all checkpoint .xyz/.k structurally present; scientific/topological checks separate'}
 write_json(directory/'DONE.json',meta)
 return meta

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=list(MODE_KNOTS));ap.add_argument('--plan',action='store_true');ap.add_argument('--execute',action='store_true');ap.add_argument('--only',nargs='*');ap.add_argument('--timeout',type=int,default=21600)
 args=ap.parse_args();ks=args.only or MODE_KNOTS[args.mode]
 if any(k not in MODE_KNOTS[args.mode] for k in ks):raise SystemExit('knot outside mode tier')
 requests=[]
 for knot in ks:
  for n in RES:
   for arm in ('ON','OFF'):
    script=make_script(knot,n,args.mode,arm)
    prev=completed(knot,n,arm,HORIZON[args.mode])
    requests.append({'knot':knot,'n':n,'arm':arm,'script':str(script.relative_to(ROOT)),
      'status':'SKIP_VERIFIED' if prev else 'PENDING','previous_run':prev})
 write_json(ROOT/'plans'/f'{args.mode}.json',{'mode':args.mode,'target_iteration':HORIZON[args.mode],
    'checkpoints':ticks(HORIZON[args.mode]),'tasks':requests})
 counts={'pending':sum(r['status']=='PENDING' for r in requests),'skipped':sum(r['status']=='SKIP_VERIFIED' for r in requests)}
 print(f'PLAN {args.mode}: {counts}; max iteration={HORIZON[args.mode]}; checkpoints={len(ticks(HORIZON[args.mode]))}')
 if args.plan or not args.execute:return 0
 try:exe=preflight_exe()
 except Exception as e:
  print('EXECUTION_BLOCKED:',e,'; scripts and plan generated for manual KnotPlot execution',file=sys.stderr)
  return 3
 # Qualify the Windows -stdin atomic workflow before any expensive campaign arm.
 pre=ROOT/'preflight'/'PREFLIGHT_PASS.json'
 qualified=False
 if pre.is_file():
  try:
   meta=json.loads(pre.read_text())
   qualified=(meta.get('status')=='LOCAL_ATOMIC_ONE_STEP_PASS' and Path(meta.get('exe',''))==exe
              and meta.get('exe_size')==exe.stat().st_size and meta.get('exe_mtime_ns')==exe.stat().st_mtime_ns)
  except Exception:pass
 if not qualified:
  print('Executing KnotPlot 1-step headless preflight...',flush=True)
  cp=subprocess.run([sys.executable,str(ROOT/'tools'/'preflight_windows.py')],cwd=ROOT,check=False)
  if cp.returncode!=0:
   print('EXECUTION_BLOCKED: one-step KnotPlot preflight failed',file=sys.stderr)
   return 5
 for idx,record in enumerate(requests,1):
  if record['status']=='SKIP_VERIFIED':print('SKIP',record['knot'],record['n'],record['arm'],flush=True);continue
  print('EXECUTE',idx,'/',len(requests),record['knot'],record['n'],record['arm'],flush=True)
  try:runtime_run(ROOT/record['script'],record['knot'],record['n'],record['arm'],args.mode,exe,args.timeout)
  except Exception as e:
   print('FAIL-CLOSED',record['knot'],record['n'],record['arm'],e,file=sys.stderr)
   return 4
 return 0
if __name__=='__main__':raise SystemExit(main())
