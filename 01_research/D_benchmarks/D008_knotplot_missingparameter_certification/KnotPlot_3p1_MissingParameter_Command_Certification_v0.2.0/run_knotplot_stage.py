from __future__ import annotations
import argparse, subprocess, sys, json, shutil, hashlib, os, re
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
KNOTPLOT_ROOT=ROOT.parent
DEFAULT_SHORTCUT=KNOTPLOT_ROOT/'KnotPlot.lnk'
PARAMS=('charge','hooke','power','timeincr')
HARD_FAILURES=('nothing to save','nothing to output')

def resolve_shortcut(lnk:Path):
    if not lnk.is_file(): raise FileNotFoundError(f'KnotPlot shortcut not found: {lnk}')
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(lnk).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    p=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True,check=False)
    lines=[x.strip() for x in (p.stdout or '').splitlines() if x.strip()]
    if not lines: raise RuntimeError('Could not resolve KnotPlot.lnk')
    exe=Path(lines[0]); wd=Path(lines[1]) if len(lines)>1 and lines[1] else KNOTPLOT_ROOT
    if not exe.is_file(): raise FileNotFoundError(exe)
    return exe,wd

def sha256(p:Path):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def rel_outroot(stage:str,workdir:Path):
    out=(ROOT/'out'/stage).resolve()
    try: return os.path.relpath(out,workdir).replace('\\','/')
    except ValueError: return str(out).replace('\\','/')

def render(src:Path,stage:str,workdir:Path):
    (ROOT/'out'/stage).mkdir(parents=True,exist_ok=True)
    text=src.read_text(encoding='utf-8',errors='replace').replace('__OUTROOT__',rel_outroot(stage,workdir))
    rd=ROOT/'runtime_kpc'/stage; rd.mkdir(parents=True,exist_ok=True)
    dst=rd/src.name; dst.write_text(text,encoding='utf-8',newline='\n'); return dst

def expected(runtime:Path,workdir:Path):
    toks=re.findall(r'(?mi)^\s*(?:save|coords)\s+(\S+)',runtime.read_text(encoding='utf-8',errors='replace'))
    return [(workdir/Path(t)).resolve() for t in toks]

def archive(paths,stage,stem):
    existing=[p for p in paths if p.exists()]
    if not existing:return
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    dest=ROOT/'archive'/stamp/stage/stem; dest.mkdir(parents=True,exist_ok=True)
    for p in existing: shutil.move(str(p),str(dest/p.name))

def classify_log(text:str,swept:str):
    lines=text.splitlines(); reject=[]; hard=[]
    rejection_markers=(
        'unknown command',
        'unknown parameter',
        'invalid parameter',
        'illegal parameter',
        'not a parameter',
        'obsolete',
    )

    # Some KnotPlot batch launches print a harmless diagnostic preamble
    # containing "nothing to save"/"nothing to output" before the actual
    # `load 3.1` happens.  Only hard save/output errors AFTER a successful
    # "knot loaded" marker belong to the scientific run.
    loaded_line=None
    for i,line in enumerate(lines,1):
        if 'knot loaded' in line.lower():
            loaded_line=i
            break

    for i,line in enumerate(lines,1):
        lo=line.lower()

        if swept.lower() in lo and any(marker in lo for marker in rejection_markers):
            reject.append({'line':i,'text':line.strip()})

        if any(x in lo for x in HARD_FAILURES):
            if loaded_line is None or i >= loaded_line:
                hard.append({'line':i,'text':line.strip()})

    return reject,hard

def run_candidate(exe,wd,src,stage,swept):
    runtime=render(src,stage,wd); exp=expected(runtime,wd); archive(exp,stage,src.stem)
    log=ROOT/'logs'/stage/f'{src.stem}.log'; log.parent.mkdir(parents=True,exist_ok=True)
    if log.exists(): archive([log],stage,src.stem)
    started=datetime.now(timezone.utc)
    with runtime.open('rb') as fin,log.open('wb') as fout:
        cp=subprocess.run([str(exe),'-nog'],cwd=str(wd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT,check=False)
    ended=datetime.now(timezone.utc)
    text=log.read_text(encoding='utf-8',errors='replace'); rejects,hard=classify_log(text,swept)
    missing=[str(p) for p in exp if not p.is_file() or p.stat().st_size==0]
    # Need proof load actually happened.
    loaded='knot loaded' in text.lower()
    status='COMPLETED'
    if cp.returncode!=0 or missing or hard or not loaded: status='RUN_FAILED'
    elif rejects: status='COMMAND_REJECTED'
    audit={'candidate':src.stem,'stage':stage,'swept_parameter':swept,'process_exit':cp.returncode,'loaded_marker':loaded,
           'started_utc':started.isoformat(),'ended_utc':ended.isoformat(),'source_sha256':sha256(src),'runtime_sha256':sha256(runtime),
           'expected_outputs':len(exp),'missing_outputs':missing,'command_rejections':rejects,'hard_log_issues':hard,'status':status,'log':str(log)}
    ap=ROOT/'logs'/stage/f'{src.stem}.audit.json'; ap.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(f'  {src.stem:22s} {status}')
    if rejects:
        for r in rejects: print(f"    L{r['line']}: {r['text']}")
    if missing: print('    missing:',len(missing))
    return status

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--stage',choices=['cert','extended'],required=True); ap.add_argument('--params',nargs='*'); ap.add_argument('--shortcut',type=Path,default=DEFAULT_SHORTCUT); a=ap.parse_args(argv)
    try: exe,wd=resolve_shortcut(a.shortcut.resolve())
    except Exception as e: print('ERROR:',e,file=sys.stderr); return 1
    params=tuple(a.params or PARAMS)
    print('='*68); print(f'KnotPlot Missing-Parameter {a.stage.upper()} stage'); print('='*68)
    print('Executable:',exe); print('CWD       :',wd); print('Bundle    :',ROOT); print('Parameters:',', '.join(params)); print('='*68)
    worst=0
    for p in params:
        files=sorted((ROOT/'kpc'/a.stage).glob(f'{p}_*.kpc'))
        print(f'\n[{p}] {len(files)} candidates')
        for src in files:
            s=run_candidate(exe,wd,src,a.stage,p)
            if s=='RUN_FAILED': worst=max(worst,2)
    if worst:
        print('\nWARNING: one or more candidates had RUN_FAILED; continuing so the analyzer can classify them.')
    return 0
if __name__=='__main__': raise SystemExit(main())
